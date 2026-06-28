// firmware-master/wireless.cpp
// ESP-NOW 发送实现

#include "wireless.h"
#include <esp_now.h>
#include <WiFi.h>

// 临时用 broadcast, 调试阶段够用
// TODO: 改成 peer-to-peer (需要 slave 板子的 MAC)
static uint8_t broadcastMac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

static volatile bool sendOk = false;
// ESP32 Arduino 库 3.x 把回调签名从 const uint8_t* 改成了 const wifi_tx_info_t*
// 我们没用到 MAC 地址, 所以参数名改成 tx_info 占位就行
static void onSend(const wifi_tx_info_t* tx_info, esp_now_send_status_t status) {
  sendOk = (status == ESP_NOW_SEND_SUCCESS);
}

bool wirelessSetup() {
  WiFi.mode(WIFI_STA);
  // 打印自己的 MAC, 后面配置 peer 时要用
  Serial.print("[WIRELESS] My MAC = ");
  Serial.println(WiFi.macAddress());

  if (esp_now_init() != ESP_OK) {
    Serial.println("[WIRELESS] esp_now_init failed");
    return false;
  }
  esp_now_register_send_cb(onSend);

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, broadcastMac, 6);
  peer.channel = 0;
  peer.encrypt = false;
  if (esp_now_add_peer(&peer) != ESP_OK) {
    Serial.println("[WIRELESS] add_peer failed");
    return false;
  }
  Serial.println("[WIRELESS] ESP-NOW init OK (broadcast mode)");
  return true;
}

bool wirelessSendFrame(const SensorFrame& f) {
  esp_err_t r = esp_now_send(broadcastMac, (uint8_t*)&f, sizeof(f));
  return (r == ESP_OK);
}