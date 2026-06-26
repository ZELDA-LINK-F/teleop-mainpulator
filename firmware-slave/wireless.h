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

#endif