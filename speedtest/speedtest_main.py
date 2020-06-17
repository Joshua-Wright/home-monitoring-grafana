import os
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
from time import sleep
import random
import speedtest

servers = []
# If you want to test against a specific server
# servers = [1234]

threads = None
# If you want to use a single threaded test
# threads = 1

def do_speed_test():
    s = speedtest.Speedtest()
    s.get_servers(servers)
    s.get_best_server()
    s.download(threads=threads)
    s.upload(threads=threads)
    s.results.share()
    return s.results.dict()

min_wait = 0.5 # hours
max_wait = 2.0 # hours

def random_wait():
    wait_sec = random.randrange(int(60*60*min_wait), int(60*60*max_wait))
    delay = timedelta(seconds=wait_sec)
    next_run = datetime.now() + delay
    print(f'waiting {delay}, until {next_run}')
    sleep(wait_sec)


INFLUXDB_ADDRESS  = os.environ.get('INFLUXDB_ADDRESS')
INFLUXDB_USER     = os.environ.get('INFLUXDB_USER')
INFLUXDB_PASSWORD = os.environ.get('INFLUXDB_PASSWORD')
INFLUXDB_DATABASE = os.environ.get('INFLUXDB_DATABASE')

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)


def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)


def main():
    _init_influxdb_database()

    while True:

        print('running speed test')
        result = do_speed_test()
        data_point = {
            'time': result['timestamp'],
            'measurement': 'internet_speed_test',
            'tags': { 'source': 'speedtest.net' },
            'fields': {
                'download': result['download'],
                'upload': result['upload'],
                'ping': result['ping'],
                'bytes_sent': result['bytes_sent'],
                'bytes_received': result['bytes_received'],
                'share': result['share'],
                'client_ip': result['client']['ip'],
                'client_lat': result['client']['lat'],
                'client_lon': result['client']['lon'],
                'client_isp': result['client']['isp'],
                'client_isprating': result['client']['isprating'],
                'server_url':     result['server']['url'],
                'server_lat':     result['server']['lat'],
                'server_lon':     result['server']['lon'],
                'server_name':    result['server']['name'],
                'server_country': result['server']['country'],
                'server_cc':      result['server']['cc'],
                'server_sponsor': result['server']['sponsor'],
                'server_id':      result['server']['id'],
                'server_host':    result['server']['host'],
                'server_d':       result['server']['d'],
                'server_latency': result['server']['latency'],
            },
        }
        print(f'writing {data_point} to influxdb')
        success = influxdb_client.write_points([data_point])
        print(success)

        random_wait()

if __name__ == '__main__':
    print('begin periodic network speed test')
    main()
