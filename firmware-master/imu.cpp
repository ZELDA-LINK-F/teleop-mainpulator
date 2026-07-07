// firmware-master/imu.cpp
// BNO055 IMU 模块实现
//
// 阶段 1 (2026-06-28): IMU 硬件未到, 编译时选 IMU_HARDWARE_READY=0 (stub)
// 阶段 3 拿到 BNO055 后:
//   1. Arduino IDE 装 Adafruit_BNO055 + Adafruit_Sensor + Adafruit_BusIO
//   2. 把 config.h 里 IMU_HARDWARE_READY 改成 1
//   3. 重新编译烧录, 就能用真实 IMU 数据

#include "imu.h"
#include "config.h"
#include <Wire.h>  // ESP32 Arduino 内置, stub 模式也要 (Wire 库没副作用)

#if IMU_HARDWARE_READY
// ========== 真实 BNO055 代码 ==========
// 依赖库: Adafruit_BNO055, Adafruit_Sensor, Adafruit_BusIO

#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// 构造: (sensor_id, i2c_addr, Wire 指针)
// 默认地址 0x28 (ADDR 引脚接 GND)
// 如果 ADDR 接 VIN, 改成 0x29
static Adafruit_BNO055 bno(55, 0x28, &Wire);

bool imuSetup() {
  // I2C 用我们指定的引脚 (ESP32-S3 软映射)
  Wire.begin(I2C_SDA, I2C_SCL);

  // NDOF = 9 轴融合模式 (加速度+陀螺仪+磁力计)
  // 上电后 BNO055 会自动校准, 不需要手动搞
  if (!bno.begin(OPERATION_MODE_NDOF)) {
    Serial.println("[IMU] BNO055 not detected, check wiring");
    return false;
  }
  delay(100);
  // 用外部晶振 (如果板子上有 32.768kHz 晶振, 更准)
  // 没有也行, BNO055 内部有 oscillator
  bno.setExtCrystalUse(true);

  Serial.println("[IMU] BNO055 init OK");
  return true;
}

bool imuReadQuat(float quat[4]) {
  // BNO055 内部已经融合好了, 直接读 quaternion
  imu::Quaternion q = bno.getQuat();
  quat[0] = q.w();
  quat[1] = q.x();
  quat[2] = q.y();
  quat[3] = q.z();
  return true;
}

#else  // ========== Stub 模式 (阶段 1 用) ==========
// 硬件没到时用这个, 不依赖任何外部库, 编译能过
// 返回"无旋转"四元数 (1,0,0,0), 等价于 IMU 不存在

bool imuSetup() {
  Serial.println("[IMU] Stub mode (set IMU_HARDWARE_READY=1 to use real BNO055)");
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
