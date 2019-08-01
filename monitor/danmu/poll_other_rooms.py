import asyncio
from itertools import zip_longest

from printer import info as print
from tasks.utils import UtilsTask
import conf_loader
import notifier
from tasks.guard_raffle_handler import GuardRafflJoinTask
from . import raffle_handler


class PollOtherRoomChecker:
    def __init__(self, start: int, end: int):
        self.urls = []
        self.start = start
        self.end = end
        dic_roomid = conf_loader.read_roomid()
        list_static_rooms = dic_roomid['roomid']
        self.static_rooms = set(list_static_rooms)
        assert len(list_static_rooms) == len(self.static_rooms)
        self.reset_max_rooms_num()

    def reset_max_rooms_num(self):  # 大约的数据
        base_url = 'http://api.live.bilibili.com'
        urls = [
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?type=master_realtime_hour&type_id=areaid_realtime_hour&page_size=12&area_id=',
                8
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=0&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=1&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=2&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=3&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=4&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=5&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=6&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=7&page=',
                5
            )

        ]
        self.urls = urls

    async def refresh(self):
        print(f'正在刷新查看ONLINE房间')
        roomlists = [await notifier.exec_func(
            UtilsTask.fetch_rooms_from_rank, *(self.urls[0]))]
        for url, pages_num in self.urls[1:]:
            await asyncio.sleep(0.1)
            roomlists.append(await notifier.exec_func(
                UtilsTask.fetch_rooms_from_rank, url, pages_num))
        print(f'结束本轮刷新查看ONLINE房间')
        dyn_rooms = []
        for rooms in zip_longest(*roomlists):  # 这里是为了保持优先级
            for room in rooms:
                if room and room not in self.static_rooms and room not in dyn_rooms:
                    dyn_rooms.append(room)
        print(f'POLL ROOMS 收获了{len(dyn_rooms)}个房间')
        dyn_rooms = dyn_rooms[self.start: self.end]
        print(f'POLL ROOMS 截取了{len(dyn_rooms)}个房间')
        for room_id in dyn_rooms:
            raffle_handler.exec_at_once(GuardRafflJoinTask, room_id, 1)
            await asyncio.sleep(0.035)

    async def run(self):
        while True:
            await self.refresh()
            await asyncio.sleep(7)
