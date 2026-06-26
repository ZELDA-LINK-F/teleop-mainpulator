// firmware-slave/protocol.h
// 跟 master 端完全相同 (本框架为清晰分别复制)
// 真实项目可以提取到 shared/ 目录

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>

struct __attribute__((packed)) SensorFrame {
  uint16_t flex[5];
  float quat[4];
  uint16_t seq;
  uint8_t reserved[4];
};

void frameInit(SensorFrame& f);
void frameSetFlex(SensorFrame& f, const float flex[5]);
void frameSetQuat(SensorFrame& f, const float quat[4]);
void framePrint(const SensorFrame& f);

#endif