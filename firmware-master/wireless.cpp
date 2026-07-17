// firmware-master/wireless.cpp
// ESP-NOW 发送实现

#include "wireless.h"
#include "config.h"
#include <esp_now.h>
#include <WiFi.h>

// SLAVE_MAC 定义在 config.h, 默认是 broadcast (FF:FF...) = 阶段 1 兼容
// 改成 slave 真实 MAC 后自动升级为 peer-to-peer
// 发送统计 (P1 改进)
// volatile 是必须的: onSend 回调跟 loop 在同一核但异步触发, 主循环读这个值要 volatile
// 单核 ESP32 上 uint32_t 读写是原子的, 不会被撕成两半
// 注意: 回调是异步的, stats 反映"已确认的部分", 不是"全部发出去的"
// 也就是说: 发了 100 帧时回调可能只跑了 80 次, 统计会滞后约 20 帧
static volatile uint32_t sendOkCount = 0;
static volatile uint32_t sendFailCount = 0;

// ESP32 Arduino 库 3.x 把回调签名从 const uint8_t* 改成了 const wifi_tx_info_t*
// 我们没用到 MAC 地址, 所以参数名改成 tx_info 占位就行
static void onSend(const wifi_tx_info_t* tx_info, esp_now_send_status_t status) {
  // volatile + ++ 在新 C++ 标准里 deprecated, 显式写成"读出来 + 1 再写回去"
  // 单核 ESP32 上这个"读-改-写"序列不会被中断, 安全
  if (status == ESP_NOW_SEND_SUCCESS) {
    sendOkCount = sendOkCount + 1;
  } else {
    sendFailCount = sendFailCount + 1;
  }
}

bool wirelessSetup() {
  WiFi.mode(WIFI_STA);
  // 给 STA 模式一点时间生效, 否则 WiFi.macAddress() 在 ESP32-S3 + Arduino 3.x
  // 上会返回 00:00:00:00:00:00 (今天验证时两板都重现, 已确认是库时序问题)
  // 不影响 broadcast 发送, 但阶段 2 改 peer-to-peer 时必须能读出真实 MAC
  delay(100);
  // 打印自己的 MAC, 后面配置 peer 时要用
  Serial.print("[WIRELESS] My MAC = ");
  Serial.println(WiFi.macAddress());

  if (esp_now_init() != ESP_OK) {
    Serial.println("[WIRELESS] esp_now_init failed");
    return false;
  }
  esp_now_register_send_cb(onSend);

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, SLAVE_MAC, 6);
  peer.channel = 0;
  peer.encrypt = false;
  if (esp_now_add_peer(&peer) != ESP_OK) {
    Serial.println("[WIRELESS] add_peer failed (SLAVE_MAC may be wrong or not updated from broadcast)");
    return false;
  }
  // 打印当前模式
  bool isBroadcast = true;
  for (int i = 0; i < 6; i++) {
    if (SLAVE_MAC[i] != 0xFF) { isBroadcast = false; break; }
  }
  Serial.print("[WIRELESS] ESP-NOW init OK (");
  Serial.print(isBroadcast ? "broadcast" : "peer-to-peer");
  Serial.println(" mode)");
  return true;
}

bool wirelessSendFrame(const SensorFrame& f) {
  esp_err_t r = esp_now_send(SLAVE_MAC, (uint8_t*)&f, sizeof(f));
  return (r == ESP_OK);
}

// ====== 发送统计读取 (P1 改进) ======
// 返回 (ok, fail) 两个累计计数, 主循环用来看丢包率
void wirelessGetSendStats(uint32_t& ok, uint32_t& fail) {
  // 在主循环上下文读, 跟回调都在 core 1, 不会被撕开
  ok = sendOkCount;
  fail = sendFailCount;
}

void wirelessResetSendStats() {
  sendOkCount = 0;
  sendFailCount = 0;
}