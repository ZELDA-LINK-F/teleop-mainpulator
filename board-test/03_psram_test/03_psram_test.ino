/*
 * ESP32-S3 N16R8 板子测试 3：PSRAM 验证
 * 用途：确认 8MB PSRAM 真的可用（这块板子的核心价值之一）
 *
 * 如果 IDE 里 PSRAM 选项没选对，这里读出来的 size 会是 0
 * 或显示 "PSRAM not available"
 *
 * IDE 设置：Tools → PSRAM → OPI PSRAM  ← 必须
 */

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println();
  Serial.println("====== PSRAM Test ======");

  if (psramFound()) {
    Serial.print("[OK] PSRAM detected, size = ");
    Serial.print(ESP.getPsramSize());
    Serial.println(" bytes");
    Serial.print("    Free PSRAM = ");
    Serial.print(ESP.getFreePsram());
    Serial.println(" bytes");

    // 实际写读一下，看看是不是真的能存数据
    size_t allocSize = 1024 * 1024;  // 1MB
    uint8_t* buf = (uint8_t*) ps_malloc(allocSize);
    if (buf == nullptr) {
      Serial.println("[FAIL] ps_malloc 1MB failed!");
    } else {
      Serial.println("[OK] Allocated 1MB in PSRAM");

      // 写入测试
      for (size_t i = 0; i < allocSize; i++) {
        buf[i] = (uint8_t)(i & 0xFF);
      }
      Serial.println("[OK] Wrote 1MB");

      // 读回校验
      bool ok = true;
      for (size_t i = 0; i < allocSize; i++) {
        if (buf[i] != (uint8_t)(i & 0xFF)) {
          ok = false;
          Serial.print("[FAIL] Mismatch at byte ");
          Serial.println(i);
          break;
        }
      }
      if (ok) {
        Serial.println("[OK] Read-back 1MB verified, PSRAM is fully functional");
      }
      free(buf);
    }
  } else {
    Serial.println("[FAIL] PSRAM NOT FOUND!");
    Serial.println("  -> IDE 里 Tools -> PSRAM 选 OPI PSRAM");
    Serial.println("  -> 或者这块板子其实不带 PSRAM（不是 R8 型号）");
  }
  Serial.println("=======================");
}

void loop() {
  delay(1000);
}
