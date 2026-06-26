// firmware-slave/servo.cpp
// LX-16A 舵机控制实现
// 需要安装库: LewanSoul/Hiwonder 舵机驱动 (库管理器搜 "LX16A")

#include "servo.h"
#include <LX16A.h>

// 串口 2 给舵机用
HardwareSerial ServoSerial(2);

// 暂存当前各舵机归一化值, 用于状态打印
static float currentAngles[NUM_SERVOS] = {0};

bool servoSetup() {
  ServoSerial.begin(SERVO_BAUD, SERIAL_8N1, -1, SERVO_TX_PIN);  // TX only
  pinMode(SERVO_DIR_PIN, OUTPUT);
  digitalWrite(SERVO_DIR_PIN, LOW);
  Serial.println("[SERVO] LX-16A init OK");
  return true;
}

static float normalizedToAngle(float n) {
  if (n < 0.0f) n = 0.0f;
  if (n > 1.0f) n = 1.0f;
  return SERVO_ANGLE_MIN + n * (SERVO_ANGLE_MAX - SERVO_ANGLE_MIN);
}

void servoSetNormalized(int servoId, float normalized) {
  // TODO: 用真实 LX-16A 库替换下面的 stub
  //   真实调用类似: LX16A servo(&ServoSerial);
  //   servo.move(servoId, normalizedToAngle(normalized));
  float angle = normalizedToAngle(normalized);
  int idx = servoId - 1;  // 假设 ID 1-6 对应数组 0-5
  if (idx >= 0 && idx < NUM_SERVOS) {
    currentAngles[idx] = normalized;
  }
  Serial.print("[SERVO] ID=");
  Serial.print(servoId);
  Serial.print(" norm=");
  Serial.print(normalized, 2);
  Serial.print(" angle=");
  Serial.println(angle, 0);
}

void servoSetAll(const float normalized[NUM_SERVOS]) {
  for (int i = 0; i < NUM_SERVOS; i++) {
    servoSetNormalized(SERVO_IDS[i], normalized[i]);
  }
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