"""这是主要的监控，每隔 20 分钟刷新一次房间号码，全覆盖所有监控
"""

import init_eventloop
import sys
import signal
import threading
import asyncio
from datetime import datetime
from itertools import zip_longest

import utils
import conf_loader
import notifier
import bili_statistics
from bili_console import BiliConsole
from user import User
from tasks.login import LoginTask
import tasks.utils
# 弹幕
from danmu.bili_danmu_monitor import DanmuRaffleMonitor
from danmu import raffle_handler


loop = asyncio.get_event_loop()

dict_user = conf_loader.read_user()
dict_bili = conf_loader.read_bili()
dict_ctrl = conf_loader.read_ctrl()
admin_privkey = conf_loader.read_key()

# user设置
users = []
# 有且仅有一个用户
assert len(dict_user['users']) == 1
for user_info in dict_user['users']:
    users.append(User(user_info, dict_bili))
notifier.init(users=users)

loop.run_until_complete(notifier.exec_task(LoginTask))

other_control = dict_ctrl['other_control']

START = dict_ctrl['other_control']['START']
END = dict_ctrl['other_control']['END']

bili_statistics.init(area_num=1, area_duplicated=False)
tasks.utils.init(
    key=admin_privkey,
    name=f'{START}-{END}V7.0.0b0',
    url=dict_ctrl['other_control']['post_office'])


async def fetch_roomid_periodic():
    list_realroomid = await notifier.exec_func(tasks.utils.UtilsTask.get_rooms_from_remote, START, END)
    if list_realroomid is None:
        print('中心分发系统错误，初始化失败')
        sys.exit(-1)
    print(list_realroomid[:5])
    monitors = []

    for i, room_id in zip_longest(range(END-START), list_realroomid):
        if room_id is None:
            room_id = 0
        monitor = DanmuRaffleMonitor(room_id, i)
        monitors.append(monitor)
        if not room_id:
            monitor.pause()

    for i, monitor in enumerate(monitors):
        if not i % 20:
            await asyncio.sleep(0.2)
        loop.create_task(monitor.run())

    while True:
        now = datetime.now()
        print(f'当前时间为 {now.hour:0>2}:{now.minute:0>2}:{now.second:0>2}')

        # 每个轮次，从中心处获取新房间 list_new_rooms，把当前的监控群(monitors)全部替换为新房间
        # 为了提高性能，仅会处理重启与 list_new_rooms 不同的监控
        if now.minute in (10, 30, 50) and now.second <= 35:
            print('到达设定时间，正在重新查看房间')

            # rooms请求会可能超出了中心房间分发服务器的房间容量，即实际获取到的比start-end的只少不多
            # 此时本机的多余的监控就休眠
            list_new_rooms = await notifier.exec_func(tasks.utils.UtilsTask.get_rooms_from_remote, START, END)

            # 只重启那些不同的，除了不同的还有缺少的房间，这时就暂停
            # 去重，不需要关心顺序;去0
            set_new_rooms = set(list_new_rooms)
            try:
                set_new_rooms.remove(0)
            except KeyError:
                pass

            set_common_rooms = set()  # 两者都有的房间

            list_unique_old_index = []  # 当前监控中的"多余"房间index
            for i, monitor in enumerate(monitors):
                room_id = monitor.room_id
                if room_id and room_id in set_new_rooms:
                    set_common_rooms.add(room_id)
                else:
                    list_unique_old_index.append(i)

            # list_new_rooms “多余”的房间
            set_unique_new_rooms = set_new_rooms - set_common_rooms

            print(f'监控重启的数目: 所需 monitor {len(set_unique_new_rooms)}, 可用 monitor {len(list_unique_old_index)}')

            # room_id为 0 的房间在后，这样会减少更改
            list_unique_old_index.sort(key=lambda item: monitors[item].room_id, reverse=True)

            for monitor_index, new_roomid in zip_longest(list_unique_old_index, set_unique_new_rooms):
                monitor = monitors[monitor_index]
                # 实际获取到的比start-end的只少不多
                if new_roomid is None:
                    if monitor.room_id:  # 只操作非0即可
                        monitor.pause()
                        await monitor.reset_roomid(0)
                else:
                    await monitor.reset_roomid(new_roomid)
                    monitor.resume()

            # 验证
            assert set(monitor.room_id for monitor in monitors if monitor.room_id) == set_new_rooms

            tasks.utils.update(latest_update_rooms_time=utils.curr_time())
            await asyncio.sleep(60)

        await asyncio.sleep(30)


# 初始化控制台
if sys.platform != 'linux' or signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:
    console_thread = threading.Thread(
        target=BiliConsole(loop).cmdloop)
    console_thread.start()
else:
    console_thread = None

other_tasks = [
    raffle_handler.run(),
    fetch_roomid_periodic()
]
if other_tasks:
    loop.run_until_complete(asyncio.wait(other_tasks))
loop.run_forever()
if console_thread is not None:
    console_thread.join()
