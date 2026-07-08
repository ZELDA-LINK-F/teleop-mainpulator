// firmware-slave/wireless.h
// ESP-NOW 接收端

#ifndef WIRELESS_H
#define WIRELESS_H

#include <Arduino.h>
#include "protocol.h"

bool wirelessSetup();

// slave 端: 检查是否收到新数据, 返回最新帧
// 返回 true 表示有新数据, false 表示无新数据
bool wirelessGetLatest(SensorFrame& out);

// 返回最近一次收到数据的 millis() 时间 (用于判断超时断连)
unsigned long wirelessGetLastReceiveTime();

// ====== P1 改进: 接收统计 ======
// 跟 master 端对应: slave 能看出"实际收到多少 + 推算丢了多少"
// rx = 总收到帧数, lost = 因为 seq 跳跃推算的丢帧数
// 比例: lost / (rx + lost) ≈ 真实丢包率
void wirelessGetRxStats(uint32_t& rx, uint32_t& lost);
void wirelessResetRxStats();

#endif