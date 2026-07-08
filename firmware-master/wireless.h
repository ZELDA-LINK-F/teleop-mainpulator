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

// TODO: 把 broadcast 改成 peer (用对方板子的真实 MAC)
// uint8_t slaveMac[6] = {0xXX, 0xXX, 0xXX, 0xXX, 0xXX, 0xXX};

#endif