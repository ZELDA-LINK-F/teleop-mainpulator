// firmware-slave/protocol.cpp
// 跟 master 端协议实现完全相同

#include "protocol.h"

void frameInit(SensorFrame& f) {
  memset(&f, 0, sizeof(f));
}

void frameSetFlex(SensorFrame& f, const float flex[5]) {
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