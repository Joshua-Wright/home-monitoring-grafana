import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import namedtuple


def get_devices_info():
    df = pd.read_html('http://192.168.1.254/cgi-bin/devices.ha')[0]
    rows=[{}]
    for i, k, v in df.itertuples():
        if pd.isna(k):
            rows.append({})
            continue
        if ' / ' in k:
            k1, k2 = k.split(' / ')
            v1, v2 = v.split(' / ')
            rows[-1][k1] = v1
            rows[-1][k2] = v2
        else:
            rows[-1][k] = v
    devices = pd.DataFrame(rows)
    devices['ethernet_port'] = np.nan
    for i in [1,2,3,4]:
        devices.loc[devices['Connection Type'] == f'Ethernet LAN-{i}', 'ethernet_port'] = f'Port {i}'
    devices['merge index'] = devices['MAC Address']
    devices.loc[~pd.isna(devices['ethernet_port']), 'merge index'] = devices['ethernet_port']
    devices.set_index('MAC Address', drop=False)
    return devices



def get_device_stats(dfs, devices_info, timestamp):
    wifi_clients = dfs[7]
    ethernet_clients = dfs[8]
    wifi_clients = wifi_clients.set_index(wifi_clients.columns[0], drop=False)
    ethernet_clients = ethernet_clients.set_index(ethernet_clients.columns[0]).transpose()
    ethernet_clients['ethernet_port'] = ethernet_clients.index
    df = pd.concat([wifi_clients, ethernet_clients])
    df['timestamp'] = timestamp
    
    # merge with devices info
    m = (pd.merge(df, devices_info, left_index=True, right_on='merge index')
            .drop(columns=['MAC Address_x', 'ethernet_port_x', 'merge index'])
            .rename(columns={'MAC Address_y': 'MAC Address', 'ethernet_port_y': 'ethernet_port'})
            .set_index('MAC Address', drop=False)
    )
    return m

def get_wifi_radio_stats(dfs):
    wifi_network_config = dfs[5].set_index('Unnamed: 0').dropna(how='all')
    wifi_network_config = wifi_network_config.iloc[0:wifi_network_config.index.get_loc('Guest SSID')]
    packet_counts = dfs[6].set_index(0).dropna(how='all')
    packet_counts = packet_counts.rename(columns=packet_counts.iloc[0])
    packet_counts = packet_counts[packet_counts.index.notna()]

    m = pd.concat([wifi_network_config, packet_counts], axis='index')
    m = m.dropna(how='all')
    m = m.transpose()
    m['Wi-Fi Radio'] = m.index
    return m

def get_broadband_stats():
    dfs2 = pd.read_html('http://192.168.1.254/cgi-bin/broadbandstatistics.ha')
    m = pd.concat([
        dfs2[3].set_index(0).rename(index=lambda idx: f'IPv4 {idx}'), # ipv4
        dfs2[4].set_index(0).rename(index=lambda idx: f'IPv6 {idx}'), # ipv6
        dfs2[2].set_index(0).rename(index=lambda idx: f'IPv6 {idx}'), # ipv6_status
        dfs2[0].set_index(0), # broadband
    ])
    m = m[m.index.notna()]
    m = m[m[1].notna()]
    return m.transpose()

NetworkInfo = namedtuple('NetworkInfo', [
    'timestamp',
    'device_stats',
    'device_count_by_interface',
    'wifi_radio_stats',
    'broadband_stats',
])

def query_router_stats():
    timestamp = datetime.utcnow()
    dfs = pd.read_html('http://192.168.1.254/cgi-bin/lanstatistics.ha')
    devices_info = get_devices_info()

    return NetworkInfo(
        timestamp=timestamp,
        device_stats=get_device_stats(dfs, devices_info, timestamp),
        device_count_by_interface=dfs[1],
        wifi_radio_stats=get_wifi_radio_stats(dfs),
        broadband_stats=get_broadband_stats(),
    )

def compute_data_rates(stats1, stats2):
    cols = [
        'timestamp',
        'Receive Bytes',
        'Transmit Bytes', 
        ]
    merged = pd.merge(stats1[cols], stats2[cols], left_index=True, right_index=True)
    merged['timedelta'] = (merged['timestamp_y'] - merged['timestamp_x'])/timedelta(seconds=1)
    merged['receive_bps'] = (
            (merged['Receive Bytes_y'].astype(int) - merged['Receive Bytes_x'].astype(int)) 
            / merged['timedelta']
        ).astype(int)
    merged['transmit_bps'] = (
            (merged['Transmit Bytes_y'].astype(int) - merged['Transmit Bytes_x'].astype(int)) 
            / merged['timedelta']
        ).astype(int)
    merged = merged.drop(columns=[
        'Receive Bytes_y',
        'Receive Bytes_x',
        'Transmit Bytes_y',
        'Transmit Bytes_x',
    ]).rename(columns={
        'timestamp_x': 'begin_timestamp',
        'timestamp_y': 'end_timestamp',
    })
    return merged


def capture_all_stats(outdir='stats'):
    stats = query_router_stats()._asdict()
    for key in ['device_stats', 'device_count_by_interface', 'wifi_radio_stats', 'broadband_stats']:
        stats[key].to_csv(f'stats/{key}.csv')

if __name__ == '__main__':
    capture_all_stats()
