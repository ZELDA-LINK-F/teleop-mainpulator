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
unsigned long lastStatsPrint = 0;  // P1: 定期打印 send 统计

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
  float flex[NUM_FLEX];
  flexSensorReadNormalized(flex);

  // 每秒打印一次原始 ADC 值 (校准用)
  static unsigned long lastRawPrint = 0;
  if (millis() - lastRawPrint >= 1000) {
    lastRawPrint = millis();
    uint16_t raw[NUM_FLEX];
    flexSensorReadRaw(raw);
    Serial.print("[RAW ADC] ");
    for (int i = 0; i < NUM_FLEX; i++) {
      Serial.print(raw[i]);
      Serial.print(i < NUM_FLEX - 1 ? "," : "");
    }
    Serial.println();
  }

  if (millis() - lastSend >= SEND_INTERVAL_MS) {
    lastSend = millis();
    frameInit(frame);
    frameSetFlex(frame, flex);            // ← 真实数据
    frameSetQuat(frame, fakeQuat);        // ← IMU 还没到, 暂时用占位
    frame.seq = seq++;
    wirelessSendFrame(frame);
    if (seq % 100 == 0) {  // 每秒打印一次 (100Hz / 100 = 1次/秒)
      framePrint(frame);
    }
  }

  // ====== P1: 每秒打印一次 send 统计 ======
  // 看 sendOk / sendFail 比例就知道通信质量
  // 100% 成功 = 健康; 大量 fail = slave 没开机 / 距离太远 / 干扰
  if (millis() - lastStatsPrint >= 1000) {
    lastStatsPrint = millis();
    uint32_t ok, fail;
    wirelessGetSendStats(ok, fail);
    uint32_t total = ok + fail;
    if (total > 0) {
      Serial.print("[SEND STATS] ok=");
      Serial.print(ok);
      Serial.print(" fail=");
      Serial.print(fail);
      Serial.print(" rate=");
      Serial.print((ok * 100) / total);
      Serial.println("%");
    }
  }
}