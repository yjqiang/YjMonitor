import sys
from configloader import ConfigLoader
import hashlib
import time
import requests
import base64
import aiohttp
import asyncio
import random
import json
from PIL import Image
from io import BytesIO


def CurrentTime():
    currenttime = int(time.time())
    return str(currenttime)


def randomint():
    return ''.join(str(random.randint(0, 9)) for _ in range(17))


def cnn_captcha(content):
    img = base64.b64encode(content)
    url = "http://47.95.255.188:5000/code"
    data = {"image": img}
    rsp = requests.post(url, data=data)
    captcha = rsp.text
    print(f'此次登录出现验证码,识别结果为{captcha}')
    return captcha
 
       
def input_captcha(content):
    img = Image.open(BytesIO(content))
    # img.thumbnail(size)
    img.show()
    captcha = input('手动输入验证码')
    return captcha


base_url = 'https://api.live.bilibili.com'


class bilibili():
    __slots__ = ('dic_bilibili', 'bili_session', 'app_params', 'var_other_session', 'var_login_session')
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(bilibili, cls).__new__(cls, *args, **kw)
            cls.instance.dic_bilibili = ConfigLoader().dic_bilibili
            dic_bilibili = ConfigLoader().dic_bilibili
            cls.instance.bili_session = None
            cls.instance.var_other_session = None
            cls.instance.var_login_session = None
            cls.instance.app_params = f'actionKey={dic_bilibili["actionKey"]}&appkey={dic_bilibili["appkey"]}&build={dic_bilibili["build"]}&device={dic_bilibili["device"]}&mobi_app={dic_bilibili["mobi_app"]}&platform={dic_bilibili["platform"]}'
        return cls.instance

    @property
    def bili_section(self):
        if self.bili_session is None:
            self.bili_session = aiohttp.ClientSession()
            # print(0)
        return self.bili_session
        
    @property
    def other_session(self):
        if self.var_other_session is None:
            self.var_other_session = aiohttp.ClientSession()
            # print(0)
        return self.var_other_session
        
    @property
    def login_session(self):
        if self.var_login_session is None:
            self.var_login_session = requests.Session()
            # print(0)
        return self.var_login_session

    def calc_sign(self, str):
        str = f'{str}{self.dic_bilibili["app_secret"]}'
        sign = hashlib.md5(str.encode('utf-8')).hexdigest()
        return sign

    @staticmethod
    def load_session(dic):
        # print(dic)
        inst = bilibili.instance
        for i in dic.keys():
            inst.dic_bilibili[i] = dic[i]
            if i == 'cookie':
                inst.dic_bilibili['pcheaders']['cookie'] = dic[i]
                inst.dic_bilibili['appheaders']['cookie'] = dic[i]
                
    def login_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                # print(self.login_session.cookies, url)
                response = self.login_session.post(url, headers=headers, data=data, params=params)
                if response.status_code == requests.codes.ok:
                    return response
                elif response.status_code == 403:
                    print('403频繁')
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
    
    def login_session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                # print(self.login_session.cookies, url)
                response = self.login_session.get(url, headers=headers, data=data, params=params)
                if response.status_code == requests.codes.ok:
                    return response
                elif response.status_code == 403:
                    print('403频繁')
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def get_json_rsp(self, rsp, url):
        if rsp.status == 200:
            # json_response = await response.json(content_type=None)
            data = await rsp.read()
            json_rsp = json.loads(data)
            if isinstance(json_rsp, dict) and 'code' in json_rsp:
                code = json_rsp['code']
                if code == 1024:
                    print('b站炸了，暂停所有请求1.5s后重试，请耐心等待')
                    await asyncio.sleep(1.5)
                    return None
                elif code == 3:
                    print('api错误，稍后重试，请反馈给作者')
                    await asyncio.sleep(1)
                    return None
            return json_rsp
        elif rsp.status == 403:
            print('403频繁', url)
        return None
        
    async def get_text_rsp(self, rsp, url):
        if rsp.status == 200:
            return await rsp.text()
        elif rsp.status == 403:
            print('403频繁', url)
        return None

    async def bili_section_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.bili_section.post(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    async def other_session_get(self, url, headers=None, data=None, params=None, is_none_allowed=False):
        if not is_none_allowed:
            while True:
                try:
                    async with self.other_session.get(url, headers=headers, data=data, params=params) as response:
                        json_rsp = await self.get_json_rsp(response, url)
                        if json_rsp is not None:
                            return json_rsp
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                    continue
        else:
            print('测试')
            for i in range(10):
                try:
                    async with self.other_session.get(url, headers=headers, data=data, params=params) as response:
                        json_rsp = await self.get_json_rsp(response, url)
                        if json_rsp is not None:
                            return json_rsp
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                    continue
                
    async def other_session_post(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.post(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    async def bili_section_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.bili_section.get(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
                
    async def session_text_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers, data=data, params=params) as response:
                    text_rsp = await self.get_text_rsp(response, url)
                    if text_rsp is not None:
                        return text_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue

    @staticmethod
    def request_logout():
        inst = bilibili.instance
        list_url = f'access_key={inst.dic_bilibili["access_key"]}&access_token={inst.dic_bilibili["access_key"]}&{inst.app_params}&ts={CurrentTime()}'
        list_cookie = inst.dic_bilibili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = inst.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/revoke'
        data = f'{params}&sign={sign}'
        appheaders = {**(inst.dic_bilibili['appheaders']), 'cookie': ''}
        response = inst.login_session_post(true_url, params=data, headers=appheaders)
        print(response.json())
        return response
    
    @staticmethod
    async def request_check_room(roomid):
        inst = bilibili.instance
        url = f"{base_url}/room/v1/Room/room_init?id={roomid}"
        response = await inst.bili_section_get(url)
        return response

    @staticmethod
    def request_getkey():
        inst = bilibili.instance
        url = 'https://passport.bilibili.com/api/oauth2/getKey'
        temp_params = f'appkey={inst.dic_bilibili["appkey"]}'
        sign = inst.calc_sign(temp_params)
        params = {'appkey': inst.dic_bilibili['appkey'], 'sign': sign}
        response = inst.login_session_post(url, data=params)
        return response

    @staticmethod
    def normal_login(username, password):
        inst = bilibili.instance
        # url = 'https://passport.bilibili.com/api/oauth2/login'   //旧接口
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        temp_params = f'appkey={inst.dic_bilibili["appkey"]}&password={password}&username={username}'
        sign = inst.calc_sign(temp_params)
        payload = f'appkey={inst.dic_bilibili["appkey"]}&password={password}&username={username}&sign={sign}'
        response = inst.login_session_post(url, params=payload)
        return response

    @staticmethod
    def login_with_captcha(username, password):
        inst = bilibili.instance
        
        # with requests.Session() as s:
        url = "https://passport.bilibili.com/captcha"
        res = inst.login_session_get(url)
        # print(res.content)

        captcha = cnn_captcha(res.content)
        temp_params = f'actionKey={inst.dic_bilibili["actionKey"]}&appkey={inst.dic_bilibili["appkey"]}&build={inst.dic_bilibili["build"]}&captcha={captcha}&device={inst.dic_bilibili["device"]}&mobi_app={inst.dic_bilibili["mobi_app"]}&password={password}&platform={inst.dic_bilibili["platform"]}&username={username}'
        sign = inst.calc_sign(temp_params)
        payload = f'{temp_params}&sign={sign}'
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        response = inst.login_session_post(url, params=payload)
        return response

    @staticmethod
    def request_check_token():
        inst = bilibili.instance
        list_url = f'access_key={inst.dic_bilibili["access_key"]}&{inst.app_params}&ts={CurrentTime()}'
        list_cookie = inst.dic_bilibili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = inst.calc_sign(params)
        true_url = f'https://passport.bilibili.com/api/v2/oauth2/info?{params}&sign={sign}'
        response1 = inst.login_session_get(true_url, headers=inst.dic_bilibili['appheaders'])
        return response1

    @staticmethod
    def request_refresh_token():
        inst = bilibili.instance
        list_url = f'access_key={inst.dic_bilibili["access_key"]}&access_token={inst.dic_bilibili["access_key"]}&{inst.app_params}&refresh_token={inst.dic_bilibili["refresh_token"]}&ts={CurrentTime()}'
        list_cookie = inst.dic_bilibili['cookie'].split(';')
        params = ('&'.join(sorted(list_url.split('&') + list_cookie)))
        sign = inst.calc_sign(params)
        payload = f'{params}&sign={sign}'
        # print(payload)
        url = f'https://passport.bilibili.com/api/v2/oauth2/refresh_token'
        response1 = inst.login_session_post(url, headers=inst.dic_bilibili['appheaders'], params=payload)
        return response1
        
    @staticmethod
    async def get_giftlist_of_guard(roomid):
        inst = bilibili.instance
        true_url = f'{base_url}/lottery/v1/Lottery/check_guard?roomid={roomid}'
        response = await inst.bili_section_get(true_url, headers=inst.dic_bilibili['pcheaders'])
        return response

    @staticmethod
    async def request_send_danmu_msg_web(msg, roomId):
        inst = bilibili.instance
        url = f'{base_url}/msg/send'
        data = {
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg,
            'rnd': '0',
            'roomid': int(roomId),
            'csrf_token': inst.dic_bilibili['csrf']
        }

        response = await inst.bili_section_post(url, headers=inst.dic_bilibili['pcheaders'], data=data)
        return response
        
    async def get_roomids(self, url, page_id):
        json_rsp = await self.other_session_get(f'{url}{page_id}')
        return json_rsp
        
    async def get_rooms_from_remote(self, start, end):
        url = f'http://room.lc4t.cn:8000/dyn_rooms/{start}-{end}'
        json_rsp = await self.other_session_get(url, is_none_allowed=True)
        return json_rsp


