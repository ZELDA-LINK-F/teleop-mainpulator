// firmware-slave/wireless.cpp
// ESP-NOW 接收实现

#include "wireless.h"
#include <esp_now.h>
#include <WiFi.h>

static volatile bool hasNew = false;
static SensorFrame latest;
static volatile unsigned long lastRxMs = 0;

// ESP32 Arduino 库 3.x 升级后, esp_now 注册的接收回调签名从
//   void cb(const uint8_t* mac, const uint8_t* data, int len)
// 改成了
//   void cb(const esp_now_recv_info_t* info, const uint8_t* data, int len)
// 跟 master 端 onSend 是同一个 ESP-IDF v5 升级带来的变化 (2026-06-28 踩过坑)
// 我们不用 MAC, 所以参数名改成 info 占位就行, 函数体不变
// 真要拿发送方 MAC 用 info->src_addr (uint8_t[6])
static void onReceive(const esp_now_recv_info_t* info, const uint8_t* data, int len) {
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