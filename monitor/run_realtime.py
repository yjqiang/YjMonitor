"""快速搜寻开播房间，筛除自带的 conf 里面的静态房间，几乎实时（本质轮询）
"""

import init_eventloop
import sys
import signal
import threading
import asyncio
from itertools import zip_longest
from typing import List

import conf_loader
import notifier
import bili_statistics
from bili_console import BiliConsole
from user import User
from tasks.login import LoginTask
import tasks.utils
# 弹幕
from danmu import raffle_handler
from danmu.bili_online_danmu_monitor import DanmuRaffleMonitor


loop = asyncio.get_event_loop()

dict_user = conf_loader.read_user()
dict_bili = conf_loader.read_bili()
dict_ctrl = conf_loader.read_ctrl()
admin_privkey = conf_loader.read_key()
dic_roomid = conf_loader.read_roomid()
static_rooms = dic_roomid['roomid']

# user设置
users = []
assert len(dict_user['users']) == 1
for user_info in dict_user['users']:
    users.append(User(user_info, dict_bili))
notifier.init(users=users)

loop.run_until_complete(notifier.exec_task(LoginTask))

other_control = dict_ctrl['other_control']
bili_statistics.init(area_num=1, area_duplicated=False)
tasks.utils.init(
    key=admin_privkey,
    name=f'REALTIMEV6.0b0',
    url=dict_ctrl['other_control']['post_office'])


async def refresh_online_roomid():
    print(f'正在刷新查看ONLINE房间')
    base_url = 'http://api.live.bilibili.com'
    urls = [
        f'{base_url}/room/v1/Area/getListByAreaID?areaId=0&sort=online&pageSize=100&page=',
        f'{base_url}/room/v1/room/get_user_recommend?page_size=100&page=',
    ]
    roomlists = [await notifier.exec_func(tasks.utils.UtilsTask.fetch_rooms_from_bili, urls[0])]
    for url in urls[1:]:
        await asyncio.sleep(3)
        roomlists.append(await notifier.exec_func(tasks.utils.UtilsTask.fetch_rooms_from_bili, url))
    print(f'结束本轮刷新查看ONLINE房间')
    dyn_rooms = []
    for rooms in zip_longest(*roomlists):  # 这里是为了保持优先级
        for room in rooms:
            if room and room not in static_rooms and room not in dyn_rooms:
                dyn_rooms.append(room)
    print(f'POLL ROOMS 收获了{len(dyn_rooms)}个房间')
    return dyn_rooms


async def add_onlinerooms_monitor():
    monitors: List[DanmuRaffleMonitor] = []
    area_id = 0
    while True:
        list_new_rooms = await refresh_online_roomid()

        set_new_rooms = set(list_new_rooms)
        set_common_rooms = set()
        list_unique_old_index = []  # 过期（下线）的直播间
        for i, monitor in enumerate(monitors):
            room_id = monitor.room_id
            if room_id and room_id in set_new_rooms:
                set_common_rooms.add(room_id)
            elif monitor.paused:
                list_unique_old_index.append(i)

        set_unique_new_rooms = set_new_rooms - set_common_rooms

        print('监控重启的数目', len(set_unique_new_rooms), len(list_unique_old_index))

        for monitor_index, new_roomid in zip_longest(list_unique_old_index, set_unique_new_rooms):
            if monitor_index is not None:
                monitor = monitors[monitor_index]
                if new_roomid is None:
                    pass  # list_unique_old_index 肯定都是pause的了
                else:
                    await monitor.reset_roomid(new_roomid)
                    monitor.resume()
            else:  # 新房间很多，老房间不够用，需要扩充
                # list_unique_old_index先到了头，那么set_unique_new_rooms一定还有多余，一定非 None
                monitor = DanmuRaffleMonitor(new_roomid, area_id)
                loop.create_task(monitor.run())
                if not area_id % 20:
                    await asyncio.sleep(0.2)
                area_id += 1
                monitors.append(monitor)


# 初始化控制台
if sys.platform != 'linux' or signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:
    console_thread = threading.Thread(
        target=BiliConsole(loop).cmdloop)
    console_thread.start()
else:
    console_thread = None

other_tasks = [
    raffle_handler.run(),
    add_onlinerooms_monitor()
]
if other_tasks:
    loop.run_until_complete(asyncio.wait(other_tasks))
loop.run_forever()
if console_thread is not None:
    console_thread.join()
