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


# setup server
make sure system time is correct https://vitux.com/keep-your-clock-sync-with-internet-time-servers-in-ubuntu/

# OTA
gotta set that up manualy
https://docs.platformio.org/en/latest/platforms/espressif8266.html#over-the-air-ota-update
https://tttapa.github.io/ESP8266/Chap13%20-%20OTA.html


# using `influx` command-line interface
influxdb query documentation https://docs.influxdata.com/influxdb/v1.8/query_language/explore-data/
```bash
export DATA_DIR=$(pwd)/datadir
docker-compose up -d --no-deps --build mqttbridge


docker exec -it influxdb bash
root@a5d0beabd98e:/# influx
> show databases
name: databases
name
----
home_db
_internal
> use home_db
Using database home_db

show measurements
show series

```

# how to make python requirements.txt docker image
```bash
pipenv lock --requirements > requirements.txt
```

