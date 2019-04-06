import base64
from time import time, sleep

import rsa
import requests


def curr_time():
    return int(time())
    
    
def sign(msg: str, privkey: rsa.PrivateKey) -> str:
    bytes_msg = msg.encode('utf8')
    bytes_signature = rsa.sign(bytes_msg, privkey, 'SHA-256')
    str_signature = base64.b64encode(bytes_signature).decode('utf8')
    return str_signature
    

# need_name是False, 返回不带name的结果
def make_signature(name: str, privkey: rsa.PrivateKey, need_name=True) -> dict:
    int_curr_time = curr_time()
    msg = f'Hello World. This is {name} at {int_curr_time}.'
    str_signature = sign(msg, privkey)
    if need_name:
        return {
            'signature': str_signature,
            'time': int_curr_time,
            'name': name
        }
    return {
        'signature': str_signature,
        'time': int_curr_time
    }


def request_json(method, url, timeout=3, **kwargs):
    while True:
        try:
            with requests.request(method, url, timeout=timeout, **kwargs) as rsp:
                if rsp.status_code == 200:
                    return rsp.json()
                print(rsp.status_code)
                return {'code': 404}
        except Exception as e:
            print(e)
            sleep(3)

