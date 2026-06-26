// firmware-master/flex_sensor.cpp
// 弯曲传感器读取模块实现

#include "flex_sensor.h"

void flexSensorSetup() {
  // ESP32-S3 ADC 默认 12-bit (0-4095)
  analogReadResolution(12);
  // ADC 参考电压默认 3.3V, 不需要设置 atten (默认 11dB ~= 0-3.3V)
  for (int i = 0; i < NUM_FLEX; i++) {
    pinMode(FLEX_PINS[i], INPUT);
  }
  Serial.print("[FLEX] Init OK, pins=");
  for (int i = 0; i < NUM_FLEX; i++) {
    Serial.print(FLEX_PINS[i]);
    Serial.print(i < NUM_FLEX - 1 ? "," : "\n");
  }
}

bool flexSensorReadRaw(uint16_t raw[NUM_FLEX]) {
  for (int i = 0; i < NUM_FLEX; i++) {
    raw[i] = analogRead(FLEX_PINS[i]);
  }
  return true;
}

bool flexSensorReadNormalized(float normalized[NUM_FLEX]) {
  uint16_t raw[NUM_FLEX];
  if (!flexSensorReadRaw(raw)) return false;

  for (int i = 0; i < NUM_FLEX; i++) {
    int flat = FLEX_RAW_FLAT[i];
    int bent = FLEX_RAW_BENT[i];
    int range = bent - flat;
    if (range == 0) {
      normalized[i] = 0.0f;
      continue;
    }
    float v = (float)(raw[i] - flat) / (float)range;
    // 限制到 [0, 1]
    if (v < 0.0f) v = 0.0f;
    if (v > 1.0f) v = 1.0f;
    normalized[i] = v;
  }
  return true;
}