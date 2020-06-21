from typing import List, Dict, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import namedtuple

from arris_router_api import *

def sanitize_name(name: str) -> str:
    return (name
        .lower()
        .replace(' ', '_')
    )

def df_to_points(df: pd.DataFrame, timestamp, measurement: str, fields: Dict[str, Callable], tags: Dict[str, Callable]):
    fallback_timestamp = timestamp
    points = []
    for k, row in df.to_dict(orient='index').items():
        data_point = {
            'time': fallback_timestamp,
            'measurement': measurement,
            'tags': {
                sanitize_name(tag): f(row[tag]) for tag, f in tags.items()
                if row[tag] is not None and pd.notna(row[tag])
            },
            'fields': {
                sanitize_name(field): f(row[field]) for field, f in fields.items()
                if row[field] is not None and pd.notna(row[field])
            },
        }
        if 'timestamp' in row:
            data_point['time'] = row['timestamp']
        points.append(data_point)
    return points

def stats_to_points(stats: NetworkInfo):
    points = []
    points += df_to_points(
        stats.device_stats,
        timestamp=stats.timestamp,
        measurement='network_device_stats',
        fields={
            'Transmit Packets': int,
            'Transmit Bytes': int,
            'Transmit Speed': int,
            'Transmit Unicast': int,
            'Transmit Multicast': int,
            'Transmit Dropped': int,
            'Transmit Errors': int,
            'Receive Packets': int,
            'Receive Bytes': int,
            'Receive Unicast': int,
            'Receive Multicast': int,
            'Receive Dropped': int,
            'Receive Errors': int,
            'Trans Errors': int,
            'Disassoc Count': int,
            'Deauth Count': int,
            'Signal Strength': str,
        },
        tags={
            # 'IP Address',
            # 'State',
            # 'Authentication State',
            # 'Last Activity',
            # 'Status',
            # 'Mesh Client',
            # 'Allocation',
            'Radio Channel': int,
            'Access Point': str,
            'Connection Type': str,
            'MAC Address': str,
            'IPv4 Address': str,
            'Name': str,
            'ethernet_port': str,
        }
    )
    points += df_to_points(
        stats.device_count_by_interface,
        timestamp=stats.timestamp,
        measurement='network_device_count_by_interface',
        fields={
            'Active Devices': int,
            'Inactive Devices': int,
        },
        tags={
            'Interface': str,
            'Status': str,
        }
    )
    points += df_to_points(
        stats.wifi_radio_stats,
        timestamp=stats.timestamp,
        measurement='network_wifi_radio_stats',
        fields={
            'Current Data Throughput': int,
            '24 Hour Peak Data Throughput': int,
            'Transmit Bytes': int,
            'Receive Bytes': int,
            'Transmit Packets': int,
            'Receive Packets': int,
            'Transmit Error Packets': int,
            'Receive Error Packets': int,
            'Transmit Discard Packets': int,
            'Receive Discard Packets': int,
        },
        tags={
            # 'Wi-Fi Radio Status',
            'Mode': str,
            'Bandwidth': str,
            'Current Radio Channel': int,
            'Radio Channel Selection': str,
            'Power Level': str,
            # 'Home SSID',
            # 'Network Name (SSID)',
            # 'Hide Network Name',
            # 'Security',
            # 'MAC Address Filtering',
            # 'MAC Address',
            # 'Wi-Fi Radio',
        }
    )
    points += df_to_points(
        stats.broadband_stats,
        timestamp=stats.timestamp,
        measurement='network_broadband_stats',
        fields={
            'IPv4 Receive Packets': int,
            'IPv4 Transmit Packets': int,
            'IPv4 Receive Bytes': int,
            'IPv4 Transmit Bytes': int,
            'IPv4 Receive Unicast': int,
            'IPv4 Transmit Unicast': int,
            'IPv4 Receive Multicast': int,
            'IPv4 Transmit Multicast': int,
            'IPv4 Receive Drops': int,
            'IPv4 Transmit Drops': int,
            'IPv4 Receive Errors': int,
            'IPv4 Transmit Errors': int,
            'IPv4 Collisions': int,
            'IPv6 Transmit Packets': int,
            'IPv6 Transmit Errors': int,
            'IPv6 Transmit Discards': int,
        },
        tags={
            # 'IPv6 Status',
            # 'IPv6 Service Type',
            'IPv6 Global Unicast IPv6 Address': str,
            'IPv6 Link Local Address': str,
            'IPv6 Default IPv6 Gateway Address': str,
            'IPv6 Global Unicast IPv6 Address': str,
            'IPv6 Link Local Address': str,
            'IPv6 Default IPv6 Gateway Address': str,
            # 'IPv6 MTU',
            'Broadband Connection Source': str,
            'Broadband Connection': str,
            'Broadband Network Type': str,
            'Broadband IPv4 Address': str,
            'Gateway IPv4 Address': str,
            'MAC Address': str,
            'Primary DNS': str,
            'Secondary DNS': str,
            # 'MTU',
        }
    )
    return points


def main():
    import os
    from time import sleep
    import random
    from datetime import datetime, timedelta
    from influxdb import InfluxDBClient

    min_wait = 25 # seconds
    max_wait = 45 # seconds

    def random_wait():
        wait_sec = random.randrange(int(min_wait), int(max_wait))
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

    _init_influxdb_database()

    while True:
        stats = query_router_stats()
        points = stats_to_points(stats)
        print(f'writing {points} to influxdb')
        success = influxdb_client.write_points(points)
        print(success)

        random_wait()

if __name__ == '__main__':
    print('begin periodic network data usage and statistics log')
    main()
