#!/bin/sh

mkdir -p datadir/ datadir/mosquitto/ datadir/grafana/
sudo chown -R 1883:root datadir/mosquitto/
sudo chown -R 472:root datadir/grafana/
