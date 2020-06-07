#include <Arduino.h>

/**
    Required libraries:
      - PubSubClient
      - DHT11
      - ArduinoJson
**/
#include <Wire.h>
#include <SPI.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoOTA.h>
#include <ArduinoJson.h>


// must define MQTT_SERVER, MQTT_USER, MQTT_PASSWORD, WIFI_SSID, WIFI_PASSWORD
#include "secrets.h"

#define DHTPIN 2
#define DHTTYPE DHT11


#define MQTT_TOPIC "home/dht11"
#define MQTT_TOPIC_HUMIDITY    MQTT_TOPIC "/humidity"
#define MQTT_TOPIC_TEMPERATURE MQTT_TOPIC "/temperature"
#define MQTT_TOPIC_STATE       MQTT_TOPIC "/status"
#define MQTT_PUBLISH_DELAY 1000
#define MQTT_CLIENT_ID "esp8266dht11"



float humidity = 0.5;
float temperature = 0.5;
long lastMsgTime = 0;
long mqttMessagesSent = 0;
long dht11SuccessfulReadings = 0;
long dht11TotalReadings = 0;


WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHTPIN, DHTTYPE);

void setupWifi();
void mqttReconnect();
void mqttPublish(const char *topic, float payload);
void mqttPublish(const char *topic, const char* payload);
void mqttPublish(const char *topic, String payload);
void publishSensorStartupInfo();
void publishSensorStats();

void setup() {
  Serial.begin(115200);
  while (! Serial);
  dht.begin();

  setupWifi();
  mqttClient.setBufferSize(512);
  mqttClient.setServer(MQTT_SERVER, 1883);

  ESP.wdtEnable(1000);

  if (!mqttClient.connected()) {
    mqttReconnect();
  }
  publishSensorStartupInfo();
}

void loop() {
  ESP.wdtFeed();
  ArduinoOTA.handle();
  if (!mqttClient.connected()) {
    mqttReconnect();
  }
  mqttClient.loop();

  long now = millis();
  if (now - lastMsgTime > MQTT_PUBLISH_DELAY) {
    publishSensorStats();
    lastMsgTime = now;

    long now_before_reading = millis();
    // Reading temperature or humidity takes about 250 milliseconds!
    // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
    humidity = dht.readHumidity();
    long now_humidity = millis();
    // Read temperature as Celsius (the default)
    temperature = dht.readTemperature();
    long now_temperature = millis();
    dht11TotalReadings++;

    mqttPublish(MQTT_TOPIC "/now", now);
    mqttPublish(MQTT_TOPIC_TEMPERATURE "_read_time", now_temperature - now_humidity);
    mqttPublish(MQTT_TOPIC_HUMIDITY "_read_time", now_humidity - now_before_reading);

    // Check if any reads failed and exit early (to try again).
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println(F("Failed to read from DHT sensor!"));
      mqttPublish(MQTT_TOPIC "/read_success", 0.0);
      publishSensorStats();
      return;
    }
    mqttPublish(MQTT_TOPIC "/read_success", 1.0);
    dht11SuccessfulReadings++;

    // Publishing sensor data
    mqttPublish(MQTT_TOPIC_TEMPERATURE, temperature);
    mqttPublish(MQTT_TOPIC_HUMIDITY, humidity);
    publishSensorStats();
  }
}


///////////////////////////////////////////////////////////////////////////////

void publishSensorStartupInfo() {
  const size_t capacity = JSON_OBJECT_SIZE(10) + 512;
  DynamicJsonDocument doc(capacity);

  doc[F("ResetInfo")]        = ESP.getResetInfo();
  doc[F("ResetReason")]      = ESP.getResetReason();
  doc[F("LocalIP")]          = WiFi.localIP().toString();
  doc[F("MacAddress")]       = WiFi.macAddress();
  doc[F("SSID")]             = WiFi.SSID();
  doc[F("BSSIDstr")]         = WiFi.BSSIDstr();
  doc[F("SketchMD5")]        = ESP.getSketchMD5();
  doc[F("SketchSize")]       = ESP.getSketchSize();
  doc[F("FreeSketchSpace")]  = ESP.getFreeSketchSpace();
  doc[F("FullVersion")]      = ESP.getFullVersion();

  String json;
  serializeJson(doc, json);
  mqttPublish(MQTT_TOPIC "/startup_info_json", json);
  // publishSensorStats();
}

void publishSensorStats() {
  uint32_t hfree;
  uint16_t hmax;
  uint8_t hfrag;
  ESP.getHeapStats(&hfree, &hmax, &hfrag);

  const size_t capacity = JSON_OBJECT_SIZE(9) + 256;
  DynamicJsonDocument doc(capacity);

  doc[F("hfree")]                   = hfree;
  doc[F("hmax")]                    = hmax;
  doc[F("hfrag")]                   = hfrag;
  doc[F("CycleCount")]              = ESP.getCycleCount();
  doc[F("Vcc")]                     = ESP.getVcc();
  doc[F("FreeContStack")]           = ESP.getFreeContStack();
  doc[F("mqttMessagesSent")]        = mqttMessagesSent;
  doc[F("dht11SuccessfulReadings")] = dht11SuccessfulReadings;
  doc[F("dht11TotalReadings")]      = dht11TotalReadings;
  String json = "";
  serializeJson(doc, json);
  mqttPublish(MQTT_TOPIC "/system_info", json);

}




///////////////////////////////////////////////////////////////////////////////

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

  ArduinoOTA.setHostname("ESP8266");
  ArduinoOTA.setPassword("esp8266");

  ArduinoOTA.onStart([]() {
    Serial.println("Start");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
  });
  ArduinoOTA.begin();
  Serial.println("OTA ready");

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

void mqttPublish(const char *topic, float payload) {
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(payload);

  if (!mqttClient.publish(topic, String(payload).c_str(), true)) {
    Serial.println("failed to send MQTT message!");
  }
  mqttMessagesSent++;
}

void mqttPublish(const char *topic, const char* payload) {
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(payload);

  if (!mqttClient.publish(topic, payload, true)) {
    Serial.println("failed to send MQTT message!");
  }
  mqttMessagesSent++;
}

void mqttPublish(const char *topic, String payload) {
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(payload);

  if (!mqttClient.publish(topic, payload.c_str(), true)) {
    Serial.println("failed to send MQTT message!");
  }
  mqttMessagesSent++;
}
