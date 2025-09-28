#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// 🔹 WiFi credentials
const char* ssid = "OPPO Reno14";
const char* password = "12345678";

// 🔹 ESP32-B IP and port
const char* ESP32B_IP = "10.54.192.108";  // Replace with ESP32-B IP
const int ESP32B_PORT = 4210;

WiFiUDP udp;
Adafruit_MPU6050 mpu;

// Kalman filter variables
float x_angle = 0, y_angle = 0;
float x_bias = 0, y_bias = 0;
float P[2][2] = { { 1, 0 }, { 0, 1 } };

// 🔹 Kalman filter tuning parameters
float q_angle = 0.01;    
float q_bias = 0.01;     
float r_measure = 0.01;  

// Kalman filter function
float kalmanFilter(float newAngle, float newRate, float dt, float &angle, float &bias) {
  float rate = newRate - bias;
  angle += dt * rate;

  // Update estimation error covariance
  P[0][0] += dt * (dt * P[1][1] - P[0][1] - P[1][0] + q_angle);
  P[0][1] -= dt * P[1][1];
  P[1][0] -= dt * P[1][1];
  P[1][1] += q_bias * dt;

  // Compute Kalman gain
  float S = P[0][0] + r_measure;
  float K[2] = { P[0][0] / S, P[1][0] / S };

  // Update estimates with measurement
  float y = newAngle - angle;
  angle += K[0] * y;
  bias  += K[1] * y;

  // Update error covariance matrix
  P[0][0] -= K[0] * P[0][0];
  P[0][1] -= K[0] * P[0][1];
  P[1][0] -= K[1] * P[0][0];
  P[1][1] -= K[1] * P[0][1];

  return angle;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Init MPU6050
  if (!mpu.begin()) {
    Serial.println("MPU6050 not found!");
    while (1) delay(10);
  }
  Serial.println("MPU6050 ready");

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_10_HZ);

  // WiFi connect
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("ESP32-A IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  static unsigned long prevTime = millis();
  float dt = (millis() - prevTime) / 1000.0;
  prevTime = millis();

  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // Apply Kalman filter
  float filteredX = kalmanFilter(a.acceleration.x, g.gyro.x, dt, x_angle, x_bias);
  float filteredY = kalmanFilter(a.acceleration.y, g.gyro.y, dt, y_angle, y_bias);

  char cmd = 'S'; // default Stop

  // Gesture detection with 2-stage speeds
  // if (filteredY > 5 && filteredY <= 8)       cmd = 'r';   // Forward slow
  // else if (filteredY > 8)                    cmd = 'R';   // Forward fast

  // else if (filteredY < -5 && filteredY >= -8) cmd = 'l';  // Backward slow
  // else if (filteredY < -8)                    cmd = 'L';  // Backward fast

  // else if (filteredX > 5 && filteredX <= 8)   cmd = 'b';  // Right slow
  // else if (filteredX > 8)                     cmd = 'B';  // Right fast

  // else if (filteredX < -5 && filteredX >= -8) cmd = 'f';  // Left slow
  // else if (filteredX < -8)                    cmd = 'F';  // Left fast

  // else cmd = 'S';  // Stop

  // Debug output
  // Serial.print("FilteredX: "); Serial.print(filteredX, 2);
  // Serial.print(" FilteredY: "); Serial.print(filteredY, 2);
  // Serial.print(" -> CMD: "); Serial.println(cmd);
  Serial.print(filteredX, 2);
  Serial.print(",");
  Serial.print(filteredY, 2);
  Serial.print(",");
  char buffer[50];
  snprintf(buffer, sizeof(buffer), "%.2f,%.2f", filteredX, filteredY);
  // Send command to ESP32-B
  udp.beginPacket(ESP32B_IP, ESP32B_PORT);
  //udp.write(cmd);
  udp.print(buffer); 
  udp.endPacket();

  delay(100); // adjust responsiveness
}
