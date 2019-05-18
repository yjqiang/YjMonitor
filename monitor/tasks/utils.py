import asyncio

import printer
import utils
from reqs.utils import UtilsReq


class UtilsTask:
    @staticmethod
    async def get_rooms_from_remote(user, start, end):
        json_rsp = await user.req_s(UtilsReq.get_rooms_from_remote, user, start, end)
        # print(json_rsp)
        if json_rsp is not None:
            rooms = json_rsp['roomid']
            printer.info(f'本次刷新房间总计获取{len(rooms)}, 请求起止指针{start}-{end}')
        else:
            printer.info(f'本次刷新房间总计获取 None, 请求起止指针{start}-{end}')
            rooms = None
        return rooms

    @staticmethod
    async def fetch_rooms_from_bili(user, url):
        rooms = []
        for page in range(1, 250):
            if not (page % 20):
                print(f'{url}截止第{page}页，获取{len(rooms)}个房间(可能重复)')

            json_rsp = await user.req_s(UtilsReq.fetch_rooms_from_bili, user, url, page)
            data = json_rsp['data']

            if not data or max(room['online'] for room in data) <= 100:
                print(f'{url}截止结束页（第{page}页），获取{len(rooms)}个房间(可能重复)')
                break
            for room in data:
                rooms.append(int(room['roomid']))
            await asyncio.sleep(0.15)

        print('去重之前', len(rooms))
        unique_rooms = []
        for room_id in rooms:
            if room_id not in unique_rooms:
                unique_rooms.append(room_id)
        print('去重之后', len(unique_rooms))
        return unique_rooms

    @staticmethod
    async def send2yj_monitor(user, *args):
        await send2yj_monitor(user, *args)


class YjMonitorPoster:
    def __init__(self):
        self.privkey = None
        self.url = None
        self.name = None
        self.latest_update_rooms_time = 0

    def init(self, key, url, name):
        self.privkey = key
        self.url = url
        self.name = name

    def update(self, latest_update_rooms_time: int):
        self.latest_update_rooms_time = latest_update_rooms_time

    async def send2yj_monitor(self, user, raffle_data: dict):
        dict_signature = utils.make_signature(
            self.name,
            self.privkey,
            need_name=True)
        print('raffle_data', raffle_data, self.latest_update_rooms_time)
        data = {
            'code': 0,
            'type': 'raffle',
            'data': {
                **raffle_data,
                'latest_update_rooms_time': self.latest_update_rooms_time
            },
            'verification': dict_signature
        }
        json_rsp = await user.req_s(UtilsReq.send2yj_monitor, user, self.url, data)
        if json_rsp['code']:
            user.warn(json_rsp)

        user.info(f'已推送{raffle_data.get("raffle_id")},结果反馈为: {json_rsp}')


var_yjmonitor_poster = YjMonitorPoster()


def init(*args, **kwargs):
    var_yjmonitor_poster.init(*args, **kwargs)


async def send2yj_monitor(user, raffle_data: dict):
    await var_yjmonitor_poster.send2yj_monitor(user, raffle_data)


def update(*args, **kwargs):
    var_yjmonitor_poster.update(*args, **kwargs)
