# GuardBox
 Secure, Smart, and Convenient Package Delivery

# GuardBox – AI-Powered IoT Package Security System

GuardBox is a secure, AI-integrated IoT solution designed to protect unattended package deliveries. It combines smart hardware with cloud-based data syncing and cross-platform apps to provide a seamless user experience for monitoring, controlling, and receiving alerts about your delivery box — in real-time.

## 🔐 Key Features

- **Smart Locking Mechanism**
  - Lock and unlock using **RFID** tags or remotely via **mobile app** or **desktop interface**.
  
- **Package Detection**
  - Integrated **load cell (HX711)** detects package placement or removal based on weight changes.

- **Tamper Detection**
  - A **vibration sensor** identifies motion or tampering attempts and sends immediate alerts.

- **AI-Powered Chatbot**
  - Built with **PyTorch**, the chatbot can answer questions like:
    - “Is the box locked?”
    - “Has there been any vibration?”
    - “Is there a package inside?”

- **Realtime Firebase Sync**
  - Centralized cloud backend using **Firebase Realtime Database** ensures consistent state across all apps.

- **Cross-Platform Interfaces**
  - **Mobile App**: Built with **Kotlin** (Android), supports remote control and live alerts.
  - **Desktop App**: Developed in **Python + KivyMD**, features a visual control panel.
  - **Web App**: Built with **TailwindCSS**, offers a responsive, admin-friendly interface with dark/light theme toggle.

## 📦 Technologies Used

- **Hardware**: ESP32, MFRC522 RFID Module, HX711 Load Cell, Servo Motor, Vibration Sensor
- **Cloud**: Firebase Realtime Database, Pyrebase
- **AI**: PyTorch, NLTK
- **Software**: Python, Kotlin (Android), TailwindCSS, KivyMD, Feather Icons, JSON-based intent system

## 🚀 Getting Started

### Prerequisites

- Arduino IDE (for ESP32 code)
- Python 3.x with `pip` installed
- Android Studio (for mobile app)
- Firebase project with RTDB set up

### Python Dependencies

```bash
pip install torch nltk pyrebase4 kivymd
