# 🌾 Agribot Autonomous Robotics & AI Ecosystem (v2.0 PRO)

An end-to-end, industrial-grade precision agriculture robotics suite developed for **ESP32 microcontrollers** (MicroPython) and companion edge computers (Raspberry Pi, NVIDIA Jetson, Linux SBC, and Workstations).

---

## 📂 Repository File Structure

```text
ml-model/
├── autonomous_robot.py          # Dual BTS7960 43A motor drive, RC mixing & obstacle avoidance
├── sensor_telemetry.py          # 3-Depth soil moisture, DHT11 & Google Sheets HTTP 302 telemetry
├── camera_capture.py            # Stable V4L2 zero-latency frame capture & blur/exposure audit
├── edge_ai_inference.py         # On-Device YOLO11n Pest Net & MobileNetV2 Disease Classifier
├── gps_waypoint_navigator.py    # NEO-M8N GNSS NMEA parser, Haversine swath grid & Geofencing
├── precision_sprayer.py         # 12V diaphragm pump/solenoid spot-sprayer & dry-run watchdog
├── power_solar_monitor.py       # INA219 I2C 3S Li-ion battery health & solar harvest manager
├── gsm_emergency_dispatcher.py  # SIM800L / A9G cellular SOS dialing & GPS SMS dispatch
├── drone_mesh_bridge.py         # MQTT / WebSocket aerial scouting & dynamic route injector
├── ai_voice_caller.py           # LiveKit SIP + Vertex AI/OpenAI bilingual (Hindi/English) voice agent
└── README.md                    # Comprehensive system documentation & wiring schemas
```

---

## 🎙️ AI Voice Calling Framework & API Requirements

### Architecture:
- **Telephony & Real-Time Audio Transport**: LiveKit Agents WebRTC + SIP Outbound Trunking (Twilio/Telnyx).
- **Voice Activity Detection (VAD)**: Silero VAD (local sub-10ms latency).
- **Speech-to-Text (STT)**: Deepgram Nova-2 / Google Cloud Speech-to-Text (Hindi `hi-IN` & English `en-IN`).
- **LLM Reasoning**: Google Cloud Vertex AI (Gemini 1.5/2.0 Flash) / OpenAI (`gpt-4o-mini`) / Groq.
- **Text-to-Speech (TTS)**: ElevenLabs Multilingual v2 / Google Cloud TTS Neural2 (`hi-IN-Neural2-A`).

### Environment Variables (`.env`):
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_SIP_TRUNK_ID=ST_xxxxxxxxx

# Google Cloud Vertex AI / Alternative LLM
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
GCP_PROJECT_ID=your-project
OPENAI_API_KEY=sk-xxxx
GROQ_API_KEY=gsk_xxxx

# Audio AI APIs
DEEPGRAM_API_KEY=xxxxxx
ELEVENLABS_API_KEY=xxxxxx
```

### Incident Voice Dispatch Matrix:
```python
INCIDENT_TEMPLATES = {
    "ROVER_STUCK": {
        "title": "Rover Blockage Alert",
        "voice_en": "Alert! Your AgriBot rover is physically stuck in muddy terrain at sector B2. Please inspect the rover.",
        "voice_hi": "चेतावनी! आपका एग्रीबॉट रोवर खेत में फंस गया है। कृपया जीपीएस लोकेशन पर जाकर रोवर की जांच करें।",
        "sms_prefix": "🚨 AGRIBOT CRITICAL: Rover is trapped/stuck at field coordinates."
    },
    "CRITICAL_BATTERY": {
        "title": "Low Battery Brownout Risk",
        "voice_en": "Warning. AgriBot battery has dropped below fifteen percent. Safe parking sequence initiated.",
        "voice_hi": "चेतावनी! रोवर की बैटरी पंद्रह प्रतिशत से कम हो गई है। कृपया तुरंत चार्ज करें।",
        "sms_prefix": "⚠️ AGRIBOT WARNING: Battery critically low (<15%)."
    },
    "SEVERE_PEST_OUTBREAK": {
        "title": "High-Risk Pest Outbreak",
        "voice_en": "Urgent agronomy advisory. Tobacco caterpillar infestation detected above ninety percent threshold.",
        "voice_hi": "कृषि सूचना! आपके खेत में तम्बाकू इल्ली का गंभीर प्रकोप देखा गया है। तुरंत स्प्रे की सलाह दी जाती है।",
        "sms_prefix": "🐛 AGRIBOT AI: Severe pest cluster detected (>90% confidence)."
    },
    "SOIL_DROUGHT_CRITICAL": {
        "title": "Extreme Soil Moisture Depletion",
        "voice_en": "Alert. Soil moisture at root depth has dropped to critical drought levels. Immediate irrigation required.",
        "voice_hi": "चेतावनी! मिट्टी में नमी बहुत कम हो गई है। तुरंत सिंचाई शुरू करने की आवश्यकता है।",
        "sms_prefix": "💧 AGRIBOT TELEMETRY: Soil moisture critical (<18%)."
    }
}
```

---

## ⚡ Complete Module Breakdown & Functioning

### 1. `autonomous_robot.py` (Chassis Locomotion & Safety)
* **Hardware:** ESP32 + 2x BTS7960 (43A H-Bridge) + 4 DC Geared Motors + HC-SR04 Ultrasonic + FS-i6X RC.
* **Slew-Rate Acceleration Limiting:** Linearly ramps motor PWM values up and down using a configurable slew-rate step (`RAMP_ACCEL_STEP = 15`). Eliminates inrush current spikes that cause battery voltage drops and ESP32 brownout reboots.
* **3-Zone Proportional Braking:**
  - $> 60\text{ cm}$: 100% full speed allowed.
  - $30\text{ cm} - 60\text{ cm}$: Smooth linear deceleration.
  - $\le 30\text{ cm}$: Forward motion prohibited. `BACKWARD` reverse drive is **always 100% permitted** to allow escape maneuvers.
* **5-Sample Median Filter:** Rejects rogue ultrasonic echo reflections and false distance drops.
* **Arcade Drive Kinematics:** Full differential steering mixing on FlySky FS-i6X channels.
* **Glassmorphism Web Dashboard:** Mobile-responsive control deck at `http://192.168.4.1`.

### 2. `sensor_telemetry.py` (Soil & Climate Telemetry)
* **Hardware:** ESP32 + 3x Capacitive Soil Moisture Sensors + DHT11 (Temp & Humidity).
* **11dB ADC Attenuation:** Configures `ADC.ATTN_11DB` on pins 34, 35, and 32 to read the full $0 - 3.3\text{V}$ dynamic range, preventing sensors from getting stuck at 4095.
* **Google Apps Script 302 Redirect Resolver:** Automatically follows HTTP 301/302/307 redirects to `script.googleusercontent.com` to guarantee reliable logging in Google Sheets.
* **Self-Healing WiFi Watchdog:** Auto-reconnects with exponential backoff if connectivity drops.

### 3. `camera_capture.py` (Real-Time Vision & Field Capture)
* **Hardware:** USB Webcam / V4L2 Sensor on Raspberry Pi / Jetson / PC.
* **Multi-Platform Auto-Discovery:** Prioritizes Linux hardware by-id path (`/dev/v4l/by-id/...`), falls back to numeric indices (`0`, `1`), and includes a synthetic pattern generator.
* **Zero-Latency Buffer Flushing:** Flushes OpenCV's 5-frame internal hardware queue before snapshots, guaranteeing fresh real-time frames instead of stale buffered images.
* **Quality & Blur Evaluation:** Computes Laplacian variance ($\text{Var}(\nabla^2 I)$) and luminance histograms to flag bad frames.
* **Audit Logging:** Automatically writes metadata to `AgribotData/CSV/capture_log_YYYYMMDD.csv`.

### 4. `edge_ai_inference.py` (On-Device Vision Diagnostic)
* **Models:** YOLO11n Pest Net (ONNX) + MobileNetV2 Disease Classifier.
* **YOLO11n Pest Detection:** Real-time bounding-box detection for aphids, caterpillars, armyworms, beetles, and spider mites.
* **MobileNetV2 Disease Classifier:** Diagnoses leaf blights, powdery mildew, and chlorosis in under 20ms.
* **Output Pipeline:** Generates annotated bounding-box frames in `AgribotData/AI_Inspections/` and appends diagnostic labels to `ai_diagnostic_audit.csv`.

### 5. `gps_waypoint_navigator.py` (Autonomous GIS Swath Navigation)
* **Hardware:** u-blox NEO-M8N GNSS Module over UART Serial.
* **NMEA Sentence Parser:** Decodes `$GPGGA` and `$GPRMC` sentences with satellite count and fix verification.
* **Haversine & Swath Tracking:** Computes forward bearing and distance to guide the rover along sequential lawnmower grid waypoints.
* **Geofence Boundary Guard:** Ray-casting point-in-polygon algorithm immediately halts the rover if it crosses the designated field boundary.

### 6. `precision_sprayer.py` (Targeted Chemical / Water Actuator)
* **Hardware:** 12V Diaphragm Pump + Solenoid Valve via MOSFET/Relay + Fluid Level Float Switch.
* **Targeted Spot-Spraying:** Triggers nozzle bursts exclusively when `edge_ai_inference.py` flags an infected crop, eliminating 40%+ chemical waste.
* **Speed-Compensated Dosage:** Dynamically calculates spray pulse duration (seconds) based on calibrated nozzle flow rate (ml/s) and vehicle travel speed.
* **Dry-Run Watchdog:** Auto-aborts spraying if the reservoir float switch detects an empty tank.

### 7. `power_solar_monitor.py` (Battery Health & Solar Harvest Manager)
* **Hardware:** INA219 I2C Current/Voltage Sensor + 3S Li-ion Battery Pack (11.1V/12.6V) + 18V Solar Panel.
* **State of Charge (SoC %):** Computes real-time battery percentage using a non-linear Lithium-ion discharge curve.
* **Return-to-Base (RTB) Failsafe:** Flags autonomous return-to-base when battery drops below 15% and commands emergency shutdown below 5%.

### 8. `gsm_emergency_dispatcher.py` (Cellular SOS & Emergency Dispatch)
* **Hardware:** SIM800L / A9G Cellular Modem over UART Serial AT Commands.
* **Instant SOS SMS:** Sends real-time GPS coordinates and a clickable Google Maps link when the rover gets stuck in mud or triggers a critical low-voltage brownout.
* **Automated Voice Dialer:** Calls the farmer's mobile number during critical threshold breaches.

### 9. `drone_mesh_bridge.py` (Aerial-to-Ground Scouting Coordinator)
* **Protocol:** MQTT / WebSocket Multi-Agent Coordinator.
* **Aerial Outlier Ingestion:** Listens to drone survey topics and parses coordinates of stressed crop patches identified by aerial multispectral NDVI imaging.
* **Dynamic Route Injection:** Automatically inserts the drone's flagged hotspot coordinates at the head of `gps_waypoint_navigator.py`'s waypoint queue.

### 10. `ai_voice_caller.py` (Real-Time Bilingual AI Voice Dispatch)
* **Telephony Protocol:** LiveKit SIP Outbound Dialing + VoicePipelineAgent.
* **Bilingual Dialogue:** Speaks to farmers in conversational **Hindi** or **English**, explains the rover blockage or pest outbreak, gives coordinates, answers agronomy questions, and delivers an instant SMS backup.

---

## 🛠️ Quick Deployment Guide

```bash
# Install voice & edge AI packages
pip install livekit livekit-agents livekit-plugins-openai livekit-plugins-silero livekit-plugins-deepgram opencv-python onnxruntime

# Trigger an immediate outbound emergency AI voice call
python3 ai_voice_caller.py +918319556016 SEVERE_PEST_OUTBREAK hi
```
