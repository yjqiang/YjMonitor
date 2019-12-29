from bili_global import API_LIVE
from json_rsp_ctrl import ZERO_ONLY_CTRL


class LotteriesRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f'{API_LIVE}/xlive/lottery-interface/v1/lottery/Check?roomid={real_roomid}'
        json_rsp = await user.bililive_session.request_json('GET', url, ctrl=ZERO_ONLY_CTRL)
        return json_rsp
