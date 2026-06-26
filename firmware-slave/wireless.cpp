// firmware-slave/wireless.cpp
// ESP-NOW 接收实现

#include "wireless.h"
#include <esp_now.h>
#include <WiFi.h>

static volatile bool hasNew = false;
static SensorFrame latest;
static volatile unsigned long lastRxMs = 0;

static void onReceive(const uint8_t* mac, const uint8_t* data, int len) {
  if (len == sizeof(SensorFrame)) {
    memcpy(&latest, data, sizeof(SensorFrame));
    hasNew = true;
    lastRxMs = millis();
  }
}

bool wirelessSetup() {
  WiFi.mode(WIFI_STA);
  Serial.print("[WIRELESS] My MAC = ");
  Serial.println(WiFi.macAddress());

  if (esp_now_init() != ESP_OK) {
    Serial.println("[WIRELESS] esp_now_init failed");
    return false;
  }
  esp_now_register_recv_cb(onReceive);
  Serial.println("[WIRELESS] ESP-NOW listening...");
  return true;
}

bool wirelessGetLatest(SensorFrame& out) {
  if (!hasNew) return false;
  out = latest;
  hasNew = false;
  return true;
}

unsigned long wirelessGetLastReceiveTime() {
  return lastRxMs;
}