// firmware-slave/servo.h
// LX-16A 舵机控制模块

#ifndef SERVO_H
#define SERVO_H

#include <Arduino.h>
#include "config.h"

bool servoSetup();

// 设置单个舵机角度 (0.0-1.0 归一化, 内部映射到 LX-16A 角度范围)
void servoSetNormalized(int servoId, float normalized);

// 同时设置 5 指 + 1 腕, normalized 长度 = 6
// 顺序: 拇指, 食指, 中指, 无名指, 小指, 腕
void servoSetAll(const float normalized[NUM_SERVOS]);

// 调试用: 打印当前所有舵机状态
void servoPrintStatus();

#endif