from bili_global import API_LIVE
from json_rsp_ctrl import ZERO_ONLY_CTRL


class GuardRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f'{API_LIVE}/lottery/v1/Lottery/check_guard?roomid={real_roomid}'
        json_rsp = await user.bililive_session.request_json('GET', url, ctrl=ZERO_ONLY_CTRL)
        return json_rsp
    
    @staticmethod
    async def join(user, real_roomid, raffle_id):
        url = f"{API_LIVE}/lottery/v2/Lottery/join"
        data = {
            'roomid': real_roomid,
            'id': raffle_id,
            'type': 'guard',
            'csrf_token': user.dict_bili['csrf']
        }
        json_rsp = await user.bililive_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp
