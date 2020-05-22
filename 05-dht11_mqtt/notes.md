# notes.md

# platformio
use this platform https://docs.platformio.org/en/latest/boards/espressif8266/d1_mini.html

# docker-compose for grafana, influxdb, mqtt, etc
ref https://github.com/Nilhcem/home-monitoring-grafana and http://nilhcem.com/iot/home-monitoring-with-mqtt-influxdb-grafana

## need to set permissions for grafana data dir 
`sudo chown -R 472 datadir/grafana/`
ref https://grafana.com/docs/grafana/latest/installation/docker/#migration-from-a-previous-version-of-the-docker-container-to-5-1-or-later

## same permissions fix for mosquitto
but how to find what UID to set to?
1. comment out the `${DATA_DIR}` volumes in `docker-compose.yml`
2. restart docker compose, then use `docker container top mosquitto` to get the UID that the process runs as
   * UID is 1883
   * ref https://docs.docker.com/engine/reference/commandline/top/
3. `sudo chown -R 1883 datadir/mosquitto/`
