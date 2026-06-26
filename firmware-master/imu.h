// firmware-master/imu.h
// BNO055 IMU 模块

#ifndef IMU_H
#define IMU_H

#include <Arduino.h>

// quat[4] = {w, x, y, z}
bool imuSetup();
bool imuReadQuat(float quat[4]);

#endif