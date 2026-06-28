// firmware-master/firmware-master.ino
// 左手套采集端 - 主程序
// 阶段 1: 弯曲传感器已接入 (2026-06-28), IMU 还没到

#include "config.h"
#include "flex_sensor.h"
#include "imu.h"
#include "protocol.h"
#include "wireless.h"

SensorFrame frame;
uint16_t seq = 0;
unsigned long lastSend = 0;

// IMU 还没到, 用单位四元数占位 (无旋转)
static float fakeQuat[4] = {1.0f, 0.0f, 0.0f, 0.0f};

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("================================");
  Serial.println("  MASTER (glove) starting...");
  Serial.println("================================");

  flexSensorSetup();
  // imuSetup();  // 硬件没到先注释
  wirelessSetup();

  Serial.println("[MAIN] Ready, sending every 10ms");
}

void loop() {
  // ====== 读真实弯曲传感器 (5 个) ======
  // flexSensorReadNormalized 会自动用 config.h 的校准值归一化到 [0, 1]
  float flex[NUM_FLEX];
  flexSensorReadNormalized(flex);

  if (millis() - lastSend >= SEND_INTERVAL_MS) {
    lastSend = millis();
    frameInit(frame);
    frameSetFlex(frame, flex);            // ← 真实数据
    frameSetQuat(frame, fakeQuat);        // ← IMU 还没到, 暂时用占位
    frame.seq = seq++;
    wirelessSendFrame(frame);
    if (seq % 10 == 0) {  // 每 10 帧打印一次, 不刷屏
      framePrint(frame);
    }
  }
}