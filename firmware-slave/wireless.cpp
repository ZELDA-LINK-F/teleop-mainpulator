// firmware-slave/wireless.cpp
// ESP-NOW 接收实现

#include "wireless.h"
#include <esp_now.h>
#include <WiFi.h>

static volatile bool hasNew = false;
static SensorFrame latest;
static volatile unsigned long lastRxMs = 0;

// ====== P1 改进: 接收统计 ======
// volatile: onReceive 跟 loop 在同一核但异步触发, 主循环读必须 volatile
// 单核 ESP32 上 uint32_t/uint16_t 读写是原子的
static volatile uint32_t rxCount = 0;       // 总共收到多少帧
static volatile uint16_t seqLastSeen = 0;   // 上一次看到的 seq (16-bit wrap 时也能正确判断, 因为差值取模 65536)
static volatile bool seqEverSeen = false;   // 是否收到过任何帧 (用来跳过第一次, 不报"丢了 65535 帧")
static volatile uint32_t seqLostCount = 0;  // 因 seq 跳跃推算的丢帧数

// ESP32 Arduino 库 3.x 升级后, esp_now 注册的接收回调签名从
//   void cb(const uint8_t* mac, const uint8_t* data, int len)
// 改成了
//   void cb(const esp_now_recv_info_t* info, const uint8_t* data, int len)
// 跟 master 端 onSend 是同一个 ESP-IDF v5 升级带来的变化 (2026-06-28 踩过坑)
// 我们不用 MAC, 所以参数名改成 info 占位就行, 函数体不变
// 真要拿发送方 MAC 用 info->src_addr (uint8_t[6])
static void onReceive(const esp_now_recv_info_t* info, const uint8_t* data, int len) {
  if (len == sizeof(SensorFrame)) {
    // 先复制数据 (可能后面 memcpy 会跟 loop 读 latest 冲突)
    SensorFrame tmp;
    memcpy(&tmp, data, sizeof(SensorFrame));

    // ====== P1: 校验 seq 连续性 ======
    // master 每帧 seq++, 我们期望 slave 收到的也是 seq, seq+1, seq+2 ...
    // 如果跳号, 说明中间丢了帧 (无线干扰 / master 阻塞 / slave 处理不过来)
    uint16_t seq = tmp.seq;
    if (seqEverSeen) {
      uint16_t expected = (uint16_t)(seqLastSeen + 1);  // 自动 wrap
      if (seq != expected) {
        // 跳跃! 算丢失了多少帧
        // volatile + += 也 deprecated, 显式写
        uint16_t gap = (uint16_t)(seq - expected);  // wrap-safe 减法
        // 保护: gap > 100 = 大概率是 master 复位 (seq wrap 到 0)
        //  100Hz 下连续丢 100 帧 = 1 秒, 已经触发了断线安全位 (300ms)
        //  真正的"连续丢包"gap 不会超过 30 (300ms 触发前就会断流)
        //  所以 gap > 100 视为 master 重启, 不计入 lost
        if (gap <= 100) {
          seqLostCount = seqLostCount + gap;
        }
        // 不打日志, 不影响主流程; 下一帧自然按新 seq 建立基准
      }
    }
    seqLastSeen = seq;
    seqEverSeen = true;
    // volatile + ++ 在新 C++ 标准里 deprecated, 显式写成"读出来 + 1 再写回去"
    rxCount = rxCount + 1;

    // 最后才更新 latest + hasNew, 避免 loop 读到半新半旧
    memcpy(&latest, &tmp, sizeof(SensorFrame));
    hasNew = true;
    lastRxMs = millis();
  }
}

bool wirelessSetup() {
  WiFi.mode(WIFI_STA);
  // 给 STA 模式一点时间生效, 否则 WiFi.macAddress() 在 ESP32-S3 + Arduino 3.x
  // 上会返回 00:00:00:00:00:00 (跟 master 同一原因)
  delay(100);
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

// ====== P1 改进: 接收统计读取 ======
void wirelessGetRxStats(uint32_t& rx, uint32_t& lost) {
  rx = rxCount;
  lost = seqLostCount;
}

void wirelessResetRxStats() {
  rxCount = 0;
  seqLostCount = 0;
  // 注意: 不重置 seqLastSeen 和 seqEverSeen, 因为 seq 本身是连续的, 重置会让人误以为"丢了 seqLastSeen 帧"
}