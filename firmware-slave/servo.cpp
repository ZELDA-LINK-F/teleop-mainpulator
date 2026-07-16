// firmware-slave/servo.cpp
// LX-16A 舵机控制 - 自己实现协议 (不依赖第三方库)
//
// 协议参考: "02+总线舵机通信协议.pdf"
// 帧格式: [0x55][0x55][ID][Length][Cmd][Params...][Checksum]
//   - 校验和 = ~(ID + Length + Cmd + Prm1 + ... + PrmN) 取低 8 位 (取反)
//
// 接线 (1kΩ 电阻方案, 见 README.md):
//   ESP32-S3 GPIO17 (U1TXD) ── 1kΩ ──┬──→ LX-16A 信号线(橙)
//   ESP32-S3 GPIO18 (U1RXD) ─────────┘
//   ESP32-S3 GND ───────────────────→ LX-16A GND(黑)
//   7.4V+ ──────────────────────────→ LX-16A V+(红)
//
// 关键点:
//   - 1kΩ 电阻让 ESP32 TX 在不发送时是"弱驱动", 不会干扰舵机回包
//   - 单线半双工, ESP32 UART 全双工硬件自动处理收发时序
//   - 不需要 DIR 引脚
//   - LX-16A 出厂默认电机卸载 (无力矩), 必须先发 LOAD 命令上电才能动

#include "servo.h"

// ====== 调试开关 ======
// 0 = 不打印每帧指令 (生产模式)
// 1 = 打印每帧指令 (调试用, 100Hz 下串口会爆, 仅低频测试时开)
#define SERVO_DEBUG 0

// 串口 2 给舵机用 (UART2 = GPIO17 TX, GPIO18 RX)
HardwareSerial ServoSerial(2);

// 暂存当前各舵机归一化值, 用于状态打印和调试
static float currentAngles[NUM_SERVOS] = {0};

// ====== 内部: 把 0.0~1.0 映射到 LX-16A 角度单位 (0~1000 = 0~240°) ======
static uint16_t normalizedToLxAngle(float n) {
  if (n < 0.0f) n = 0.0f;
  if (n > 1.0f) n = 1.0f;
  return (uint16_t)(SERVO_ANGLE_MIN + n * (SERVO_ANGLE_MAX - SERVO_ANGLE_MIN));
}

// ====== 内部: 发送原始 LX-16A 帧 (通用) ======
// 协议帧: [0x55][0x55][ID][Length][Cmd][Prm1...PrmN][Checksum]
// Length = 从 Length 自身到 Checksum 的字节数 (含 Length 和 Checksum)
// Checksum = ~(ID + Length + Cmd + Prm1 + ... + PrmN) & 0xFF
static void lx16aSendFrame(uint8_t id, uint8_t cmd, const uint8_t* params, uint8_t paramCount) {
  // 帧总长 = 2(帧头) + 1(ID) + 1(Length) + 1(Cmd) + N(Params) + 1(Checksum)
  // Length = 1(Cmd) + N(Params) + 1(Checksum) + 1(Length自身) = 3 + N
  uint8_t length = 3 + paramCount;
  uint8_t frame[6 + paramCount];  // 2 + 1 + 1 + 1 + N + 1
  uint8_t idx = 0;

  frame[idx++] = 0x55;   // 帧头
  frame[idx++] = 0x55;   // 帧头
  frame[idx++] = id;      // 舵机 ID
  frame[idx++] = length;  // 数据长度
  frame[idx++] = cmd;     // 指令

  for (uint8_t i = 0; i < paramCount; i++) {
    frame[idx++] = params[i];
  }

  // 校验和 = ~(ID + Length + Cmd + Prm1 + ... + PrmN)
  uint8_t sum = 0;
  for (uint8_t i = 2; i < idx; i++) {
    sum += frame[i];
  }
  frame[idx] = ~sum;

  ServoSerial.write(frame, idx + 1);
}

// ====== 内部: 发送 MOVE 命令 (cmd=1) ======
// 参数: angle 0~1000, time 0~30000ms
static void lx16aSendMove(uint8_t id, uint16_t angle, uint16_t timeMs) {
  uint8_t params[4];
  params[0] = angle & 0xFF;         // 角度低字节
  params[1] = (angle >> 8) & 0xFF;  // 角度高字节
  params[2] = timeMs & 0xFF;        // 时间低字节
  params[3] = (timeMs >> 8) & 0xFF; // 时间高字节
  lx16aSendFrame(id, 0x01, params, 4);
}

// ====== 内部: 发送电机上电命令 (cmd=31, LOAD_OR_UNLOAD_WRITE) ======
// 参数: 0=卸载掉电 (无力矩), 1=装载电机 (有力矩)
// LX-16A 出厂默认是 0 (卸载), 必须先发这个才能控制舵机转动
static void lx16aSendLoad(uint8_t id, uint8_t load) {
  uint8_t p = load;
  lx16aSendFrame(id, 0x1F, &p, 1);
}

bool servoSetup() {
  ServoSerial.begin(SERVO_BAUD, SERIAL_8N1, SERVO_RX_PIN, SERVO_TX_PIN);
  delay(50);

  Serial.print("[SERVO] LX-16A init OK (TX=GPIO");
  Serial.print(SERVO_TX_PIN);
  Serial.print(", RX=GPIO");
  Serial.print(SERVO_RX_PIN);
  Serial.print(", baud=");
  Serial.print(SERVO_BAUD);
  Serial.println(")");

  // 给所有舵机上电 (LOAD=1), 否则舵机收到 MOVE 也不会动
  servoPowerOn();

  return true;
}

void servoPowerOn() {
  Serial.println("[SERVO] Powering on all servos (LOAD=1)...");
  for (int i = 0; i < NUM_SERVOS; i++) {
    lx16aSendLoad(SERVO_IDS[i], 1);
    delay(10);  // 每个舵机间隔一点时间, 避免总线冲突
  }
  Serial.println("[SERVO] All servos powered on.");
}

void servoSetNormalized(int servoId, float normalized, uint16_t timeMs) {
  int idx = servoId - 1;
  if (idx >= 0 && idx < NUM_SERVOS) {
    currentAngles[idx] = normalized;
  }

  uint16_t angle = normalizedToLxAngle(normalized);
  lx16aSendMove((uint8_t)servoId, angle, timeMs);

#if SERVO_DEBUG
  Serial.print("[SERVO] ID=");
  Serial.print(servoId);
  Serial.print(" norm=");
  Serial.print(normalized, 2);
  Serial.print(" angle=");
  Serial.println(angle);
#endif
}

void servoSetAll(const float normalized[NUM_SERVOS]) {
  for (int i = 0; i < NUM_SERVOS; i++) {
    servoSetNormalized(SERVO_IDS[i], normalized[i]);
  }
}

void servoSetSafe() {
  servoSetAll(SERVO_SAFE_NORM);
}

void servoPrintStatus() {
  Serial.print("[SERVO STATUS] ");
  for (int i = 0; i < NUM_SERVOS; i++) {
    Serial.print(SERVO_IDS[i]);
    Serial.print(":");
    Serial.print(currentAngles[i], 2);
    Serial.print(" ");
  }
  Serial.println();
}
