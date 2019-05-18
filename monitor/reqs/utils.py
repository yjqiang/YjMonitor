# 不具有任何意义,仅仅是常见func


class UtilsReq:
    @staticmethod
    async def get_rooms_from_remote(user, start, end):
        url = f'http://room.lc4t.cn:8000/dyn_rooms/{start}-{end}'
        json_rsp = await user.other_session.request_json('GET', url)
        return json_rsp

    @staticmethod
    async def fetch_rooms_from_bili(user, url, page_id):
        json_rsp = await user.other_session.request_json('GET', f'{url}{page_id}')
        return json_rsp

    @staticmethod
    async def send2yj_monitor(user, url, data):
        json_rsp = await user.other_session.request_json('POST', url, json=data)
        return json_rsp
