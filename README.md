# 📦 GuardBox — Secure, Smart & Convenient Package Delivery

GuardBox is an IoT smart delivery box that protects packages during the vulnerable window between drop-off and pickup. It combines a physical secure enclosure with electronic monitoring, automatic locking, RFID/remote authentication, and real-time alerts. A built-in **AI chatbot** lets you query the box's live status by voice or text.

![Platform](https://img.shields.io/badge/Platform-ESP32%20%2B%20Firebase-orange)
![Firmware](https://img.shields.io/badge/Firmware-C%2B%2B%20(Arduino)-00599C?logo=arduino&logoColor=white)
![Apps](https://img.shields.io/badge/Apps-Android%20%7C%20Web%20%7C%20Desktop-blue)
![Chatbot](https://img.shields.io/badge/Chatbot-PyTorch%20%2B%20NLTK-EE4C2C?logo=pytorch&logoColor=white)
![Cloud](https://img.shields.io/badge/Cloud-Firebase%20RTDB-FFCA28?logo=firebase&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green)

---
<p align="center">
  <img width="600" height="800" alt="1747146211644" src="https://github.com/user-attachments/assets/cae55c41-3567-4ead-8705-b7911d757bda" />
  <img width="600" height="800" alt="1747145874546" src="https://github.com/user-attachments/assets/d813bc3a-99f0-455e-ac13-c12d7196f69d" />
</p>

## 🚨 Security Notice (read this first)

The original sources contained **hardcoded credentials**. They have been replaced with placeholders / environment variables in this repository, but if the secrets were ever committed or shared, you must still:

1. **Revoke the OpenAI API key** that was in `intentsgenerator.py` (it began with `sk-proj-…`). Treat it as compromised.
2. **Revoke / rotate the Firebase credentials** that were in the Python sources.
3. **Scrub them from git history** if they were pushed — deleting a file in a new commit is not enough (use `git filter-repo` or BFG Repo-Cleaner).
4. Lock down your **Firebase Security Rules** so the database isn't world-readable/writable.

All credentials are now read from environment variables. Copy `.env.example` to `.env`, fill in your values, and keep `.env` untracked (it is already in `.gitignore`).

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Hardware](#-hardware)
- [Firebase Data Model](#-firebase-data-model)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [How It Works](#-how-it-works)
- [Team](#-team)
- [License](#-license)

---

## 🔍 Overview

Package theft ("porch piracy") is a large and growing problem. GuardBox addresses the "last yard" of delivery: once a courier drops a parcel, it sits exposed until the recipient retrieves it. GuardBox closes that gap with a connected, lockable box that:

- detects when a package is placed (weight sensor),
- automatically locks itself,
- watches for tampering (vibration sensor),
- pushes real-time status and alerts to the cloud, and
- only opens for authorized users (RFID card or remote app command).

Status is mirrored across an Android app, a web dashboard, and a desktop app — all synchronized through Firebase Realtime Database. The desktop app additionally embeds an AI chatbot that answers questions like *"is the box locked?"* or *"how many deliveries?"* using the live database values.

---

## ✨ Features

**Smart locking** — a servo-driven lock engages automatically when a package is detected and the door is closed; it only releases for an authorized RFID card or a remote unlock command.

**Real-time monitoring** — a load cell (via HX711) confirms package presence; a vibration sensor flags tampering and escalates to a critical alert after repeated triggers.

**Multi-platform control** — Android (Kotlin/MVVM), web (HTML/Tailwind/JS), and desktop (Python/KivyMD) clients all share one live state through Firebase.

**Visual & system feedback** — red/green LEDs on the device, plus in-app and OS-level desktop notifications for package, lock, unlock, and vibration events.

**AI chatbot** — a PyTorch intent classifier (bag-of-words + NLTK) maps natural-language questions to actions and reads live values straight from Firebase. Works in **voice mode** (speech recognition + text-to-speech) or **text mode**, and is embedded in the desktop app behind a "Chatbot" button.

---

## 🏗 System Architecture

```
                         ┌─────────────────────────────┐
                         │    Firebase Realtime DB      │
                         │  /guardbox  /guardbox_stats  │
                         └────────────┬─────────────────┘
              push/pull state         │       listen / command
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
 ┌───────┴────────┐          ┌────────┴────────┐          ┌────────┴────────┐
 │  ESP32 device  │          │  Client apps    │          │  AI Chatbot     │
 │  (firmware)    │          │  Android / Web  │          │  voice + text   │
 │  sensors+lock  │          │  / Desktop      │          │  (PyTorch+NLTK) │
 └────────────────┘          └─────────────────┘          └─────────────────┘
```

Three logical layers:

1. **Physical layer** — enclosure, servo lock, load cell, vibration sensor, RFID, LEDs, button.
2. **Control layer** — ESP32 firmware running a state machine (Idle → Package Detected → Locked → Authenticating → Unlocked → Alert).
3. **Connectivity layer** — Firebase for real-time sync, notifications, and remote commands.

---

## Flowchart
<img width="1706" height="1391" alt="flowchart2" src="https://github.com/user-attachments/assets/fd082a77-cdc9-467a-a1aa-83fb0ddbda63" />

## 🧰 Tech Stack

| Area | Technologies |
| --- | --- |
| Microcontroller / Firmware | ESP32, C++ (Arduino IDE), `Firebase_ESP_Client`, `HX711`, `ESP32Servo`, `MFRC522` |
| Cloud | Firebase Realtime Database, Firebase Auth |
| Android app | Kotlin, Android Studio, MVVM, LiveData, Material Design, Firebase SDK |
| Web app | HTML5, Tailwind CSS, JavaScript, Feather Icons |
| Desktop app | Python, KivyMD, Plyer (notifications), Pyrebase |
| Chatbot | Python, PyTorch, NLTK, NumPy, SpeechRecognition, pyttsx3, Pyrebase, OpenAI (data generation) |

---

## 📂 Repository Structure

```
GuardBox/
├── README.md
├── .env.example                # Template for credentials (copy to .env)
├── .gitignore
├── firmware/
│   └── esp32/
│       └── guardbox_esp32.ino   # ESP32 firmware (sensors, lock, RFID, cloud sync)
├── chatbot/                     # AI assistant (importable + runnable)
│   ├── chatbot.py               # Inference module: exposes get_response() (import-safe)
│   ├── train.py                 # Train the model -> chatbot_model.pth
│   ├── run_chatbot.py           # Interactive voice/text loop
│   ├── model.py                 # NeuralNet architecture (shared)
│   ├── nltk_utils.py            # tokenize / stem / bag_of_words helpers
│   ├── firebase_config.py       # Reads Firebase config from env vars
│   ├── intentsgenerator.py      # (optional) paraphrase patterns via OpenAI
│   ├── intents.json             # Intents: tags, patterns, responses
│   ├── chatbot_model.pth        # Pre-trained PyTorch model
│   ├── chatbot.ipynb            # Legacy all-in-one notebook
│   └── requirements.txt
├── desktop-app/                 # KivyMD desktop app (embeds the chatbot)
│   ├── guardbox.py              # Imports get_response from ../chatbot
│   ├── *.png                    # UI icons (box / locked / unlocked / alert, light + dark)
│   └── requirements.txt
├── web-app/
│   └── index.html               # Browser dashboard (Tailwind + Feather Icons)
└── mobile-app/
    └── MainActivity.kt          # Android main activity (Kotlin / MVVM)
```

> **Chatbot ↔ desktop integration:** the desktop app (`desktop-app/guardbox.py`) adds the
> `chatbot/` folder to `sys.path` and imports `get_response` from it. `chatbot.py` is
> import-safe — importing it only loads the trained model, it does **not** start training
> or the voice loop — so the desktop app launches normally. Run the desktop app from inside
> `desktop-app/` so the icon files resolve correctly.

---

## 🔩 Hardware

| Component | Specification |
| --- | --- |
| ESP32 Dev Board | WiFi + Bluetooth SoC |
| HX711 | Load cell amplifier module |
| Load Cell | 20 kg aluminum strain gauge |
| Servo Motor | SG90 / MG996R (box-size dependent) |
| RFID Reader | MFRC522 module |
| RFID Card | 13.56 MHz MIFARE |
| Vibration Sensor | Spring-based module |
| LEDs + Resistors | Status indicators |
| Enclosure | Powder-coated steel box |
| Power Supply | 5V battery pack or adapter |
| Misc. | Wiring, PCB, fasteners |

The ESP32 reads the HX711 (DT/SCK), the MFRC522 over SPI, the vibration sensor and door button on GPIO, and drives the servo (PWM) plus the red/green LEDs.

---

## 🔥 Firebase Data Model

GuardBox uses a simple, flat structure for low-latency sync:

```jsonc
{
  "guardbox": {
    "locked": false,        // boolean lock state
    "weight": 0,            // grams from the load cell
    "vibration": false,     // tamper flag
    "event": "Box empty"    // last event string (used for notifications)
  },
  "guardbox_stats": {
    "deliveries": 10,       // total deliveries
    "locked": 5,            // number of lock events
    "vibrations": 1         // number of vibration events
  }
}
```

The `guardbox` node carries live device state; `guardbox_stats` holds the aggregate counters the chatbot reads for questions like *"how many deliveries?"*.

---

## 🚀 Getting Started

First, copy `.env.example` to `.env` and fill in your Firebase (and optionally OpenAI) credentials. See [Configuration](#-configuration).

### 1. ESP32 Firmware

**Requirements:** Arduino IDE with the ESP32 board package, plus libraries: `HX711`, `ESP32Servo`, `MFRC522`, `Firebase_ESP_Client`.

1. Open `firmware/esp32/guardbox_esp32.ino` in the Arduino IDE.
2. Fill in your WiFi and Firebase credentials (`WIFI_SSID`, `WIFI_PASSWORD`, `API_KEY`, `DATABASE_URL`, `USER_EMAIL`, `USER_PASSWORD`) — ideally from a separate, untracked `secrets.h`.
3. Verify the pin definitions for the load cell, servo, RFID, LEDs, button, and vibration sensor against your wiring.
4. Add your authorized RFID UIDs to the `authorizedUIDs` array.
5. Select your ESP32 board and port, then upload.

The firmware auto-locks when weight is detected and the door is closed, unlocks on an authorized card or a remote `/guardbox/locked` change, and writes weight/lock/vibration/event values back to Firebase.

### 2. AI Chatbot

**Requirements:** Python 3.x. Voice mode also needs a microphone (PortAudio + PyAudio).

```bash
cd chatbot
pip install -r requirements.txt
# For voice input you may also need PortAudio + PyAudio:
#   Debian/Ubuntu: sudo apt-get install portaudio19-dev && pip install pyaudio
#   macOS:         brew install portaudio && pip install pyaudio
#   Windows:       pip install pyaudio
```

Chat interactively (uses the pre-trained `chatbot_model.pth`):

```bash
python run_chatbot.py
```

Set `VOICE_MODE` at the top of `run_chatbot.py` (`True` = speak/listen, `False` = type). Say or type `quit`/`bye` to exit.

Re-train the model from `intents.json` (rebuilds `chatbot_model.pth`):

```bash
python train.py
```

**Optional — generate more training patterns:** `intentsgenerator.py` uses the OpenAI API to paraphrase queries. It reads `OPENAI_API_KEY` from the environment — do not hardcode it.

Example interaction:

```
You: number of deliveries
Bot: There have been 10 package deliveries.
```

### 3. Desktop App

**Requirements:** Python 3.x.

```bash
cd desktop-app
pip install -r requirements.txt
python guardbox.py   # run from this folder so the icons load
```
<img width="987" height="622" alt="app2" src="https://github.com/user-attachments/assets/39e7d110-7fb2-418f-a027-6bc2bf07ca5e" />

The desktop app shows box status, lock control, and a notifications panel, and includes a **Chatbot** button. It imports `get_response` from the sibling `chatbot/` folder, so keep both folders in place.

### 4. Web App

No build step required.

```bash

cd web-app
# open index.html directly, or serve it:
python -m http.server 8000
# visit http://localhost:8000
```

> **Note:** the web and mobile apps have minor gaps
> (e.g. live Firebase wiring on the web side, and the full Android Studio project around
> `MainActivity.kt`). They are functional starting points and open to further development.
<img width="1280" height="731" alt="1747142366207" src="https://github.com/user-attachments/assets/fe53d33b-5676-45d7-9852-91fa78640ec3" />

### 5. Android App

**Requirements:** Android Studio, JDK, an Android device/emulator.

`mobile-app/MainActivity.kt` is the main activity. Drop it into an Android Studio project (MVVM + Firebase) with the usual supporting classes, resources and your `google-services.json`, then build and run.
<img width="322" height="642" alt="mobile " src="https://github.com/user-attachments/assets/dc497042-8f95-4155-863f-c187d0a66a49" />

## ⚙️ Configuration

All Python credentials are read from environment variables. Copy the template and fill it in:

```bash
cp .env.example .env
```

`.env` contents:

```env
# Firebase
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your_project-default-rtdb.firebasedatabase.app
FIREBASE_PROJECT_ID=your_project
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=000000000000
FIREBASE_APP_ID=1:000000000000:web:xxxxxxxxxxxx

# OpenAI (only for intentsgenerator.py)
OPENAI_API_KEY=sk-...

# ESP32 (keep in an untracked secrets.h, not in source)
WIFI_SSID=your_wifi
WIFI_PASSWORD=your_wifi_password
```

`chatbot/firebase_config.py` loads these (via `python-dotenv` if installed) and exposes a shared `get_db()` handle used by both the chatbot and the desktop app. `.env`, `secrets.h`, and `google-services.json` are all gitignored.

---

## 🔄 How It Works

1. A courier places a package; the load cell registers a weight increase.
2. When the door closes, the ESP32 engages the servo lock, lights the red LED, and writes `locked: true` to Firebase.
3. All clients update instantly; a notification logs the lock event.
4. The vibration sensor monitors for tampering and raises an alert (escalating to a critical alert on repeated hits).
5. The recipient unlocks remotely from any app, or with an authorized RFID card; the box opens and the event is recorded.
6. At any time, ask the chatbot — *"is the box locked?"*, *"how heavy is the package?"*, *"how many deliveries?"* — and it answers from the live Firebase values.

---

## 👥 Team

Maltepe University — Faculty of Engineering and Natural Sciences.

- Zihni AKIN
- Enes İŞBİLEN
- Arda ŞİMŞEK
- Furkan AKSOY
- Can ÖZEL

---

## 📄 License

Released under the MIT License. See the [`LICENSE`](LICENSE) file for details.
