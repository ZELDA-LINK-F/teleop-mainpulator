/*
 * ESP32-S3 N16R8 板子测试 1：串口回环测试
 * 用途：验证 USB 链路、驱动、烧录、串口监视器是否正常
 *
 * 操作流程：
 *   1. 选择开发板：ESP32S3 Dev Module
 *   2. 选择正确的 COM 口（插上板子后才出现的那个）
 *   3. 上传代码
 *   4. 打开串口监视器（波特率 115200）
 *   5. 应该每 1 秒看到一次 "Hello from ESP32-S3! ..."
 *   6. 在串口监视器输入框里随便打几个字，按回车，会被回显出来
 */

void setup() {
  Serial.begin(115200);
  // S3 启动比 S2 快一点，但还是等一下串口就绪
  delay(1500);

  Serial.println();
  Serial.println("================================");
  Serial.println("  ESP32-S3 N16R8 串口测试启动");
  Serial.println("================================");
  Serial.print("Chip Model: ");
  Serial.println(ESP.getChipModel());
  Serial.print("Chip Revision: v");
  Serial.println(ESP.getChipRevision());
  Serial.print("CPU Frequency: ");
  Serial.print(ESP.getCpuFreqMHz());
  Serial.println(" MHz");
  Serial.print("Flash Size: ");
  Serial.print(ESP.getFlashChipSize() / 1024 / 1024);
  Serial.println(" MB");
  Serial.print("PSRAM Size: ");
  Serial.print(ESP.getPsramSize() / 1024 / 1024);
  Serial.println(" MB");
  Serial.print("Free Heap: ");
  Serial.print(ESP.getFreeHeap() / 1024);
  Serial.println(" KB");
  Serial.print("SDK Version: ");
  Serial.println(ESP.getSdkVersion());
  Serial.println("================================");
  Serial.println("输入任意字符回车测试回显...");
}

int counter = 0;

void loop() {
  // 定时输出心跳，证明主循环还活着
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint >= 1000) {
    lastPrint = millis();
    Serial.print("Heartbeat #");
    Serial.print(counter++);
    Serial.print(" | uptime=");
    Serial.print(millis() / 1000);
    Serial.println("s");
  }

  // 串口接收回显
  while (Serial.available()) {
    char c = Serial.read();
    Serial.write(c);
  }
}
