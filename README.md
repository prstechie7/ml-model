# 🌾 Agribot Robotics & IoT Sensor Ecosystem (v2.0 PRO)

An end-to-end, field-grade autonomous robotics and precision agriculture IoT suite developed for the **ESP32 microcontroller** (MicroPython) and companion edge computing platforms (Raspberry Pi, NVIDIA Jetson, Linux/macOS).

This repository contains three clean, specialized subsystems:

| File | Subsystem | Platform | Primary Purpose |
| :--- | :--- | :--- | :--- |
| [`autonomous_robot.py`](./autonomous_robot.py) | **Robot Motion & Navigation** | ESP32 (MicroPython) | Dual BTS7960 (43A) motor drive, FS-i6X RC arcade mixing, HC-SR04 proportional braking, Wi-Fi web deck, and autonomous roaming. |
| [`sensor_telemetry.py`](./sensor_telemetry.py) | **Soil & Climate Telemetry** | ESP32 (MicroPython) | Triple soil moisture sensing, DHT11 climate tracking, 11dB ADC attenuation, and Google Sheets cloud logging with HTTP 302 redirect resolution. |
| [`camera_capture.py`](./camera_capture.py) | **Vision & Field Image Capture** | Edge Linux / SBC / PC | Stable V4L2 webcam capture, buffer flushing, OpenCV Laplacian blur detection, exposure auditing, and CSV metadata logging. |

---

## 📑 Table of Contents
- [1. Subsystem 1: Robot Motion & Navigation (`autonomous_robot.py`)](#1-subsystem-1-robot-motion--navigation)
  - [Key Architecture & Features](#key-architecture--features)
  - [Hardware Pinout & Connections](#hardware-pinout--connections)
  - [Operational Modes & Kinematics](#operational-modes--kinematics)
  - [Proportional Deceleration Math](#proportional-deceleration-math)
- [2. Subsystem 2: Soil & Climate Telemetry (`sensor_telemetry.py`)](#2-subsystem-2-soil--climate-telemetry)
  - [Critical Engineering Enhancements](#critical-engineering-enhancements)
  - [Wiring & ADC Configuration](#wiring--adc-configuration)
  - [Cloud Integration (Google Apps Script)](#cloud-integration-google-apps-script)
- [3. Subsystem 3: Vision & Field Image Capture (`camera_capture.py`)](#3-subsystem-3-vision--field-image-capture)
  - [Core Vision Capabilities](#core-vision-capabilities)
  - [Buffer Latency & Quality Metrics](#buffer-latency--quality-metrics)
  - [Directory & CSV Audit Schema](#directory--csv-audit-schema)
- [4. Deployment & Quick Start Guide](#4-deployment--quick-start-guide)
- [5. Failsafes & Field Reliability Summary](#5-failsafes--field-reliability-summary)

---

## 1. Subsystem 1: Robot Motion & Navigation
**File:** `autonomous_robot.py`

High-current robotic chassis locomotion system powered by dual **BTS7960 43A H-Bridge motor drivers**, designed to eliminate common hardware pitfalls like microcontroller brownout reboots, gear stripping, and sensor ghost echoes.

### Key Architecture & Features:
1. **Slew-Rate Acceleration Limiting (Soft-Start / Soft-Brake)**:
   - Linearly ramps motor PWM values up and down using a configurable slew-rate step (`RAMP_ACCEL_STEP = 15`).
   - Prevents massive inrush current spikes that cause battery voltage drops and unexpected ESP32 brownout resets.
2. **5-Sample Moving Median Filter**:
   - Rejects single-pulse ultrasonic echo glitches and acoustic reflections from uneven soil or weeds.
3. **Proportional Adaptive Braking**:
   - Replaces binary stop logic with smooth deceleration as obstacles approach.
   - **Crucial Rule:** `BACKWARD` (reverse drive) is **100% allowed at all times** to allow obstacle escape maneuvers.
4. **FlySky FS-i6X RC Arcade Mixing**:
   - Full differential steering mixing (throttle + steering combined) rather than discrete forward/spin commands.
5. **Built-in Glassmorphism Web Dashboard**:
   - Hosted directly on the ESP32 Access Point (`http://192.168.4.1`).
   - Responsive virtual touch D-pad, live telemetry badge (distance, mode, speed), speed slider, and full keyboard control (`W`, `A`, `S`, `D`, `Space`).

### Hardware Pinout & Connections

| Component | ESP32 Pin | Function / Wire |
| :--- | :--- | :--- |
| **Left BTS7960 Driver** | `GPIO 25` | `L_RPWM` (Forward PWM) |
| | `GPIO 26` | `L_LPWM` (Backward PWM) |
| **Right BTS7960 Driver** | `GPIO 27` | `R_RPWM` (Forward PWM) |
| | `GPIO 14` | `R_LPWM` (Backward PWM) |
| **HC-SR04 Ultrasonic** | `GPIO 32` | `TRIG` (Trigger Output) |
| | `GPIO 33` | `ECHO` (Echo Input) |
| **Mode Switch** | `GPIO 23` | Push Button to GND (Internal Pull-Up) |
| **FS-i6X Receiver** | `GPIO 18` | `CH1` (Steering / Aileron) |
| | `GPIO 19` | `CH2` (Throttle / Elevator) |
| | `GPIO 21` | `CH3` (Speed Limiter / Governor) |

### Operational Modes & Kinematics

```
┌──────────────────────────────────────────────────────────────┐
│                    MODE SELECTION ENGINE                     │
└──────────────────────────────────────────────────────────────┘
         │
         ├───► MODE 0: FS-i6X RC MANUAL
         │      • CH2 Throttle + CH1 Steering Arcade Mixing
         │      • CH3 Speed Governor Limiter (0 to 255 PWM)
         │      • Loss-of-Signal (LOS) Watchdog (>300ms cut-off)
         │
         ├───► MODE 1: WI-FI COMMAND DECK
         │      • AP SSID: "ROBOT_ESP32_PRO" (192.168.4.1)
         │      • Interactive Touch D-Pad & Keyboard (WASD)
         │      • Heartbeat Safety Timeout (>1000ms cut-off)
         │
         └───► MODE 2: AUTONOMOUS OBSTACLE ROAMING
                • State Machine: DRIVE ──► BACKOFF ──► PIVOT
                • Automatically reverses and pivots away when trapped
```

#### Proportional Deceleration Math:
$$\text{Speed Scalar} = 
\begin{cases} 
1.0 & \text{if } \text{Distance} > 60\text{ cm} \\
0.3 + 0.7 \times \left(\frac{\text{Distance} - 30}{60 - 30}\right) & \text{if } 30\text{ cm} < \text{Distance} \le 60\text{ cm} \\
0.0\ (\text{Blocked}) & \text{if } \text{Distance} \le 30\text{ cm}
\end{cases}$$

---

## 2. Subsystem 2: Soil & Climate Telemetry
**File:** `sensor_telemetry.py`

Field IoT environmental monitoring station collecting multi-depth soil moisture data and ambient temperature/humidity, forwarding live telemetry to Google Sheets.

### Critical Engineering Enhancements:
1. **11dB ADC Attenuation Configuration**:
   - On the ESP32, unconfigured ADC channels saturate at $\sim 1.1\text{V}$, causing standard 3.3V soil moisture sensors to read `4095` (dry) at all times.
   - The script explicitly configures `ADC.ATTN_11DB` on pins 34, 35, and 32 to utilize the full **$0\text{V} - 3.3\text{V}$ dynamic range**.
2. **Google Apps Script HTTP 302 Redirection Engine**:
   - Google Apps Script webhooks issue HTTP 302/307 redirects to `script.googleusercontent.com`.
   - Standard MicroPython `urequests` fails without following redirects. Built-in recursive header inspection guarantees payload delivery to the Google Sheet.
3. **DHT11 Timing & Noise Filter**:
   - Single-wire DHT11 sensors frequently throw `ETIMEDOUT` (Errno 110) in field humidity.
   - Implements a 3-attempt retry routine with microsecond pauses.
4. **Self-Healing WiFi Connection Watchdog**:
   - Reconnects automatically with exponential recovery without freezing or blocking telemetry cycles.

### Wiring & ADC Configuration

| Sensor | ESP32 Pin | Function | Notes |
| :--- | :--- | :--- | :--- |
| **Soil Probe 1** | `GPIO 34` | Analog Input (ADC1_CH6) | Configured with `ATTN_11DB` |
| **Soil Probe 2** | `GPIO 35` | Analog Input (ADC1_CH7) | Configured with `ATTN_11DB` |
| **Soil Probe 3** | `GPIO 32` | Analog Input (ADC1_CH4) | Configured with `ATTN_11DB` |
| **DHT11 Sensor** | `GPIO 4` | Digital Single-Wire | Temp (-20 to 60°C) & Humidity (20-90%) |

### Calibration & Mapping:
- **Dry Soil Value (`DRY_VALUE`)**: `4095` (Sensor suspended in open air)
- **Wet Soil Value (`WET_VALUE`)**: `1500` (Sensor submerged in water)
$$\text{Moisture \%} = \text{constrain}\left(\frac{\text{Raw} - \text{DRY}}{\text{WET} - \text{DRY}} \times 100,\ 0,\ 100\right)$$
- **Soil Status Tiers**:
  - `LOW` ($< 33\%$) $\rightarrow$ Irrigation required
  - `MEDIUM` ($33\% - 70\%$) $\rightarrow$ Optimal field moisture
  - `HIGH` ($> 70\%$) $\rightarrow$ Saturated / Overwatered

---

## 3. Subsystem 3: Vision & Field Image Capture
**File:** `camera_capture.py`

Edge computer vision capture and quality auditing system written in Python with OpenCV.

### Core Vision Capabilities:
1. **Multi-Platform Resilient Camera Discovery**:
   - **Primary:** Stable Linux V4L2 hardware path (`/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_Camera_SN0001-video-index0`).
   - **Secondary:** Fallback probe of standard numeric device indices (`0`, `1`, `2`).
   - **Development Fallback:** Synthetic agricultural test pattern generator so the pipeline can be tested on laptops without a webcam.
2. **Zero-Latency Buffer Flushing**:
   - Standard OpenCV maintains a 5-frame hardware queue. Taking a picture after `sleep(5)` saves a 5-second-old frame.
   - `flush_and_grab_fresh_frame()` empties the queue before capturing, ensuring real-time synchronized captures.
3. **Laplacian Blur & Exposure Validation**:
   - **Blur Metric**: Variance of the Laplacian filter ($\text{Var}(\nabla^2 I)$). Flags frames blurred by robot wheel vibration.
   - **Exposure Metric**: Grayscale histogram mean. Flags underexposed (night/shadow) or overexposed (sun-glare) shots.
4. **Storage Safety Watchdog**:
   - Continuously checks partition disk space.
   - Suspends writes if storage drops below **500 MB**, preventing SD card corruption.

### Directory & CSV Audit Schema:
Images are stored in `AgribotData/JPG/` and every capture is logged into `AgribotData/CSV/capture_log_YYYYMMDD.csv`:

```csv
timestamp,filename,resolution,blur_score,brightness,quality_status,file_size_kb
2026-10-13 19:15:02,Agribot_20261013_191502.jpg,1280x720,142.30,118.40,OPTIMAL,84.2
2026-10-13 19:15:07,Agribot_20261013_191507.jpg,1280x720,41.20,115.10,BLURRED,78.5
```

---

## 4. Deployment & Quick Start Guide

### Deploying Subsystems to ESP32 (MicroPython):
1. **Flash MicroPython Firmware** to your ESP32:
   ```bash
   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-firmware.bin
   ```
2. **Upload Files** using Thonny IDE or `mpremote`:
   ```bash
   # Upload robot firmware
   mpremote cp autonomous_robot.py :main.py

   # OR upload sensor firmware
   mpremote cp sensor_telemetry.py :main.py
   ```

### Running the Inspection Camera on Edge Host (Pi / Jetson / PC):
```bash
# Install dependencies
pip install opencv-python numpy

# Launch camera pipeline
python3 camera_capture.py
```

---

## 5. Failsafes & Field Reliability Summary

| Hazard / Field Condition | System Defense Mechanism |
| :--- | :--- |
| **High inrush motor current / Voltage drop** | Slew-rate PWM ramping prevents battery dip below ESP32 3.0V brownout threshold. |
| **RC Transmitter out of range / switched off** | LOS Watchdog halts all motors within 300 ms. |
| **Wi-Fi Web client disconnection** | Web watchdog halts all motors if no command heartbeat received in 1000 ms. |
| **Obstacle right in front of robot** | Proportional slowdown above 30 cm, total forward cutoff $\le 30$ cm. Reverse always permitted. |
| **Ultrasonic false echo reflections** | 5-sample moving median filter discards single-cycle outlier spikes. |
| **Google Apps Script HTTP 302 Redirect** | Custom redirect resolver automatically follows target endpoint to record data. |
| **ESP32 ADC saturation (Moisture stuck at 4095)** | Explicit `ADC.ATTN_11DB` attenuation expands ADC reference to $3.3\text{V}$. |
| **OpenCV stale image buffer** | Triple queue flush ensures images saved match the exact moment of capture. |
| **Robot vibration causing blurry pictures** | Laplacian variance metric flags motion-blurred images directly in telemetry CSV. |
| **SD card filling up during long field runs** | Storage watchdog pauses capture when free space drops below 500 MB. |

---

### 📄 License & Attribution
Designed and maintained for precision agricultural robotics, computer vision research, and autonomous field systems. Open for academic, competition, and commercial adaptation.
