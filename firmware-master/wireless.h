// firmware-master/wireless.h
// ESP-NOW 无线通信 (master 端 - 发送)

#ifndef WIRELESS_H
#define WIRELESS_H

#include <Arduino.h>
#include "protocol.h"

bool wirelessSetup();
bool wirelessSendFrame(const SensorFrame& f);

// TODO: 把 broadcast 改成 peer (用对方板子的真实 MAC)
// uint8_t slaveMac[6] = {0xXX, 0xXX, 0xXX, 0xXX, 0xXX, 0xXX};

#endif