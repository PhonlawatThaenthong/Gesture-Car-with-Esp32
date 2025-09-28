

void setup() {
  Serial.begin(9600);    // Serial Monitor
  Serial1.begin(9600);   // RX1/TX1 connected to HC-05
  Serial.println("Mega ready to receive gestures from ESP32-B...");
}

int gestureCount = 0;

void loop() {
  if (Serial1.available()) {
    String gesture = Serial1.readStringUntil('\n');  // read until newline

    gesture.trim();  // remove any whitespace/newlines
    if (gesture.length() > 0) {
      gestureCount++;
      Serial.print("Gesture #");
      Serial.print(gestureCount);
      Serial.print(": ");
      Serial.println(gesture);
      Serial1.println("Safe");
    }
    if (gestureCount % 10 == 0){
      Serial1.println("block");
    }
  }

}
