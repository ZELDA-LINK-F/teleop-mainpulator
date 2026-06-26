/*
 * ESP32-S3 N16R8 板子测试 2：板载 LED 测试
 * 用途：验证 GPIO 输出
 *
 * 不同板子的板载 LED 位置不一样，这里给出三种最常见的：
 *   - GPIO48: 大多数 ESP32-S3-DevKitC-1 / 多数 N16R8 核心板
 *   - GPIO2 : 一些 Waveshare / 合宙 / 部分国产板
 *   - GPIO38: 部分老版本核心板
 *
 * 把 #define ACTIVE_LED 那行注释/取消注释，挨个试，
 * 哪个灯会闪就说明板载 LED 在那个引脚。
 *
 * 注意：S3 的 RGB LED 如果是共阳的（高电平灭、低电平亮），
 * 下面用了 LOW 点亮、 HIGH 熄灭。
 */

#define ACTIVE_LED 48   // 先试 48，不亮改成 2，还不亮改成 38

void setup() {
  pinMode(ACTIVE_LED, OUTPUT);
  Serial.begin(115200);
  delay(1000);
  Serial.print("Blink test on GPIO ");
  Serial.println(ACTIVE_LED);
}

void loop() {
  digitalWrite(ACTIVE_LED, LOW);   // 点亮（低电平有效）
  Serial.println("LED ON");
  delay(500);
  digitalWrite(ACTIVE_LED, HIGH);  // 熄灭
  Serial.println("LED OFF");
  delay(500);
}
