// firmware-master/protocol.cpp
// 32 字节协议实现

#include "protocol.h"

void frameInit(SensorFrame& f) {
  memset(&f, 0, sizeof(f));
}

void frameSetFlex(SensorFrame& f, const float flex[5]) {
  // 把 0.0-1.0 的归一化值映射成 uint16_t (0-65535)
  for (int i = 0; i < 5; i++) {
    float v = flex[i];
    if (v < 0.0f) v = 0.0f;
    if (v > 1.0f) v = 1.0f;
    f.flex[i] = (uint16_t)(v * 65535.0f);
  }
}

void frameSetQuat(SensorFrame& f, const float quat[4]) {
  for (int i = 0; i < 4; i++) {
    f.quat[i] = quat[i];
  }
}

void framePrint(const SensorFrame& f) {
  Serial.print("[FRAME seq=");
  Serial.print(f.seq);
  Serial.print("] flex=[");
  for (int i = 0; i < 5; i++) {
    Serial.print(f.flex[i]);
    Serial.print(i < 4 ? "," : "");
  }
  Serial.print("] quat=[");
  for (int i = 0; i < 4; i++) {
    Serial.print(f.quat[i], 3);
    Serial.print(i < 3 ? "," : "");
  }
  Serial.println("]");
}