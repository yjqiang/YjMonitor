import asyncio
from itertools import zip_longest

from printer import info as print
from tasks.utils import UtilsTask
import conf_loader
import notifier
from tasks.guard_raffle_handler import GuardRafflJoinTask
from . import raffle_handler


class PollRoomChecker:
    def __init__(self, start: int, end: int):
        self.urls = []
        self.start = start
        self.end = end
        dic_roomid = conf_loader.read_roomid()
        list_static_rooms = dic_roomid['roomid']
        self.static_rooms = set(list_static_rooms)
        assert len(list_static_rooms) == len(self.static_rooms)
        self.reset_max_rooms_num(self.end, -1)

    def reset_max_rooms_num(self, num: int, url_index: int):  # 大约的数据
        base_url = 'http://api.live.bilibili.com'

        urls = [
            f'{base_url}/room/v1/Area/getListByAreaID?areaId=0&sort=online&pageSize={max(200, int(num/40))}&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page_size=100&page=',
        ]
        if url_index == -1:
            self.urls = urls
        else:
            self.urls = [urls[url_index]]

    async def refresh(self):
        print(f'正在刷新查看ONLINE房间')
        roomlists = [await notifier.exec_func(
            UtilsTask.fetch_rooms_from_bili, self.urls[0], self.end, self.static_rooms)]
        for url in self.urls[1:]:
            await asyncio.sleep(4)
            roomlists.append(await notifier.exec_func(
                UtilsTask.fetch_rooms_from_bili, url, self.end, self.static_rooms))
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
