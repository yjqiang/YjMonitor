"""用于检查服务器状态，比如有多少人在监听服务器、推送者有哪些等等
"""

import rsa

import utils
import global_var


name = 'bbbn'  # 用户名没必要改
key = 'V_F<Nv)!WeK]irWY'  # 检测 key 是否存在以及相关信息

with open(f'{global_var.KEY_PATH}/admin_privkey.pem', 'rb') as f:
    admin_privkey = rsa.PrivateKey.load_pkcs1(f.read())


dict_signature = utils.make_signature(
    name,
    admin_privkey,
    need_name=True)

data = {}
if key:
    naive_hashed_key = utils.naive_hash(key)
    data['naive_hashed_key'] = naive_hashed_key
    
data = {
    'code': 0,
    'type': 'raffle',
    'data': data,
    'verification': dict_signature,
    }
    
json_rsp = utils.request_json(
    'GET',
    f'{global_var.URL}/check',
    json=data)
print('JSON结果:', json_rsp)

