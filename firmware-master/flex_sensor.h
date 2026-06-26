// firmware-master/flex_sensor.h
// 弯曲传感器读取模块

#ifndef FLEX_SENSOR_H
#define FLEX_SENSOR_H

#include <Arduino.h>
#include "config.h"

// 初始化所有弯曲传感器引脚
void flexSensorSetup();

// 读取所有传感器原始值 (0-4095, 12-bit)
// 返回 true 表示读取成功
bool flexSensorReadRaw(uint16_t raw[NUM_FLEX]);

// 读取并归一化 (0.0 = 平直, 1.0 = 最大弯曲)
// 在校准值之间线性插值
bool flexSensorReadNormalized(float normalized[NUM_FLEX]);

#endif