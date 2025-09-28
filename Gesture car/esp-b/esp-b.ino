#include "BluetoothSerial.h"
#include <WiFi.h>
#include <WiFiUdp.h>

#define Slave_Name "H-C-2010-06-01"
#define MACadd "00:19:10:09:31:AD"

#if !defined(CONFIG_BT_SPP_ENABLED)
#error Serial Bluetooth not available or not enabled. Only for ESP32.
#endif

// 🔹 WiFi credentials
const char* ssid = "OPPO Reno14";
const char* password = "12345678";

// 🔹 UDP settings
const int udpPort = 4210;  // same as ESP32-A
WiFiUDP udp;
char incomingPacket[10];    // small buffer for gesture command

// 🔹 Bluetooth settings
BluetoothSerial SerialBT;
String myName = "ESP32-BT-Master";
const char *pin = "1234";

// 🔹 HC-05 MAC address (optional if connecting by MAC)
uint8_t address[6] = {0x00, 0x19, 0x10, 0x09, 0x31, 0xAD};

void setup() {
  Serial.begin(9600);        // For debugging Serial Monitor
  bool connected;
  // Setup Bluetooth SPP
  SerialBT.begin(myName, true);  // true = master mode
  SerialBT.setPin(pin, strlen(pin));
  //Serial.println("Bluetooth Master started. Connecting to Mega...");

  connected = SerialBT.connect(address);
  Serial.print("Connecting to slave BT device with MAC "); 
  Serial.println(MACadd);


  if(connected) {
    Serial.println("Connected Successfully!");
  } else {
    while(!SerialBT.connected(10000)) {
      Serial.println("Failed to connect. Make sure remote device is available and in range, then restart app.");
    }
  }

  // Disconnect() may take up to 10 secs max
  if (SerialBT.disconnect()) {
    //Serial.println("Disconnected Successfully!");
  }
  // This would reconnect to the slaveName(will use address, if resolved) or address used with connect(slaveName/address).
  SerialBT.connect();
  if(connected) {
    Serial.println("Reconnected Successfully!");
  } else {
    while(!SerialBT.connected(10000)) {
      Serial.println("Failed to reconnect. Make sure remote device is available and in range, then restart app.");
    }
  }


  // Setup WiFi
  WiFi.begin(ssid, password);
  //Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    //Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());

  // Start UDP listener
  udp.begin(udpPort);
  //Serial.println("Listening for UDP packets on port " + String(udpPort));
}

void loop() {
  // Check for incoming UDP packets from ESP32-A
  int packetSize = udp.parsePacket();
  if (packetSize) {
    char incoming[255];               // bigger buffer
    int len = udp.read(incoming, 254); // leave space for null
    if (len > 0) {
      incoming[len] = 0;              // null terminate
      String gesture = String(incoming);
      gesture.trim();                 // remove \r \n or spaces

      if (gesture.length() > 0) {
        Serial.println(gesture);      // clean line to Python
      }

      // Forward to Mega via Bluetooth
      if (SerialBT.connected()) {
        //SerialBT.println(gesture);    // optional if you want Mega to get raw data
      } else {
        Serial.println("Bluetooth disconnected. Trying to reconnect...");
        SerialBT.connect(address);
      }
    }
  }

  if (SerialBT.available()) {
  String msg = SerialBT.readStringUntil('\n');
  // Optional: forward back to PC
  Serial.println("Forwarded to PC: " + msg);
}

  // Optional: forward Serial Monitor input to Mega
  if (Serial.available()) {
    SerialBT.write(Serial.read());
  }
}

