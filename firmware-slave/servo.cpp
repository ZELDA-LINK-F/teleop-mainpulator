// firmware-slave/servo.cpp
// LX-16A 舵机控制 - 自己实现协议 (不依赖第三方库)
//
// 协议参考: "lx-16a LewanSoul Bus Servo Communication Protocol.pdf"
// 命令 0x01 = MOVE (转动到指定角度, 指定时间)
// 帧格式: [0x55][0x55][len][cmd][params...][checksum]
//   - 校验和 = (len + cmd + params 全部字节求和) 取低 8 位 (不取反)
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
//   - 不需要 DIR 引脚 (之前 stub 里有, 已删除)
//   - 不依赖 LewanSoul 库 (GitHub 仓库 404 了)

#include "servo.h"

// ====== 调试开关 ======
// 改成 1 看每帧舵机指令 (刷屏警告: 100Hz 时串口会炸)
// 阶段 1 验证建议先保持 0, 看舵机动就行
#define SERVO_DEBUG 0

// 串口 2 给舵机用 (UART2 = GPIO17 TX, GPIO18 RX)
// 注意: ESP32-S3 的 UART2 引脚可以映射, 我们硬编码 17/18
HardwareSerial ServoSerial(2);

// 暂存当前各舵机归一化值, 用于状态打印和调试
static float currentAngles[NUM_SERVOS] = {0};

// ====== 内部: 把 0.0~1.0 映射到 LX-16A 角度单位 (0~1000 = 0~240°) ======
static uint16_t normalizedToLxAngle(float n) {
  // 钳制到 [0,1] - 防止异常输入导致舵机跑到范围外
  if (n < 0.0f) n = 0.0f;
  if (n > 1.0f) n = 1.0f;
  // LX-16A 单位 0-1000 对应 0-240° (不是 0-180°)
  return (uint16_t)(SERVO_ANGLE_MIN + n * (SERVO_ANGLE_MAX - SERVO_ANGLE_MIN));
}

// ====== 内部: 发送一条 LX-16A MOVE 命令 ======
//
// frame 结构 (10 字节):
//   [0]: 0x55          - 帧头
//   [1]: 0x55          - 帧头
//   [2]: 0x09          - 长度 (从 cmd 到 checksum 的字节数 = 9)
//   [3]: 0x01          - 命令: MOVE
//   [4]: id            - 舵机 ID (1-253)
//   [5]: angle_lo      - 目标角度低字节
//   [6]: angle_hi      - 目标角度高字节
//   [7]: time_lo       - 转动时间低字节 (毫秒)
//   [8]: time_hi       - 转动时间高字节
//   [9]: checksum      - (frame[2..8] 求和) & 0xFF
//
static void lx16aSendMove(uint8_t id, uint16_t angle, uint16_t timeMs) {
  uint8_t frame[10];
  frame[0] = 0x55;
  frame[1] = 0x55;
  frame[2] = 0x09;          // 长度
  frame[3] = 0x01;          // cmd = MOVE
  frame[4] = id;
  frame[5] = angle & 0xFF;          // 角度低字节
  frame[6] = (angle >> 8) & 0xFF;   // 角度高字节
  frame[7] = timeMs & 0xFF;         // 时间低字节 (毫秒)
  frame[8] = (timeMs >> 8) & 0xFF;  // 时间高字节

  // 校验和 = len + cmd + 所有 params 求和, 取低 8 位
  uint8_t sum = 0;
  for (int i = 2; i <= 8; i++) {
    sum += frame[i];
  }
  frame[9] = sum;  // 取低 8 位 (uint8_t 自动截断)

  // 一次性发送整个帧
  ServoSerial.write(frame, sizeof(frame));
}

bool servoSetup() {
  // 启动串口 2 (TX=GPIO17, RX=GPIO18)
  // 参数: baud, 8N1, RX pin, TX pin
  // 1kΩ 方案下, TX 通过电阻出去, RX 直接接信号线
  ServoSerial.begin(SERVO_BAUD, SERIAL_8N1, SERVO_RX_PIN, SERVO_TX_PIN);
  delay(50);  // 等串口稳定

  Serial.print("[SERVO] LX-16A init OK (TX=GPIO");
  Serial.print(SERVO_TX_PIN);
  Serial.print(", RX=GPIO");
  Serial.print(SERVO_RX_PIN);
  Serial.print(", baud=");
  Serial.print(SERVO_BAUD);
  Serial.println(")");
  return true;
}

void servoSetNormalized(int servoId, float normalized) {
  // 1. 更新本地缓存 (无论舵机在不在, 状态都对)
  int idx = servoId - 1;  // 假设 ID 1-6 对应数组 0-5
  if (idx >= 0 && idx < NUM_SERVOS) {
    currentAngles[idx] = normalized;
  }

  // 2. 转换: 归一化 [0,1] → LX-16A 角度 [0,1000]
  uint16_t angle = normalizedToLxAngle(normalized);

  // 3. 时间设为 0 = 舵机以最快速度转到目标角度
  //    (改成 200 表示 200ms 内转到, 平滑一点但延迟大)
  uint16_t timeMs = 0;

  // 4. 发送 MOVE 命令
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
  // 6 个舵机依次发命令 (单总线半双工, 不能并发)
  // 每个 move 命令大约 1ms 内发完, 6 个 = 6ms, 加上舵机执行时间
  // 总周期 ~20ms, 比 100Hz 慢, 但阶段 1 单舵机验证足够
  for (int i = 0; i < NUM_SERVOS; i++) {
    servoSetNormalized(SERVO_IDS[i], normalized[i]);
  }
}

// ====== P1: 回安全姿势 ======
// 通信断了的时候让舵机回安全姿势, 避免失控 (比如卡在握紧状态)
// 实现上就是复用 servoSetAll, 传 SERVO_SAFE_NORM (在 config.h 里定义)
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
