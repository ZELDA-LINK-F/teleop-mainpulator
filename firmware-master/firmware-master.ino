// firmware-master/firmware-master.ino
// 左手套采集端 - 主程序
// 阶段 1: 框架版, 用 stub 数据测通信链路
// 硬件到了之后: 替换 flexSensorReadNormalized / imuReadQuat 的真实数据

#include "config.h"
#include "flex_sensor.h"
#include "imu.h"
#include "protocol.h"
#include "wireless.h"

SensorFrame frame;
uint16_t seq = 0;
unsigned long lastSend = 0;

// 模拟传感器数据 (硬件没到时用)
static float fakeFlex[NUM_FLEX] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
static float fakeQuat[4] = {1.0f, 0.0f, 0.0f, 0.0f};  // 单位四元数
static unsigned long fakeStart = 0;

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

  fakeStart = millis();
  Serial.println("[MAIN] Ready, sending every 10ms");
}

void loop() {
  // 用模拟数据生成一帧 (硬件到了改用真数据)
  // float flex[NUM_FLEX];
  // flexSensorReadNormalized(flex);
  // imuReadQuat(fakeQuat);
  // 模拟正弦波动, 串口能看出变化
  float t = (millis() - fakeStart) / 1000.0f;
  for (int i = 0; i < NUM_FLEX; i++) {
    fakeFlex[i] = 0.5f + 0.4f * sin(t * (i + 1));
  }

  if (millis() - lastSend >= SEND_INTERVAL_MS) {
    lastSend = millis();
    frameInit(frame);
    frameSetFlex(frame, fakeFlex);
    frameSetQuat(frame, fakeQuat);
    frame.seq = seq++;
    wirelessSendFrame(frame);
    if (seq % 10 == 0) {  // 每 10 帧打印一次, 不刷屏
      framePrint(frame);
    }
  }
}