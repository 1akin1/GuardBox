<div align="center">

# 🔒 GuardBox

### Secure, Smart, and Convenient Package Delivery

An IoT system that protects packages during the vulnerable window between delivery and pickup — combining a physical smart lock, real-time sensors, and cross-platform monitoring apps.

</div>

---

## Overview

GuardBox is a smart, secure package-delivery box built around an **ESP32** microcontroller and a **Firebase Realtime Database** backend. When a courier places a package inside, a weight sensor confirms delivery and the box automatically locks. The owner can monitor and control the box in real time from a **mobile**, **web**, or **desktop** app, gets instant alerts on tampering (vibration), and can unlock the box remotely or with an authorized RFID card. A natural-language **chatbot** lets users query box status by text or voice.

```
Courier places package  ──▶  Weight sensor detects it  ──▶  Box auto-locks (servo)
                                                                   │
       RFID card / remote unlock  ◀──  Owner monitors & controls   │
                                                                   ▼
            Mobile · Web · Desktop apps  ◀── Firebase Realtime DB ──┘
```

## Repository Structure

| Folder | Description | Stack |
| --- | --- | --- |
| [`firmware/esp32/`](firmware/esp32) | ESP32 firmware controlling sensors, lock, RFID and cloud sync | C++ / Arduino |
| [`chatbot/`](chatbot) | NLP chatbot (text + voice) that answers questions about box status | Python · PyTorch · NLTK |
| [`desktop-app/`](desktop-app) | Desktop monitoring & control app with built-in chatbot | Python · KivyMD |
| [`web-app/`](web-app) | Browser dashboard for status, lock control and notifications | HTML · Tailwind CSS · JS |
| [`mobile-app/`](mobile-app) | Native Android app for on-the-go control | Kotlin · Android |

## System Architecture

GuardBox is organized in three layers:

1. **Physical layer** — the metal enclosure, servo-driven lock, and sensor array (load cell, vibration sensor, door switch, LEDs).
2. **Control layer** — the ESP32, running a state machine that reads sensors, manages authentication, and drives the lock.
3. **Connectivity layer** — Firebase Realtime Database, which synchronizes state across all client apps in real time.

All clients read and write a single `guardbox` node:

```json
{
  "guardbox": {
    "locked": false,
    "weight": 0,
    "vibration": false,
    "event": "Box empty - not locked"
  }
}
```

## Hardware

| Component | Role |
| --- | --- |
| ESP32 Dev Board | Main controller, WiFi + Bluetooth |
| HX711 + 20 kg load cell | Package detection (weight) |
| MFRC522 RFID reader + card | Authorized access |
| SG90 / MG996R servo motor | Locking mechanism |
| Spring vibration sensor | Tamper detection |
| Red / Green LEDs | Lock-status indication |
| Push button | Door-closed switch |
| Powder-coated steel box | Enclosure |

## Getting Started

> **Security note:** All credentials in this repo (WiFi, Firebase API keys, OpenAI key) are placeholders such as `YOUR_FIREBASE_API_KEY`. Fill in your own values locally and **never commit real secrets**. A `.gitignore` is included to help keep config files out of version control.

### 1. Firmware (ESP32)

1. Open [`firmware/esp32/guardbox_esp32.ino`](firmware/esp32/guardbox_esp32.ino) in the Arduino IDE.
2. Install the libraries: `HX711`, `ESP32Servo`, `MFRC522`, `Firebase ESP Client` (by mobizt), and the ESP32 board package.
3. Fill in your WiFi and Firebase credentials at the top of the file, and verify the GPIO pin assignments against your wiring.
4. Add your authorized RFID card UIDs to the `authorizedUIDs[][4]` array.
5. Select your ESP32 board and upload.

### 2. Chatbot (Python)

```bash
cd chatbot
pip install -r requirements.txt
# Add your Firebase config in chatbot.py, then:
python chatbot.py
```

Set `voice_mode = False` inside `chatbot.py` for text-only mode. `chatbot_model.pth` is a pre-trained model; the script also retrains on startup using `intents.json`.

### 3. Desktop App (Python · KivyMD)

```bash
cd desktop-app
pip install -r requirements.txt
# Add your Firebase config in guardbox.py, then:
python guardbox.py
```

The image assets (`box.png`, `locked.png`, etc.) must stay alongside `guardbox.py`.

### 4. Web App

Open [`web-app/index.html`](web-app/index.html) in a browser, or serve it locally:

```bash
cd web-app
python -m http.server 8000
# visit http://localhost:8000
```

To enable live data, wire the UI actions to your Firebase Realtime Database (Tailwind and Feather Icons load from CDN).

### 5. Mobile App (Android · Kotlin)

[`mobile-app/MainActivity.kt`](mobile-app/MainActivity.kt) is the main activity from the Android Studio project. To build a full app, place it in an Android project with the supporting `LoginActivity`, `HistoryActivity`, `SettingsActivity`, model classes (`User`, `GuardBoxStatus`, `ActivityLog`), the `FirebaseHelper` utility, adapters, layouts, and a `google-services.json` from your Firebase project.

## Core Features

- **Smart lock** — auto-locks when a package is detected and the door closes; unlock via RFID or any app.
- **Real-time tracking** — weight and vibration sensors report status to all clients instantly.
- **Tamper alerts** — repeated vibrations escalate to a critical alert.
- **Remote access** — monitor and unlock from anywhere through Firebase.
- **Cross-platform** — mobile, web, and desktop clients stay in sync.
- **Chatbot** — ask "Is the box locked?" or "Any package?" by text or voice.

## Tech Stack

`ESP32 / Arduino (C++)` · `Firebase Realtime Database` · `Python` · `PyTorch` · `NLTK` · `KivyMD` · `Kotlin / Android` · `HTML` · `Tailwind CSS` · `JavaScript`

## Team

Maltepe University — Faculty of Engineering and Natural Sciences
Special Topics in Computer Engineering (CEN 309)

- Enes İŞBİLEN
- Arda ŞİMŞEK
- Zihni AKIN
- Furkan AKSOY
- Can ÖZEL

## License

No license file is included yet. Add one (e.g. MIT) if you intend to make this project open source.
