// firmware-master/config.h
// 左手套采集端 - 引脚和常量定义

#ifndef CONFIG_H
#define CONFIG_H

// ====== 弯曲传感器 (5 个) ======
// ESP32-S3 的 ADC1 通道 GPIO 映射：
// GPIO1=ADC1_CH0, GPIO2=ADC1_CH1, GPIO5=ADC1_CH4, GPIO6=ADC1_CH5, GPIO7=ADC1_CH6
// 避开了 GPIO 3(strapping), 4(留给slave的DIR), 8/9(I2C)
const int FLEX_PINS[5] = {1, 2, 5, 6, 7};
const int NUM_FLEX = 5;

// ====== BNO055 IMU ======
// I2C 接口
const int I2C_SDA = 8;
const int I2C_SCL = 9;

// IMU 硬件开关: 0 = 用 stub (阶段 1, 硬件没到), 1 = 用真实 BNO055 (阶段 3)
// 切到 1 之前: 装 Adafruit_BNO055 + Adafruit_Sensor 库 (Arduino IDE 库管理器)
#define IMU_HARDWARE_READY 0

// ====== 通信参数 ======
// 每 10ms 发一帧 (100Hz), 跟 README 协议一致
const int SEND_INTERVAL_MS = 10;

// ====== 校准参数 (2026-06-28 实测) ======
// 硬件: SpectraFlex FLX 55mm + 47kΩ 上拉电阻 + ESP32 GPIO 1 (3.3V 参考)
// 弯曲传感器平直时的 ADC 值
const int FLEX_RAW_FLAT[5]  = {1180, 1180, 1180, 1180, 1180};
// 弯曲传感器最大弯曲时的 ADC 值
const int FLEX_RAW_BENT[5]  = {2500, 2500, 2500, 2500, 2500};
// TODO: 阶段 3 接 5 个传感器时, 每个单独校准 (datasheet ±20%)

#endif