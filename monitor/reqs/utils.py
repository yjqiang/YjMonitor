# 不具有任何意义,仅仅是常见func

import time
from random import randint
from bili_global import API_LIVE


class UtilsReq:
    @staticmethod
    def randomint():
        return ''.join(str(randint(0, 9)) for _ in range(17))
        
    @staticmethod
    def curr_time():
        return int(time.time())

    @staticmethod
    async def get_rooms_from_remote(user, start, end):
        url = f'http://room.lc4t.cn:8000/dyn_rooms/{start}-{end}'
        json_rsp = await user.other_session.request_json('GET', url, is_none_allowed=True)
        return json_rsp
        
    @staticmethod
    async def send_danmu(user, msg, room_id):
        url = f'{API_LIVE}/msg/send'
        data = {
            'color': '16777215',
            'fontsize': '25',
            'mode': '1',
            'msg': msg,
            'rnd': '0',
            'roomid': int(room_id),
            'csrf_token': user.dict_bili['csrf'],
            'csrf': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp
