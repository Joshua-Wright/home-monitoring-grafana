#include <Arduino.h>

/**
    Required libraries:
      - PubSubClient
      - DHT11
**/
#include <Wire.h>
#include <SPI.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>


// must define MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, WIFI_SSID, WIFI_PASSWORD
#include "secrets.h"

#define DHTPIN 2
#define DHTTYPE DHT11


#define MQTT_TOPIC_HUMIDITY "home/dht11/humidity"
#define MQTT_TOPIC_TEMPERATURE "home/dht11/temperature"
#define MQTT_TOPIC_STATE "home/dht11/status"
#define MQTT_PUBLISH_DELAY 3000
#define MQTT_CLIENT_ID "esp8266dht11"



float humidity = 0.5;
float temperature = 0.5;
long lastMsgTime = 0;


WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHTPIN, DHTTYPE);

void setupWifi();
void mqttReconnect();
void mqttPublish(char *topic, float payload);

void setup() {
  Serial.begin(115200);
  while (! Serial);
  dht.begin();

  setupWifi();
  mqttClient.setServer(MQTT_SERVER, 1883);
}

void loop() {
  if (!mqttClient.connected()) {
    mqttReconnect();
  }
  mqttClient.loop();

  long now = millis();
  if (now - lastMsgTime > MQTT_PUBLISH_DELAY) {
    lastMsgTime = now;

    // Reading temperature or humidity takes about 250 milliseconds!
    // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
    humidity = dht.readHumidity();
    // Read temperature as Celsius (the default)
    temperature = dht.readTemperature();

    // Check if any reads failed and exit early (to try again).
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println(F("Failed to read from DHT sensor!"));
      return;
    }

    // Publishing sensor data
    mqttPublish(MQTT_TOPIC_TEMPERATURE, temperature);
    mqttPublish(MQTT_TOPIC_HUMIDITY, humidity);
  }
}

void setupWifi() {
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void mqttReconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");

    // Attempt to connect
    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD, MQTT_TOPIC_STATE, 1, true, "disconnected", false)) {
      Serial.println("connected");

      // Once connected, publish an announcement...
      mqttClient.publish(MQTT_TOPIC_STATE, "connected", true);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void mqttPublish(char *topic, float payload) {
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(payload);

  mqttClient.publish(topic, String(payload).c_str(), true);
}
