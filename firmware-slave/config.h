// firmware-slave/config.h
// 右手爪执行端 - 引脚和常量定义

#ifndef CONFIG_H
#define CONFIG_H

// ====== LX-16A 舵机总线 ======
// 串口 2 (UART2) - 不占用默认 Serial (UART0)
// 1kΩ 方案: TX 通过电阻出去, RX 直接接信号线, 单线半双工
const int SERVO_TX_PIN = 17;   // ESP32-S3 GPIO17 (U1TXD) → 1kΩ → 信号线
const int SERVO_RX_PIN = 18;   // ESP32-S3 GPIO18 (U1RXD) → 信号线 (直接连)
const int SERVO_BAUD = 115200;

// DIR_PIN 已弃用 (1kΩ 方案不需要 DIR)
// 原值: const int SERVO_DIR_PIN = 4; (2026-07-07 删除)
// GPIO 4 现在空出来了, 可以给 PWM / 第二 UART / 其他用途

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

// ====== P1: 断线安全位 ======
// 通信断了这么久, 舵机自动回安全姿势 (全 0 = 张开手)
// 300ms = 丢 30 帧 @ 100Hz, 足够排除偶发抖动又不至于反应慢
const unsigned long SAFE_POSITION_TIMEOUT_MS = 300;

// 安全姿势: 6 个舵机归一化值 (0.0 = 完全放松/张开)
// LX-16A 默认角度 0 = 放松位, 所以全 0 就是"张开手"姿势
// 阶段 1 用这个最保守的姿势; 阶段 3 拿到 IMU 后可以改成"手掌朝上"
const float SERVO_SAFE_NORM[NUM_SERVOS] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};

#endif