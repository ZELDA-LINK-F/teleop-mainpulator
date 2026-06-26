// firmware-master/imu.cpp
// BNO055 IMU 模块实现

#include "imu.h"
#include "config.h"
#include <Wire.h>
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