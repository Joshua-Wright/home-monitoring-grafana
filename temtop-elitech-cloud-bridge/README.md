# temtop-elitech-cloud-bridge

**problem:** I have a wifi-connected air quality sensor, and I want to programmatically ingest the data.  
**solution:** reverse-engineer the complimentary android app that it uses to find a HTTP API, and use that directly. Then I can load that data into grafana (or whatever I want).

## more details
I used tcpdump and wireshark to reverse engineer the HTTP API that backs the android app that came with my wifi-connected air quality sensor.
Reverse engineering the app's API turned out to be easier than expected because it uses only unencrypted HTTP, cookie-based sessions, and the password is transmitted in plain text. (It's a good thing this isn't a door lock!)
I wrote a simple script to poll the reverse-engineered API and write data to influxdb so I can add it to my grafana dashboard.

