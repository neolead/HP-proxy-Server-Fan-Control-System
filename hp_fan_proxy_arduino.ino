#include <ArduinoJson.h>
#include <EEPROM.h> // Library for working with EEPROM

#define NUM_FANS 6
#define MIN_PWM 10    // Minimum speed (approximately 12%)
#define MAX_PWM 255   // Maximum speed (100%)
#define DEFAULT_PWM 50 // Default value for the first fill

byte fanPins[NUM_FANS] = {3, 5, 6, 9, 10, 11};
String fanNames[NUM_FANS] = {"CPU", "Front", "Rear", "HDD", "PCIe", "Aux"};

void setup() {
  Serial.begin(115200);

  for (byte i = 0; i < NUM_FANS; i++) {
    pinMode(fanPins[i], OUTPUT);

    // Reading PWM value from EEPROM
    int savedPWM = EEPROM.read(i); // Read one byte from EEPROM
    if (savedPWM < MIN_PWM || savedPWM > MAX_PWM) {
      // If the value is incorrect (e.g., first fill), set the default value
      savedPWM = DEFAULT_PWM;
      EEPROM.write(i, savedPWM); // Save the default value in EEPROM
    }

    // Setting the fan speed
    analogWrite(fanPins[i], savedPWM);
    Serial.print("Initialized ");
    Serial.print(fanNames[i]);
    Serial.print(" fan to PWM value ");
    Serial.println(savedPWM);
  }
  Serial.println("Fan Controller Ready");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    processCommand(input);
  }
}

void processCommand(String json) {
  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, json);

  if (error) {
    Serial.print("JSON parsing error: ");
    Serial.println(error.c_str());
    return;
  }

  int fanIdx = doc["fan"];
  int speed = doc["speed"]; // Get value from 0 to 100

  Serial.print("Received speed: ");
  Serial.println(speed);

  // Limit speed in the range [10, 100]
  speed = constrain(speed, 10, 100);

  if (fanIdx >= 0 && fanIdx < NUM_FANS) {
    // Convert speed to PWM
    byte pwm = map(speed, 10, 100, MIN_PWM, MAX_PWM);
    analogWrite(fanPins[fanIdx], pwm);

    Serial.print("Set ");
    Serial.print(fanNames[fanIdx]);
    Serial.print(" fan to PWM value ");
    Serial.println(pwm);
  } else {
    Serial.println("Invalid fan index");
  }
}
