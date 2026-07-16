// firmware-slave/firmware-slave.ino
// 右手爪执行端 - 主程序
// 收 master 无线数据 → 驱动 6 个 LX-16A 舵机

#include "config.h"
#include "servo.h"
#include "protocol.h"
#include "wireless.h"

// 断线安全位状态机
static bool safeModeActive = false;
static int rxStreak = 0;
const int RX_STREAK_THRESHOLD = 10;  // 连续 10 帧才退出安全模式

// 延迟监控
static unsigned long lastFrameMs = 0;
static unsigned long lastStatusPrint = 0;

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
    unsigned long now = millis();
    unsigned long interval = now - lastFrameMs;
    lastFrameMs = now;
    rxStreak++;

    // 连续收到足够多帧才退出安全模式
    if (safeModeActive && rxStreak >= RX_STREAK_THRESHOLD) {
      Serial.println("[MAIN] Link restored");
      safeModeActive = false;
    }

    // flex[0..4] 是 uint16_t [0, 65535], 映射到 float [0, 1]
    for (int i = 0; i < 5; i++) {
      float norm = f.flex[i] / 65535.0f;
      servoSetNormalized(SERVO_IDS[i], norm);
    }
    // 腕部 (ID=6) 暂时固定中间位置
    servoSetNormalized(6, 0.5f);

    // 每秒打印一次状态: 帧间隔 + flex 值 + rx 统计
    if (now - lastStatusPrint >= 1000) {
      lastStatusPrint = now;
      uint32_t rx, lost;
      wirelessGetRxStats(rx, lost);

      Serial.print("[STATUS] interval=");
      Serial.print(interval);
      Serial.print("ms  flex=[");
      for (int i = 0; i < 5; i++) {
        Serial.print(f.flex[i]);
        if (i < 4) Serial.print(",");
      }
      Serial.print("]  rx=");
      Serial.print(rx);
      Serial.print(" lost=");
      Serial.println(lost);
    }
  }

  // 断线检测
  if (!safeModeActive &&
      (millis() - wirelessGetLastReceiveTime() > SAFE_POSITION_TIMEOUT_MS)) {
    Serial.println("[MAIN] Link lost!");
    servoSetSafe();
    safeModeActive = true;
    rxStreak = 0;
  }
}
