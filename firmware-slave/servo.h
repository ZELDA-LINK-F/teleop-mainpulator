// firmware-slave/servo.h
// LX-16A 舵机控制模块

#ifndef SERVO_H
#define SERVO_H

#include <Arduino.h>
#include "config.h"

bool servoSetup();

// 给所有舵机上电 (LOAD=1), servoSetup() 会自动调一次
// 断线恢复后也可以单独调用
void servoPowerOn();

// 设置单个舵机角度 (0.0-1.0 归一化, 内部映射到 LX-16A 角度范围)
// timeMs: 1~30000=匀速转动到目标的时间 (默认 50ms)
void servoSetNormalized(int servoId, float normalized, uint16_t timeMs = 50);

// 同时设置 5 指 + 1 腕, normalized 长度 = 6
// 顺序: 拇指, 食指, 中指, 无名指, 小指, 腕
void servoSetAll(const float normalized[NUM_SERVOS]);

// ====== P1: 回安全姿势 ======
// 通信断了的时候调, 让舵机回到 config.h 里 SERVO_SAFE_NORM 定义的姿势
// (默认全 0 = 张开手)
void servoSetSafe();

// 调试用: 打印当前所有舵机状态
void servoPrintStatus();

#endif