import base64

import rsa

import utils
import global_var


max_users = 1  # 此key最大同时在线用户数量
name = 'super_admin'
available_days = 0

with open(f'{global_var.KEY_PATH}/super_admin_privkey.pem', 'rb') as f:
    super_admin_privkey = rsa.PrivateKey.load_pkcs1(f.read())

dict_signature = utils.make_signature(
    name,
    super_admin_privkey,
    need_name=False)

data = {
    'code': 0,
    'type': 'create_key',
    'data': {
        'max_users': max_users,
        'available_days': available_days
        },
    'verification': dict_signature
    }

json_rsp = utils.request_json(
    'GET',
    f'{global_var.URL}/create_key',
    json=data)

print('JSON结果:', json_rsp)
if not json_rsp['code']:
    encrypted_key = json_rsp['data']['encrypted_key']
    bytes_orig_key = rsa.decrypt(
        base64.b64decode(encrypted_key.encode('utf8')),
        super_admin_privkey
        ).decode('utf8')
    print('KEY(16位)解密结果为:', bytes_orig_key)
    

