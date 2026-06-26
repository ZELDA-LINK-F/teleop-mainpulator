// firmware-master/protocol.h
// 32 字节主从通信协议 (跟 README 协议一致)

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>

// 32 字节帧结构, packed 确保内存布局严格
struct __attribute__((packed)) SensorFrame {
  uint16_t flex[5];   // [0-9]   5 个弯曲传感器 (uint16_t)
  float quat[4];      // [10-25] IMU 四元数 (w, x, y, z)
  uint16_t seq;       // [26-27] 序列号
  uint8_t reserved[4];// [28-31] 保留
};

// 填充 SensorFrame 的工具函数
void frameInit(SensorFrame& f);
void frameSetFlex(SensorFrame& f, const float flex[5]);
void frameSetQuat(SensorFrame& f, const float quat[4]);

// 调试打印
void framePrint(const SensorFrame& f);

#endif