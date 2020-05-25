# main.py
import os
from influxdb import InfluxDBClient
from temtop_api import TemtopApi
from datetime import datetime, timedelta
import pytz
from time import sleep

TEMPTOP_USER = os.environ.get('TEMPTOP_USER')
TEMPTOP_PASS = os.environ.get('TEMPTOP_PASS')

INFLUXDB_ADDRESS  = os.environ.get('INFLUXDB_ADDRESS')
INFLUXDB_USER     = os.environ.get('INFLUXDB_USER')
INFLUXDB_PASSWORD = os.environ.get('INFLUXDB_PASSWORD')
INFLUXDB_DATABASE = os.environ.get('INFLUXDB_DATABASE')

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)

timezone = pytz.timezone("America/Chicago")


def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)


def main():
    _init_influxdb_database()

    while True:

        temtopApi = TemtopApi(TEMPTOP_USER, TEMPTOP_PASS)

        deviceId = temtopApi.getFirstDeviceId()
        
        endDateTime = timezone.normalize(datetime.utcnow().replace(tzinfo=pytz.utc))
        startDateTime = endDateTime - timedelta(minutes=30)
        # end 5 minutes in the future, just in case there is some time skew
        endDateTime += timedelta(minutes=5)
        print('querying for:')
        print(f'\tstartDateTime: {startDateTime}')
        print(f'\tendDateTime:   {endDateTime}')
        deviceData = temtopApi.getM10iDeviceData(
            deviceId=deviceId,
            startDateTime=startDateTime,
            endDateTime=endDateTime,
        )

        points = []
        for d in deviceData:
            timestamp = d['datetime']
            for reading_name in temtopApi.readings:
                reading = d[reading_name]
                point = {
                    'time': timestamp,
                    'measurement': reading_name,
                    'tags': { 'location': 'M10i' },
                    'fields': { 'value': reading },
                }
                points.append(point)
        print(f'writing {len(points)} to influxdb')
        success = influxdb_client.write_points(points)
        print(success)

        sleep(10*60)

if __name__ == '__main__':
    print('temptop M10i (elitech cloud) to InfluxDB bridge')
    main()
