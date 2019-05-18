import asyncio

from printer import info as print
from tasks.utils import UtilsTask
import conf_loader
import notifier
from tasks.guard_raffle_handler import GuardRafflJoinTask
from . import raffle_handler


class PollRoomChecker:
    def __init__(self):
        dic_roomid = conf_loader.read_roomid()
        self.static_rooms = dic_roomid['roomid']
        assert len(self.static_rooms) == len(set(self.static_rooms))

    async def refresh(self):
        print(f'正在刷新查看ONLINE房间')
        base_url = 'http://api.live.bilibili.com'
        urls = [
            f'{base_url}/room/v1/Area/getListByAreaID?areaId=0&sort=online&pageSize=40&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page=',
        ]
        roomlists = [await notifier.exec_func(UtilsTask.fetch_rooms_from_bili, urls[0])]
        for url in urls[1:]:
            await asyncio.sleep(7)
            roomlists.append(await notifier.exec_func(UtilsTask.fetch_rooms_from_bili, url))
        print(f'结束本轮刷新查看ONLINE房间')
        dyn_rooms = []
        for rooms in roomlists:
            for room in rooms:
                if room and room not in self.static_rooms and room not in dyn_rooms:
                    dyn_rooms.append(room)

        print(f'POLL ROOMS 收获了{len(dyn_rooms)}个房间')
        for room_id in dyn_rooms:
            raffle_handler.exec_at_once(GuardRafflJoinTask, room_id, 1)
            await asyncio.sleep(0.1)

    async def run(self):
        while True:
            await self.refresh()
            await asyncio.sleep(20)
