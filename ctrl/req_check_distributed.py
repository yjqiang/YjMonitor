import utils


distributed_clients = [
    'http://127.0.0.1:9001',
    'http://127.0.0.1:9001',
    'http://127.0.0.1:9001'
]

center_clients = 'http://127.0.0.1:9000'

sum_online_rooms_num = 0
max_rooms_num = 0

for client in distributed_clients:
    data = utils.request_json(
        'GET',
        f'{client}/check')['data']
    online_rooms_num = len(data['roomids_monitored'])
    sum_online_rooms_num += online_rooms_num
    max_rooms_num += online_rooms_num + data['remain_roomids']
    
    
print('sum_online_rooms_num', sum_online_rooms_num)
print('max_rooms_num', max_rooms_num)
print('center_clients', utils.request_json('GET', center_clients))

