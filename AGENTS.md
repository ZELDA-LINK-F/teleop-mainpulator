# AGENTS.md — Repo Guide for AI Agents

## What This Is

Teleoperation robotic hand project: left glove (flex sensors + IMU) captures hand motion → ESP32-S3 wireless → right robotic hand (6 servos). All docs and comments in Chinese.

## Repo Structure

```
firmware-master/    # Glove-side Arduino sketch (sensors → wireless TX)
firmware-slave/     # Hand-side Arduino sketch (wireless RX → servos)
board-test/         # Standalone test sketches (01-04), one per board-validation step
openscad/           # Parametric finger segment models (.scad + exported .stl + renders)
fusion-ai-assistant/# Fusion 360 Add-In for AI-assisted 3D modeling
docs/               # Pinout notes, reference links
stl/                # (empty — final prints go here)
ESP32-S3 资料/      # Vendor docs (gitignored)
my-project/         # Empty (contains only .mimocode/)
```

## Hardware Facts an Agent Must Know

- **Board**: YD-ESP32-S3-N16R8 (not official DevKitC). Board WS2812B LED is on **GPIO 48**, not 38.
- **USB**: Left Type-C = native USB (OTG), Right Type-C = CH343P UART0 (serial monitor).
- **Servos**: LX-16A, single-wire half-duplex bus. 1kΩ resistor on TX line — no DIR pin needed, no controller board needed. Baud: 115200. Servo IDs: 1=thumb, 2=index, 3=middle, 4=ring, 5=pinky, 6=wrist.
- **Flex sensors**: Voltage divider with 47kΩ pull-up. ADC on GPIO 1,2,5,6,7 (ADC1 channels). Calibration values in `firmware-master/config.h`.
- **IMU**: BNO055 on I2C (GPIO 8/9). Toggle `IMU_HARDWARE_READY` in `firmware-master/config.h` — currently 0 (stub), set to 1 when hardware arrives.
- **Communication protocol**: 32-byte frame @ 100Hz (10ms interval). Struct: flex[5] uint16 + quat[4] float + seq uint16 + reserved 4 bytes. Defined in `protocol.h`.

## Arduino IDE Settings (Verified)

From `docs/板子引脚备忘.md`:

| Setting | Value |
|---------|-------|
| Board | ESP32S3 Dev Module |
| USB CDC On Boot | Enabled |
| CPU Frequency | 240MHz (WiFi) |
| Flash Size | 16MB (128Mb) |
| Partition Scheme | Default 4MB with spiffs |
| PSRAM | OPI PSRAM |
| Upload Speed | 921600 (fallback: 115200) |

## Build & Upload

No build system (PlatformIO, Makefile) — pure Arduino IDE sketches. Each `firmware-*` directory is a standalone `.ino` project.

- **Upload master**: Open `firmware-master/firmware-master.ino` in Arduino IDE → select board → Upload
- **Upload slave**: Open `firmware-slave/firmware-slave.ino` in Arduino IDE → select board → Upload
- **Board tests**: Open `board-test/NN_name/NN_name.ino` → Upload
- **Serial monitor**: 115200 baud. Look for `[MAIN]`, `[SEND STATS]`, `[RX STATS]` prefixed lines.

## Key Gotchas

1. **No `src/` in firmware dirs matters**: Both `firmware-master/src/` and `firmware-slave/src/` exist but are empty — the real code is the `.ino` + `.cpp`/`.h` at directory root. Don't look for code in `src/`.
2. **LX-16A angle range**: 0-1000 maps to 0-240 degrees. `SERVO_ANGLE_MAX = 1000` in slave config.
3. **Disconnect safety**: Slave has a 300ms timeout state machine — if no data received, servos go to safe position (all 0 = open hand). Only triggers once per disconnect event (not per-frame).
4. **Fusion plugin units**: Fusion 360 Python API uses **cm**, not mm. `50mm = 5cm` in code. OpenSCAD files use mm.
5. **Fusion plugin queue**: `fusion-ai-assistant/queue/` is gitignored. Contains `pending_request.json` and `completed_response.json` at runtime.
6. **OpenSCAD rendering**: F5 = preview (fast), F6 = render (slow, for STL export). `$fn = 64` is the default quality.
7. **Finger model naming**: `b1_finger` = proximal phalanx, `b2_finger` = middle, `b3_finger` = distal. All parametric `.scad` files.
8. **LX-16A protocol**: Implemented directly in `firmware-slave/servo.cpp` — no third-party library. Frame: `[0x55][0x55][len][cmd][params...][checksum]`. Checksum = sum of bytes [2..8] & 0xFF.
9. **ESP-NOW wireless**: Uses ESP-NOW broadcast mode (not peer-to-peer). Master sends to `FF:FF:FF:FF:FF:FF`. Slave listens. Both print MAC address on startup for future peer configuration.
10. **Arduino 3.x API**: Callback signatures changed from earlier versions. `onSend` uses `wifi_tx_info_t*`, `onReceive` uses `esp_now_recv_info_t*`. See `wireless.cpp` for correct signatures.
11. **ADC calibration**: Flex sensor calibration values (`FLEX_RAW_FLAT`, `FLEX_RAW_BENT`) in `firmware-master/config.h` are placeholders — need per-sensor calibration when 5 sensors are connected.

## Communication Protocol (Quick Reference)

32 bytes, little-endian:

| Offset | Field | Type | Notes |
|--------|-------|------|-------|
| 0-9 | flex[5] | uint16 × 5 | Normalized 0-65535 |
| 10-25 | quat[4] | float × 4 | IMU quaternion w,x,y,z |
| 26-27 | seq | uint16 | Frame sequence number |
| 28-31 | reserved | uint8 × 4 | Unused |

## Safety Rules (Non-Negotiable)

- Battery must never short-circuit (fire/explosion risk)
- Servo stall time < 5 seconds (burns servo)
- Secure mechanical hand to desk during debug
- Check all wiring before every power-on
- Keep a fire extinguisher nearby
