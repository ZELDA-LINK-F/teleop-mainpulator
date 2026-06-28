/*
 * ESP32-S3 + SpectraFlex FLX 55mm 弯曲传感器测试
 *
 * ============== 接线图 ==============
 *
 *   3V3 -----[47kΩ]-----+-----[FLX 弯曲传感器]----- GND
 *                        |
 *                        +----- GPIO 1 (ADC1_CH0)
 *
 * ============== 工具菜单设置 ==============
 * （跟之前 01_serial_test 一样，参考 docs/板子引脚备忘.md）
 *   Board:              ESP32S3 Dev Module
 *   USB CDC On Boot:    Enabled
 *   Upload Speed:       921600
 *   COM 口:             COM5（按你电脑实际显示的）
 *
 * ============== 怎么看 ==============
 *   1. 烧录代码
 *   2. 打开串口监视器 (波特率 115200)
 *   3. 每 100ms 打印一行: ADC 值 + 进度条
 *   4. 弯曲传感器,看 ADC 值变化
 *   5. 记下: 平直时的值 / 弯曲 180° 时的值
 *
 * ============== 预期范围 ==============
 *   (按 47kΩ 上拉 + 18kΩ 平直算)
 *   平直:      ~1100
 *   弯曲 90°:  ~1500
 *   弯曲 180°: ~1800 ~ 2500
 *   方向:      弯曲时 ADC 应该**变大**
 */

const int FLEX_PIN = 1;  // GPIO 1 = ADC1_CH0

// ===== 校准值（用你的实测数据）=====
// 平直时 ADC ≈ 1180
// 弯曲 180° 时 ADC ≈ 2500
const int CAL_FLAT = 1180;
const int CAL_BENT = 2500;

void setup() {
  // 启动串口, 115200 波特率 (跟之前测试代码一致)
  Serial.begin(115200);

  // 等串口监视器就绪 (不然开头几行打印会丢)
  delay(1500);

  // ADC 设成 12-bit (0~4095), 弯曲传感器要精细读数
  analogReadResolution(12);

  // GPIO 1 设成输入 (虽然 ADC 引脚默认就是输入, 写一下更清楚)
  pinMode(FLEX_PIN, INPUT);

  Serial.println();
  Serial.println("================================");
  Serial.println("  弯曲传感器测试");
  Serial.println("  型号: SpectraFlex FLX 55mm");
  Serial.println("  上拉电阻: 47kΩ");
  Serial.println("================================");
  Serial.println("校准值 (用你的实测数据):");
  Serial.print("  CAL_FLAT = "); Serial.println(CAL_FLAT);
  Serial.print("  CAL_BENT = "); Serial.println(CAL_BENT);
  Serial.println("================================");
  Serial.println("预期归一化值:");
  Serial.println("  平直      → 0.00");
  Serial.println("  弯曲 90°  → ~0.62");
  Serial.println("  弯曲 180° → 1.00");
  Serial.println("================================");
}

void loop() {
  // 读 ADC 原始值 (0~4095)
  int raw = analogRead(FLEX_PIN);

  // ====== 归一化计算 ======
  // 公式: norm = (raw - FLAT) / (BENT - FLAT)
  // raw = FLAT 时 → norm = 0.0 (平直)
  // raw = BENT 时 → norm = 1.0 (弯到底)
  float norm = (float)(raw - CAL_FLAT) / (float)(CAL_BENT - CAL_FLAT);

  // 钳制到 [0, 1] 范围 (防止异常值越界)
  if (norm < 0.0f) norm = 0.0f;
  if (norm > 1.0f) norm = 1.0f;

  // 打印原始值 + 归一化值
  Serial.print("ADC: ");
  Serial.print(raw);
  Serial.print(" | norm: ");
  Serial.print(norm, 2);  // 保留 2 位小数

  // 画个进度条方便看趋势 (用归一化值, 0~50 个字符)
  Serial.print(" | ");
  int bars = (int)(norm * 50);  // 0.0~1.0 → 0~50 个字符
  for (int i = 0; i < bars; i++) {
    Serial.print("=");
  }
  Serial.println();

  // 100ms 刷新一次 = 10Hz, 看着不闪
  delay(100);
}