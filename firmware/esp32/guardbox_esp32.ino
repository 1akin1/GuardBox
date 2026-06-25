/*
 * GuardBox - ESP32 Firmware
 * -------------------------------------------------------------
 * Smart, secure package delivery box.
 *
 * Hardware:
 *   - ESP32 Dev Board (WiFi + Bluetooth)
 *   - HX711 + 20kg load cell      -> package detection (weight)
 *   - MFRC522 RFID reader + card  -> authorized access
 *   - SG90 / MG996R servo motor   -> locking mechanism
 *   - Spring vibration sensor     -> tamper detection
 *   - Red / Green LEDs            -> lock status indication
 *   - Push button                 -> door-closed switch
 *
 * Cloud: Firebase Realtime Database (state sync + events)
 *
 * NOTE: Fill in the WiFi/Firebase credentials and verify the GPIO
 *       pin assignments against your own wiring before flashing.
 *       Never commit real credentials to a public repository.
 */

#include <HX711.h>
#include <ESP32Servo.h>
#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <Firebase_ESP_Client.h>

// Firebase helper files
#include "addons/TokenHelper.h"
#include "addons/RTDBHelper.h"

// ===================== WiFi & Firebase Config =====================
// Replace with your own credentials (do NOT commit real values).
#define WIFI_SSID       "YOUR_WIFI_SSID"
#define WIFI_PASSWORD   "YOUR_WIFI_PASSWORD"
#define API_KEY         "YOUR_FIREBASE_API_KEY"
#define DATABASE_URL    "https://YOUR_PROJECT.firebasedatabase.app"
#define USER_EMAIL      "YOUR_AUTH_EMAIL"
#define USER_PASSWORD   "YOUR_AUTH_PASSWORD"

// ===================== Pin Definitions =====================
// Verify these against your actual breadboard wiring.
#define LOADCELL_DT    16
#define LOADCELL_SCK    4
#define SERVO_PIN      13
#define RED_LED         2
#define GREEN_LED      15
#define BUTTON_PIN     27
#define VIBRATION_PIN  14

#define SS_PIN          5   // MFRC522 SDA
#define RST_PIN        22   // MFRC522 RST
#define SCK_PIN        18
#define MOSI_PIN       23
#define MISO_PIN       19

// ===================== Global objects and flags =====================
HX711 scale;
Servo lockServo;
MFRC522 rfid(SS_PIN, RST_PIN);
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

bool locked = false;
bool lastVibrationState = false;
bool weightAlert = false;
bool firebaseConnected = false;
bool bypassDone = false;

unsigned long unlockUntil = 0;
unsigned long remoteUnlockUntil = 0;
unsigned long lastVibrationTime = 0;
const unsigned long unlockDuration = 5000;
const unsigned long remoteUnlockDuration = 5000;
const float weightThreshold = 0.01;

// Authorized RFID cards (example UIDs) - add your own card UIDs here
byte authorizedUIDs[][4] = {
  // { 0xDE, 0xAD, 0xBE, 0xEF },
};
const int authorizedCount = sizeof(authorizedUIDs) / sizeof(authorizedUIDs[0]);

// Function: Check if scanned UID matches any authorized UID
bool isAuthorized(byte *scannedUID) {
  for (int i = 0; i < authorizedCount; i++) {
    bool match = true;
    for (int j = 0; j < 4; j++) {
      if (scannedUID[j] != authorizedUIDs[i][j]) {
        match = false;
        break;
      }
    }
    if (match) return true;
  }
  return false;
}

// Function: Update servo and LED based on lock state
void updateLockState() {
  if (locked) {
    lockServo.write(0);
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
  } else {
    lockServo.write(90);
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, HIGH);
  }
}

// Function: Perform hard reset on RFID module
void resetRFID() {
  digitalWrite(RST_PIN, LOW);
  delay(100);
  digitalWrite(RST_PIN, HIGH);
  delay(500);
  rfid.PCD_Init();
  rfid.PCD_SetAntennaGain(MFRC522::RxGain_max);
}

// Function: Setup Firebase connection
bool setupFirebase() {
  config.database_url = DATABASE_URL;
  config.api_key = API_KEY;
  config.time_zone = 3;
  auth.user.email = USER_EMAIL;
  auth.user.password = USER_PASSWORD;

  Firebase.signUp(&config, &auth, USER_EMAIL, USER_PASSWORD);
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  unsigned long startTime = millis();
  while (!Firebase.ready() && millis() - startTime < 10000) {
    delay(300);
  }
  return Firebase.ready();
}

// Function: Check for RFID card and handle authentication
void checkRFID() {
  if (!rfid.PICC_IsNewCardPresent()) return;

  if (!rfid.PICC_ReadCardSerial()) {
    Serial.println("Failed to read UID. Resetting RFID...");
    resetRFID();
    return;
  }

  Serial.print("UID read: ");
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
    Serial.print(rfid.uid.uidByte[i], HEX);
    Serial.print(" ");
  }
  Serial.println();

  if (isAuthorized(rfid.uid.uidByte)) {
    Serial.println("Authorized card. Unlocking...");
    locked = false;
    updateLockState();
    remoteUnlockUntil = millis() + unlockDuration;
    bypassDone = false;

    if (firebaseConnected) {
      Firebase.RTDB.setBool(&fbdo, "/guardbox/locked", false);
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "RFID unlocked");
    }
  } else {
    Serial.println("Unauthorized card.");
    if (firebaseConnected) {
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "Unauthorized RFID attempt");
    }
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

// Function: Initial setup
void setup() {
  Serial.begin(115200);
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(RST_PIN, OUTPUT);
  digitalWrite(RST_PIN, HIGH);

  lockServo.attach(SERVO_PIN);
  updateLockState();
  delay(1000);

  Serial.println("GuardBox starting...");

  // Initialize weight sensor
  scale.begin(LOADCELL_DT, LOADCELL_SCK);
  scale.set_scale(1500);
  scale.tare();

  // Initialize SPI and RFID
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);
  resetRFID();

  // WiFi setup
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 20000) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected.");
    firebaseConnected = setupFirebase();
    if (firebaseConnected) Serial.println("Firebase connected.");
  }

  updateLockState();
  Serial.println("GuardBox is ready.");
}

// Function: Main control loop
void loop() {
  checkRFID();

  // Print debug info every 5 seconds
  static unsigned long lastDebugTime = 0;
  if (millis() - lastDebugTime > 5000) {
    float weight = abs(scale.get_units(3));
    bool doorClosed = digitalRead(BUTTON_PIN) == LOW;
    Serial.printf("Door: %s | Weight: %.2f | Locked: %s\n",
                  doorClosed ? "Closed" : "Open",
                  weight,
                  locked ? "Yes" : "No");
    lastDebugTime = millis();
  }

  // Handle bypass (unlock delay)
  if (millis() < remoteUnlockUntil) {
    if (locked && !bypassDone) {
      locked = false;
      updateLockState();
      bypassDone = true;
      if (firebaseConnected) {
        Firebase.RTDB.setBool(&fbdo, "/guardbox/locked", false);
      }
    }
    delay(50);
    return;
  } else if (bypassDone) {
    bypassDone = false;
  }

  // Firebase lock control
  if (firebaseConnected && Firebase.ready()) {
    if (Firebase.RTDB.getBool(&fbdo, "/guardbox/locked")) {
      bool cloudLock = fbdo.boolData();
      if (cloudLock != locked) {
        locked = cloudLock;
        updateLockState();
        if (!cloudLock) remoteUnlockUntil = millis() + remoteUnlockDuration;
      }
    }
  }

  // WiFi reconnect logic
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastReconnectAttempt = 0;
    if (millis() - lastReconnectAttempt > 30000) {
      WiFi.reconnect();
      lastReconnectAttempt = millis();
      delay(5000);
      if (WiFi.status() == WL_CONNECTED && !firebaseConnected) {
        firebaseConnected = setupFirebase();
      }
    }
  }

  // Read sensors
  float weight = abs(scale.get_units(3));
  bool doorClosed = digitalRead(BUTTON_PIN) == LOW;
  bool vibration = digitalRead(VIBRATION_PIN) == HIGH;

  // Upload weight
  if (firebaseConnected && Firebase.ready()) {
    Firebase.RTDB.setFloat(&fbdo, "/guardbox/weight", weight);
  }

  // Auto-lock after placing a package
  if (!locked && doorClosed && weight >= weightThreshold && millis() >= remoteUnlockUntil) {
    locked = true;
    updateLockState();
    if (firebaseConnected) {
      Firebase.RTDB.setBool(&fbdo, "/guardbox/locked", true);
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "Box locked due to weight");
    }
  }

  // Notify if empty and unlocked
  static unsigned long lastEmptyNotification = 0;
  if (!locked && doorClosed && weight < weightThreshold && millis() - lastEmptyNotification > 60000) {
    if (firebaseConnected) {
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "Box empty - not locked");
    }
    lastEmptyNotification = millis();
  }

  // Auto-unlock if door opened
  if (locked && !doorClosed) {
    locked = false;
    updateLockState();
    if (firebaseConnected) {
      Firebase.RTDB.setBool(&fbdo, "/guardbox/locked", false);
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "Box unlocked due to door open");
    }
  }

  // Vibration detection
  if (vibration && !lastVibrationState) {
    if (firebaseConnected) {
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "Vibration detected");
    }
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
    lastVibrationTime = millis();
  }

  lastVibrationState = vibration;

  // Weight dropped alert
  if (weight < weightThreshold && !weightAlert) {
    weightAlert = true;
    if (firebaseConnected) {
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "Weight dropped");
    }
  } else if (weight >= weightThreshold && weightAlert) {
    weightAlert = false;
    if (firebaseConnected) {
      Firebase.RTDB.setString(&fbdo, "/guardbox/event", "Weight normal");
    }
  }

  delay(50);
}
