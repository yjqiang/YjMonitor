"""补足监控。轮询房间，筛除自带的 conf 里面的静态房间，同时需要从 Yj 获取到已经做掉的数据，保证不会重复
"""

import init_eventloop
import sys
import signal
import threading
import asyncio

import conf_loader
import notifier
import bili_statistics
from bili_console import BiliConsole
from user import User
from tasks.login import LoginTask
import tasks.utils
# 弹幕
from danmu import raffle_handler
from danmu.yj_monitor import TcpYjMonitorClient
from poll.poll_rooms0 import PollRoomChecker


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

START = 0
END = 1250

bili_statistics.init(area_num=1, area_duplicated=False)
tasks.utils.init(
    key=admin_privkey,
    name=f'{START}-{END}POLL0V7.2.0b0',
    url=dict_ctrl['other_control']['post_office'])


async def fetch_roomid_periodic():
    yjmonitor_tcp_addr = other_control['yjmonitor_tcp_addr']
    yjmonitor_tcp_key = other_control['yjmonitor_tcp_key']
    monitor = TcpYjMonitorClient(
        key=yjmonitor_tcp_key,
        url=yjmonitor_tcp_addr,
        area_id=0)
    loop.create_task(monitor.run())
    await PollRoomChecker(START, END).run()


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
