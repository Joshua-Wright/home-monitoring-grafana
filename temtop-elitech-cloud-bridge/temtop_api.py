# download_data.py
import requests
from datetime import datetime, timedelta
import pytz


class TemtopApi:
    readings = [ 'HCHO', 'PM2.5', 'TVOC', 'AQI' ]

    def __init__(self, username, password):
        # do login
        self.headers = {
            'User-Agent': 'okhttp/2.7.5',
        }
        r = requests.get(
            f'http://www.i-elitech.com//apiLoginAction.do?method=login&password={password}&username={username}',
            headers=self.headers,
        )
        resp = r.json()
        if not resp['success']:
            raise RuntimeError('login failed')
        self.userId = resp['user']['id']
        self.token = resp['token']
        self.timezone = pytz.timezone("America/Chicago")


    def get(self, url: str, params: None):
        headers = {
            'User-Agent': 'okhttp/2.7.5',
            'JSESSIONID': self.token,
        }
        cookies = { 'JSESSIONID': self.token }
        r = requests.get(url, headers=headers, cookies=cookies, params=params)
        resp = r.json()
        if not resp['success']:
            print(f'request failed, response={resp}')
            raise RuntimeError('request failed')
        return resp

    def getDeviceList(self):
        params={
            'method':   'getList',
            'typeList': '0',
            'userId':   self.userId,
        }
        return self.get('http://www.i-elitech.com//apiDeviceAction.do', params=params)['rows']
    
    def getFirstDeviceId(self) -> int:
        return self.getDeviceList()[0]['id']

    def getDeviceData(self, deviceId: int, startDateTime: datetime, endDateTime: datetime):
        params = {
            'method'    : 'getList',
            'page'      : '1',
            'rows'      : '4500',
            'startDate' : startDateTime.replace(tzinfo=None).isoformat(sep=' ', timespec='seconds'),
            'endDate'   : endDateTime.replace(tzinfo=None).isoformat(sep=' ', timespec='seconds'),
            'deviceId'  : deviceId,
        }
        return self.get('http://www.i-elitech.com//apiDeviceDataAction.do', params=params)['rows']
    
    def getM10iDeviceData(self, deviceId: int, startDateTime: datetime, endDateTime: datetime):
        data = self.getDeviceData(deviceId, startDateTime, endDateTime)
        
        def parseDate(createTime) -> datetime:
            d = datetime(
                day     = createTime['date'],
                hour    = createTime['hours'],
                minute  = createTime['minutes'],
                month   = createTime['month']+1,
                second  = createTime['seconds'],
                year    = createTime['year']+1900,
                tzinfo  = None,
            )
            return self.timezone.localize(d)
        return [
            {
                # 'originaldatetime': d['createTime'],
                'datetime' : parseDate(d['createTime']),
                'HCHO'     : float(d['probe1']),
                'PM2.5'    : float(d['probe2']),
                'TVOC'     : float(d['probe3']),
                'AQI'      : float(d['probe4']),
            }
            for d in data
        ]


if __name__ == '__main__':
    import os

    username = os.environ.get('TEMPTOP_USER')
    password = os.environ.get('TEMPTOP_PASS')
    api = TemtopApi(username, password)

    deviceId = api.getFirstDeviceId()
    print(f'device id: {deviceId}')

    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0)
    # end 5 minutes in the future, just in case there is some time skew
    now += timedelta(minutes=5)
    deviceData = api.getM10iDeviceData(
        deviceId=deviceId,
        startDateTime=midnight,
        endDateTime=now,
    )
    print('data for today:')
    for d in deviceData:
        print(d)

    for reading in [ 'HCHO', 'PM2.5', 'TVOC', 'AQI' ]:
        print(f'min {reading}: {min(deviceData, key=lambda x: x[reading])}')

