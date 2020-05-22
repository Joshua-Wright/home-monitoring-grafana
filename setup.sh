#!/bin/sh

mkdir -p datadir/ datadir/mosquitto/ datadir/grafana/
sudo chown -R 1883 datadir/mosquitto/
sudo chown -R 472 datadir/grafana/