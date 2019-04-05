import rsa

import utils
import global_var


name = 'bbbn'

with open(f'{global_var.KEY_PATH}/admin_privkey.pem', 'rb') as f:
    admin_privkey = rsa.PrivateKey.load_pkcs1(f.read())


dict_signature = utils.make_signature(
    name,
    admin_privkey,
    need_name=True)


data = {
    'code': 0,
    'type': 'raffle',
    'data': {},
    'verification': dict_signature,
    }
    
json_rsp = utils.request_json(
    'GET',
    f'{global_var.URL}/check',
    json=data)
print('JSON结果:', json_rsp)

