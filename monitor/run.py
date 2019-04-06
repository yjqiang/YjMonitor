import init_eventloop
import sys
import signal
import threading
import asyncio
from os import path
from datetime import datetime
from danmu import YjMonitorServer, YjCheckMonitor
import conf_loader
import notifier
import raffle_handler
import bili_statistics
from bili_console import Biliconsole
import printer
from user import User
from tasks.login import LoginTask
from tasks.utils import UtilsTask, set_refresh_ok, set_checkmsg, set_roomid, set_values

root_path = path.dirname(path.realpath(__file__))
conf_loader.set_path(root_path)

loop = asyncio.get_event_loop()
        
dict_user = conf_loader.read_user()
dict_bili = conf_loader.read_bili()
dict_color = conf_loader.read_color()
dict_ctrl = conf_loader.read_ctrl()
admin_privkey = conf_loader.read_key()
printer.init_config(dict_color, dict_ctrl['print_control']['danmu'])
area_ids = dict_ctrl['other_control']['area_ids']

users = []
task_control = dict_ctrl['task_control']
for i, user_info in enumerate(dict_user['users']):
    users.append(User(i, user_info, task_control, dict_bili))
notifier.set_values(loop)
notifier.set_users(users)

bili_statistics.init_area_num(len(area_ids))
    
loop.run_until_complete(notifier.exec_func(-2, LoginTask.handle_login_status))

# users[1].fall_in_jail()
yj_danmu_roomid = dict_ctrl['other_control']['raffle_minitor_roomid']
START = dict_ctrl['other_control']['START']
END = dict_ctrl['other_control']['END']
set_checkmsg(f'{int(START/100)}阝阝{int(END/100)}')
set_roomid(yj_danmu_roomid)
set_values(
    key=admin_privkey,
    name=f'{START}-{END}',
    url=dict_ctrl['other_control']['post_office'])


async def fetch_roomid_periodic():
    list_realroomid = await notifier.exec_func(0, UtilsTask.get_rooms_from_remote, START, END)
    if list_realroomid is None:
        print('中心分发系统错误，初始化失败')
        sys.exit(-1)
    print(list_realroomid[:5])
    list_raffle_connection = []
    for i, room in enumerate(list_realroomid):
        list_raffle_connection.append(YjMonitorServer(room, i))
    for i in list_raffle_connection:
        asyncio.ensure_future(i.run_forever())

    if yj_danmu_roomid:
        asyncio.ensure_future(YjCheckMonitor(yj_danmu_roomid, -1, f'check{START}-{END}').run_forever())
    while True:
        now = datetime.now()
        print(f'当前时间为 {now.hour:0>2}:{now.minute:0>2}:{now.second:0>2}')
        if (now.minute == 10 or now.minute == 30 or now.minute == 50) and now.second <= 35:
            print('到达设定时间，正在重新查看房间')
            old_rooms = [room.room_id for room in list_raffle_connection]
            new_rooms = await notifier.exec_func(0, UtilsTask.get_rooms_from_remote, START, END)
            if new_rooms is None:
                set_refresh_ok(False)
                await asyncio.sleep(60)
                continue
            # 只重启那些不同的
            set_new_rooms = set(new_rooms)
            set_dup_new_rooms = set()
            list_unique_old_index = []
            for i, value in enumerate(old_rooms):
                if value in set_new_rooms:
                    set_dup_new_rooms.add(value)
                else:
                    list_unique_old_index.append(i)
            set_unique_new_rooms = set_new_rooms - set_dup_new_rooms
            print('监控重启的数目', len(set_unique_new_rooms), len(list_unique_old_index))
            assert len(set_unique_new_rooms) == len(list_unique_old_index)
            list_unique_connection = [list_raffle_connection[i] for i in list_unique_old_index]
            for connection, roomid in zip(list_unique_connection, set_unique_new_rooms):
                await connection.reset_roomid(roomid)
            set_refresh_ok(True)

            await asyncio.sleep(60)

        await asyncio.sleep(30)


if sys.platform != 'linux' or signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:
    console_thread = threading.Thread(target=Biliconsole(loop).cmdloop)
    console_thread.start()
else:
    console_thread = None


other_tasks = [
    raffle_handler.run(),
    fetch_roomid_periodic()
    # SubstanceRaffleMonitor().run()
    ]

loop.run_until_complete(asyncio.wait(other_tasks))
if console_thread is not None:
    console_thread.join()

