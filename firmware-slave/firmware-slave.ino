// firmware-slave/firmware-slave.ino
// 右手爪执行端 - 主程序
// 阶段 1: 框架版, 收 master 数据并打印
// 硬件到了之后: 替换 servoSetAll 为真实舵机指令

#include "config.h"
#include "servo.h"
#include "protocol.h"
#include "wireless.h"

SensorFrame rxFrame;
unsigned long lastPrint = 0;
unsigned long lastStatsPrint = 0;  // P1: 定期打印 rx 统计

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("================================");
  Serial.println("  SLAVE (hand) starting...");
  Serial.println("================================");

  servoSetup();
  wirelessSetup();

  Serial.println("[MAIN] Waiting for master data...");
}

void loop() {
  SensorFrame f;
  if (wirelessGetLatest(f)) {
    // 收到新数据, 解析并动作
    // 1. 把 uint16_t (0-65535) 反归一化回 float (0.0-1.0)
    float flex[NUM_SERVOS];
    for (int i = 0; i < 5; i++) {
      flex[i] = (float)f.flex[i] / 65535.0f;
    }
    // 腕部暂时用四元数的 w 控制 (TODO: 改成姿态推算)
    flex[5] = (f.quat[0] + 1.0f) * 0.5f;  // w: -1~1 -> 0~1

    servoSetAll(flex);

    if (millis() - lastPrint >= 500) {  // 每 500ms 打印一次状态
      lastPrint = millis();
      framePrint(f);
    }
  }

  // 超时检测
  unsigned long lastRx = wirelessGetLastReceiveTime();
  if (lastRx > 0 && millis() - lastRx > WIRELESS_TIMEOUT_MS) {
    static unsigned long lastWarn = 0;
    if (millis() - lastWarn > 1000) {
      lastWarn = millis();
      Serial.print("[MAIN] WARN: no data for ");
      Serial.print(millis() - lastRx);
      Serial.println("ms");
    }
  }

  // ====== P1: 每秒打印一次 rx 统计 ======
  // 配合 master 端的 send stats, 能算出双向丢包率
  if (millis() - lastStatsPrint >= 1000) {
    lastStatsPrint = millis();
    uint32_t rx, lost;
    wirelessGetRxStats(rx, lost);
    if (rx > 0) {
      uint32_t total = rx + lost;
      Serial.print("[RX STATS] rx=");
      Serial.print(rx);
      Serial.print(" lost=");
      Serial.print(lost);
      Serial.print(" rate=");
      Serial.print((rx * 100) / total);
      Serial.println("%");
    }
  }
}