// firmware-slave/config.h
// 右手爪执行端 - 引脚和常量定义

#ifndef CONFIG_H
#define CONFIG_H

// ====== LX-16A 舵机总线 ======
// 串口 2 (UART2) - 不占用默认 Serial (UART0)
const int SERVO_TX_PIN = 17;   // ESP32 TX2 -> 转接板 TX
const int SERVO_DIR_PIN = 4;   // ESP32 GPIO4 -> 转接板 DIR
const int SERVO_BAUD = 115200;

// ====== 舵机 ID 分配 (跟 README 一致) ======
const int SERVO_ID_THUMB  = 1;  // 拇指
const int SERVO_ID_INDEX  = 2;  // 食指
const int SERVO_ID_MIDDLE = 3;  // 中指
const int SERVO_ID_RING   = 4;  // 无名指
const int SERVO_ID_PINKY  = 5;  // 小指
const int SERVO_ID_WRIST  = 6;  // 腕部
const int NUM_SERVOS = 6;
const int SERVO_IDS[NUM_SERVOS] = {1, 2, 3, 4, 5, 6};

// ====== 舵机角度范围 (TODO: 实测填入) ======
const int SERVO_ANGLE_MIN = 0;     // 放松
const int SERVO_ANGLE_MAX = 1000;  // 最大弯曲 (LX-16A 单位 0-1000 = 0-240度)

// ====== 通信参数 ======
const int WIRELESS_TIMEOUT_MS = 100;  // 100ms 没收到新数据认为断连

#endif