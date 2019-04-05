import rsa

import utils
import global_var


name = 'bbbn'  # 名字用于统计是否poster还在线
data = {'room_id': 0, 'raffle_id': 133, 'raffle_type': 'storm'}

with open(f'{global_var.KEY_PATH}/admin_privkey.pem', 'rb') as f:
    admin_privkey = rsa.PrivateKey.load_pkcs1(f.read())

dict_signature = utils.make_signature(
    name,
    admin_privkey,
    need_name=True)


data = {
    'code': 0,
    'type': 'raffle',
    'data': data,
    'verification': dict_signature,
    }
    
json_rsp = utils.request_json(
    'POST',
    f'{global_var.URL}/post_raffle',
    json=data)
print('JSON结果:', json_rsp)

