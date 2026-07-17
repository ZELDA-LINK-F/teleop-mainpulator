// firmware-master/wireless.h
// ESP-NOW 无线通信 (master 端 - 发送)

#ifndef WIRELESS_H
#define WIRELESS_H

#include <Arduino.h>
#include "protocol.h"

bool wirelessSetup();
bool wirelessSendFrame(const SensorFrame& f);

// ====== P1 改进: 发送统计 ======
// 让 master 知道"发送成功率", 不再盲目以为"调了 esp_now_send 就发出去了"
void wirelessGetSendStats(uint32_t& ok, uint32_t& fail);
void wirelessResetSendStats();

// SLAVE_MAC 定义在 config.h, 默认 broadcast, 改成真实 MAC 即升级 peer-to-peer

#endif