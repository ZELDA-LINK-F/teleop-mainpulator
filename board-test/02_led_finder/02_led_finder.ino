/*
 * WS2812 LED 探测器 V4（基于原理图）
 *
 * 关键发现：从 YD-ESP32-S3-COREBOARD V1.4 原理图看，WS2812 LED 接在 GPIO 48
 *
 * 行为：
 *   - 每个候选 GPIO 跑 5 色循环（红绿蓝白紫）
 *   - 串口打印当前测试的 GPIO，方便你对照
 *   - 全部测试完等按 RST 重跑
 */

#include <FastLED.h>

#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

template<int PIN>
void testPinHardcoded() {
  CLEDController& ctrl = FastLED.addLeds<WS2812, PIN, GRB>(leds, NUM_LEDS);

  Serial.print("\n[");
  Serial.print(PIN);
  Serial.print("] Red ");
  leds[0] = CRGB::Red;
  ctrl.showLeds(255);
  delay(400);
  leds[0] = CRGB::Black;
  ctrl.showLeds(0);
  delay(150);

  Serial.print("Green ");
  leds[0] = CRGB::Green;
  ctrl.showLeds(255);
  delay(400);
  leds[0] = CRGB::Black;
  ctrl.showLeds(0);
  delay(150);

  Serial.print("Blue ");
  leds[0] = CRGB::Blue;
  ctrl.showLeds(255);
  delay(400);
  leds[0] = CRGB::Black;
  ctrl.showLeds(0);
  delay(150);

  Serial.print("White ");
  leds[0] = CRGB::White;
  ctrl.showLeds(255);
  delay(400);
  leds[0] = CRGB::Black;
  ctrl.showLeds(0);
  delay(150);

  Serial.print("Purple ");
  leds[0] = CRGB::Purple;
  ctrl.showLeds(255);
  delay(400);
  leds[0] = CRGB::Black;
  ctrl.showLeds(0);
  delay(150);

  Serial.println("done");
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("================================");
  Serial.println("YD-ESP32-S3 V4 LED Finder");
  Serial.println("Top suspect: GPIO 48 (per schematic)");
  Serial.println("================================");

  // 原理图确认：GPIO 48 是 WS2812 控制脚
  testPinHardcoded<48>();
  delay(2000);

  // 备选：GPIO 38（官方 DevKitC-1 位置，可能 YD 板也兼容）
  testPinHardcoded<38>();
  delay(1500);

  // 其他常见脚位
  testPinHardcoded<21>();
  delay(1000);
  testPinHardcoded<2>();
  delay(1000);
  testPinHardcoded<8>();
  delay(1000);
  testPinHardcoded<42>();
  delay(1000);

  Serial.println("\n================================");
  Serial.println("All candidates done.");
  Serial.println("If LED lit up, check serial for [xx] markers");
  Serial.println("Press RST to repeat.");
  Serial.println("================================");
}

void loop() {
  delay(1000);
}
