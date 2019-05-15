import time
import string
import base64
from datetime import datetime

import rsa


# 半角字符Printable characters(' '-'~')
# 对应的全角字符('　' + '！'-'～')
_table_hwid2fwid = str.maketrans(
    ''.join(chr(i) for i in range(32, 127)),
    '　' + ''.join(chr(i) for i in range(65281, 65375))
    )
    
_table_clear_whitespace = str.maketrans('', '', string.whitespace + '　')
    

# 中英文对齐（半角转全角）
def hwid2fwid(orig_text, format_control=10):
    new_text = orig_text.translate(_table_hwid2fwid)
    return f'{new_text:　^{format_control}}'


def clear_whitespace(orig_text, more_whitespace: str = ''):
    if not more_whitespace:
        return orig_text.translate(_table_clear_whitespace)
    return orig_text.translate(_table_clear_whitespace).\
        translate(str.maketrans('', '', more_whitespace))


def seconds_until_tomorrow():
    dt = datetime.now()
    return (23 - dt.hour) * 3600 + (59 - dt.minute) * 60 + 60 - dt.second
    

def print_progress(finished_exp, sum_exp, num_sum=30):
    num_arrow = int(finished_exp / sum_exp * num_sum)
    num_line = num_sum - num_arrow
    percent = finished_exp / sum_exp * 100
    return f'[{">" * num_arrow}{"-" * num_line}] {percent:.2f}%'
    
    
def curr_time():
    return int(time.time())


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
