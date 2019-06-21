"""补足协同监控。从 Yj 获取到已经做掉的数据，保证不会重复
"""

import init_eventloop
import asyncio
import json
from typing import List
from itertools import zip_longest
import sys
import signal
import base64
import threading
import socket

import rsa
from aiohttp import web
from aiojobs.aiohttp import atomic, setup

import utils
from bili_console import BiliConsole
import json_req_exceptions
from danmu.bili_online_danmu_monitor import DanmuRaffleMonitor
import conf_loader
from danmu import raffle_handler
import notifier
import bili_statistics
from user import User
from tasks.login import LoginTask
import tasks.utils


MAX = 3300
loop = asyncio.get_event_loop()

dict_user = conf_loader.read_user()
dict_bili = conf_loader.read_bili()
dict_ctrl = conf_loader.read_ctrl()
admin_privkey = conf_loader.read_key()
admin_pubkey = conf_loader.read_pubkey()

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
    name=f'RDISTRIBUTEDV1.0b2',
    url=dict_ctrl['other_control']['post_office'])


class MonitorsCtrlCenter:
    def __init__(self):
        self.monitors = []
        self.loop = asyncio.get_event_loop()
        self.lock = asyncio.Lock()

        for i in range(MAX):
            monitor = DanmuRaffleMonitor(0, i)
            monitor.pause()
            self.monitors.append(monitor)

        for i, monitor in enumerate(self.monitors):
            self.loop.create_task(monitor.run())

        self.errs = []

    def get_roomids_monitored(self) -> List[int]:
        roomids_monitored = []
        for i, monitor in enumerate(self.monitors):
            room_id = monitor.room_id
            if not monitor.paused and room_id:
                roomids_monitored.append(room_id)
        return roomids_monitored

    async def add_new_roomids(self, room_ids: List[int]) -> float:
        async with self.lock:
            set_new_rooms = set(room_ids)
            set_common_rooms = set()
            list_unique_old_index = []  # 过期（下线）的直播间
            for i, monitor in enumerate(self.monitors):
                room_id = monitor.room_id
                if not monitor.paused and room_id and room_id in set_new_rooms:
                    set_common_rooms.add(room_id)
                elif monitor.paused:
                    list_unique_old_index.append(i)

            set_unique_new_rooms = set_new_rooms - set_common_rooms

            print('监控重启的数目', len(set_unique_new_rooms), len(list_unique_old_index))
            err = []
            for monitor_index, new_roomid in zip_longest(list_unique_old_index, set_unique_new_rooms):
                if monitor_index is not None:
                    monitor = self.monitors[monitor_index]
                    if new_roomid is None:
                        pass  # list_unique_old_index 肯定都是pause的了
                    else:
                        loop.create_task(monitor.reset_roomid(new_roomid))
                        monitor.resume()
                else:  # 新房间很多，老房间不够用，需要扩充
                    # list_unique_old_index先到了头，那么set_unique_new_rooms一定还有多余，一定非 None
                    err.append(new_roomid)
            if err:
                self.errs.append({'time': utils.curr_time(), 'err_new_roomids': err})
                self.errs = err[-20:]

            if set_unique_new_rooms:
                return len(set_unique_new_rooms) / 100 * 1.2 + 5
            return 0


monitors_ctrl_center = MonitorsCtrlCenter()


# 验证json请求签名正确性
async def _verify_json_req(request, pubkey: rsa.PublicKey) -> tuple:
    """
    {
        'code': 0,
        'type': 'raffle',
        'verification':
            {'signature': f'Hello World. This is {name} at {time}.', 'name': name, 'time': int},
        'data': {...}
    }
    """
    try:
        json_data = await request.json()
    except json.JSONDecodeError:
        raise json_req_exceptions.ReqFormatError()
    except:
        raise json_req_exceptions.OtherError()

    if 'verification' in json_data and 'data' in json_data:
        verification = json_data['verification']
        if isinstance(verification, dict) and 'signature' in verification and 'time' in verification:
            try:
                cur_time0 = int(verification['time'])
                cur_time1 = utils.curr_time()
                if -1200 <= cur_time0 - cur_time1 <= 1200:
                    # 缺省name表示为super_admin，需要使用超管签名校验，其他的用管理员校验
                    name = verification.get("name", "super_admin")
                    text = f'Hello World. This is {name} at {cur_time0}.'.encode('utf-8')
                    rsa.verify(
                        text,
                        base64.b64decode(verification['signature'].encode('utf8')),
                        pubkey)
                    data = json_data['data']
                    if isinstance(data, dict):
                        return name, data
                    raise json_req_exceptions.DataError
                else:
                    raise json_req_exceptions.TimeError
            except rsa.VerificationError:
                raise json_req_exceptions.VerificationError
            except json_req_exceptions.JsonReqError:
                raise
            except:
                raise json_req_exceptions.DataError
    raise json_req_exceptions.DataError


@atomic
async def check_handler(_: web.Request):
    roomids_monitored = monitors_ctrl_center.get_roomids_monitored()
    return web.json_response({
        'code': 0,
        'data': {
            'roomids_monitored': roomids_monitored,
            'err': monitors_ctrl_center.errs,
            'remain_roomids': MAX - len(roomids_monitored)
        }})


@atomic
async def add_new_roomids_handler(request: web.Request):
    try:
        _, data = await _verify_json_req(request, admin_pubkey)
        sleep_time = await monitors_ctrl_center.add_new_roomids(data['new_roomids'])
        return web.json_response({
            'code': 0,
            'data': {
                'sleep_time': sleep_time,
            }})
    except json_req_exceptions.JsonReqError as e:
        return web.json_response(e.RSP_SUGGESTED)
    except:
        return web.json_response(json_req_exceptions.DataError.RSP_SUGGESTED)

if sys.platform != 'linux' or signal.getsignal(signal.SIGHUP) == signal.SIG_DFL:
    console_thread = threading.Thread(
        target=BiliConsole(loop).cmdloop)
    console_thread.start()
else:
    console_thread = None

loop.create_task(raffle_handler.run())

app = web.Application()
setup(app)
app.router.add_route('GET', '/check', check_handler)
app.router.add_route('POST', '/add_new_roomids', add_new_roomids_handler)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.connect(("114.114.114.114", 80))
    print('本机 IP 为', s.getsockname()[0])

web.run_app(app, port=9001)
loop.run_forever()
if console_thread is not None:
    console_thread.join()
