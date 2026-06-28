// firmware-master/imu.cpp
// BNO055 IMU 模块实现
//
// 阶段 1 (2026-06-28): IMU 硬件未到, 使用 stub
// 阶段 3 拿到 BNO055 后: 把 #if 0 改成 #if 1, 装 Adafruit_BNO055 库

#include "imu.h"
#include "config.h"
#include <Wire.h>  // 阶段 1 也需要 (I2C 总线), ESP32 Arduino 内置

#if 0  // ========== IMU 真实代码 (硬件未到, 暂时禁用) ==========
// 下面这段依赖 Adafruit_BNO055 库, 阶段 1 编译时跳过

#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

static Adafruit_BNO055 bno(55, 0x28, &Wire);

bool imuSetup() {
  Wire.begin(I2C_SDA, I2C_SCL);
  if (!bno.begin(OPERATION_MODE_NDOF)) {
    Serial.println("[IMU] BNO055 not detected, check wiring");
    return false;
  }
  delay(100);
  bno.setExtCrystalUse(true);
  Serial.println("[IMU] BNO055 init OK");
  return true;
}

bool imuReadQuat(float quat[4]) {
  imu::Quaternion q = bno.getQuat();
  quat[0] = q.w();
  quat[1] = q.x();
  quat[2] = q.y();
  quat[3] = q.z();
  return true;
}

#else  // ========== IMU Stub (阶段 1 用) ==========
// 不依赖任何外部库, 编译能过
// 返回"无旋转"四元数 (1,0,0,0), 等价于 IMU 不存在

bool imuSetup() {
  Serial.println("[IMU] Stub mode (IMU hardware not connected)");
  return false;
}

bool imuReadQuat(float quat[4]) {
  // 单位四元数 (w=1, x=0, y=0, z=0) = 不旋转
  // 这样下游 slave 收到的姿态是"不动", 不会乱转舵机
  quat[0] = 1.0f;
  quat[1] = 0.0f;
  quat[2] = 0.0f;
  quat[3] = 0.0f;
  return true;
}

#endif