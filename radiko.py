#!/usr/bin/env python

import argparse
import base64
import os
import re
import subprocess
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
import requests
from selenium import webdriver

from spinner import Spinner, spinner_decorator


class Radiko:
    
    player_name = 'myplayer-release.swf'
    key_name = 'authkey.png'
    player_url = 'http://radiko.jp/apps/js/flash/' + player_name
    fms1_url = 'https://radiko.jp/v2/api/auth1_fms'
    fms2_url = 'https://radiko.jp/v2/api/auth2_fms'

    def __init__(self, url):
        self.url = url
        self.spinner = Spinner()

        self.stream_url = None
        self.station_id = None
        self.ft = None
        self.to = None
        self.auth_token = None
        self.key_offset = None
        self.key_length = None
        self.partial_key = None
        self.auth_response_body = None
        self.area_id = None
        self.title = None

    @spinner_decorator('Obtaining streaming url... ', 'done')
    def set_basic_info(self):
        driver = webdriver.PhantomJS(executable_path='./phantomjs', service_log_path=os.path.devnull)
        
        driver.get(self.url)
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        hidden_input = soup.find('input', id='share-url')
        self.stream_url = str(hidden_input['value'])

        pat = r'station_id=(?P<station_id>[A-Z\-]+)&ft=(?P<ft>[0-9]+)&to=(?P<to>[0-9]+)'
        match = re.search(pat, self.stream_url)
        if match:
            self.station_id = match.group('station_id')
            self.ft = match.group('ft')
            self.to = match.group('to')
    
    def authenticate(self):
        @spinner_decorator('Downloading player... ', 'done')
        def download_player():
            r = requests.get(self.player_url)
            if r.status_code == 200:
                with open('myplayer-release.swf', 'wb') as f:
                    f.write(r.content)
        
        @spinner_decorator('Creating key file... ', 'done')
        def create_key():
            subprocess.call('swfextract -b 12 {} -o {}'.format(self.player_name, self.key_name), shell=True)
        
        @spinner_decorator('Authenticating with auth1_fms... ', 'done')
        def auth1():
            headers = {
                'Host': 'radiko.jp',
                'pragma': 'no-cache',
                'X-Radiko-App': 'pc_ts',
                'X-Radiko-App-Version': '4.0.0',
                'X-Radiko-User': 'test-stream',
                'X-Radiko-Device': 'pc'
            }
            r = requests.post(url=self.fms1_url, headers=headers)
            
            if r.status_code == 200:
                response_headers = r.headers
                self.auth_token = response_headers['x-radiko-authtoken']
                self.key_offset = int(response_headers['x-radiko-keyoffset'])
                self.key_length = int(response_headers['x-radiko-keylength'])
        
        @spinner_decorator('Creating partial key file... ', 'done')
        def create_partial_key():
            with open(self.key_name, 'rb+') as f:
                f.seek(self.key_offset)
                data = f.read(self.key_length)
                self.partial_key = base64.b64encode(data)
        
        @spinner_decorator('Authenticating with auth2_fms... ', 'done')
        def auth2():
            headers ={
                'pragma': 'no-cache',
                'X-Radiko-App': 'pc_ts',
                'X-Radiko-App-Version': '4.0.0',
                'X-Radiko-User': 'test-stream',
                'X-Radiko-Device': 'pc',
                'X-Radiko-Authtoken': self.auth_token,
                'X-Radiko-Partialkey': self.partial_key,
            }
            r = requests.post(url=self.fms2_url, headers=headers)

            if r.status_code == 200:
                self.auth_response_body = r.text
        
        download_player()
        create_key()
        auth1()
        create_partial_key()
        auth2()
    
    def set_area_id(self):
        area = self.auth_response_body.strip().split(',')
        self.area_id = area[0]
    
    @spinner_decorator('Obtainig file title... ', 'done')
    def set_title(self):
        try:
            datetime_api_url = 'http://radiko.jp/v3/program/date/{}/{}.xml'.format(self.ft[:8], self.area_id)
            r = requests.get(url=datetime_api_url)
            if r.status_code == 200:
                channels_xml = r.content
                tree = ET.fromstring(channels_xml)
                station = tree.find('.//station[@id="{}"]'.format(self.station_id))
                prog = station.find('.//prog[@ft="{}"]'.format(self.ft))
                to = prog.attrib['to']
        except AttributeError:
            datetime_api_url = 'http://radiko.jp/v3/program/date/{}/{}.xml'.format(int(self.ft[:8]) - 1, self.area_id)
            r = requests.get(url=datetime_api_url)
            if r.status_code == 200:
                channels_xml = r.content
                tree = ET.fromstring(channels_xml)
                station = tree.find('.//station[@id="{}"]'.format(self.station_id))
                prog = station.find('.//prog[@ft="{}"]'.format(self.ft))
                to = prog.attrib['to']

        self.title = prog.find('.//title').text.replace(' ', '_').replace('　', '_')

    def setup(self):
        self.set_basic_info()
        self.authenticate()
        self.set_area_id()
        self.set_title()
    
    def teardown(self):
        os.remove(self.player_name)
        os.remove(self.key_name)

    def download(self):
        self.setup()
        
        cmd = (
            'ffmpeg '
            '-loglevel fatal '
            '-n -headers "X-Radiko-AuthToken: {}" '
            '-i "{}" '
            '-vn -acodec copy "{}.aac"'.format(
                self.auth_token,
                self.stream_url,
                self.title
            )
        )
        print('Downloading {}.aac... '.format(self.title), end='')
        self.spinner.start()
        subprocess.call(cmd, shell=True)
        self.spinner.stop()
        print('done!')

        self.teardown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('url')
    args = parser.parse_args()
    
    url = args.url
    radiko = Radiko(url)
    radiko.download()
