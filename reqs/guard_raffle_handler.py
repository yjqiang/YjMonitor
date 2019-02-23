from bili_global import API_LIVE


class GuardRaffleHandlerReq:
    @staticmethod
    async def check(user, real_roomid):
        url = f'{API_LIVE}/lottery/v1/Lottery/check_guard?roomid={real_roomid}'
        json_rsp = await user.bililive_session.request_json('GET', url, headers=user.dict_bili['pcheaders'])
        return json_rsp
