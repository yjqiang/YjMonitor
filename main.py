from danmu import YjCheckMonitor, YjMonitorServer
from rafflehandler import Rafflehandler
import asyncio
from printer import Printer
from statistics import Statistics
from bilibili import bilibili
from configloader import ConfigLoader
from datetime import datetime
import threading
import os
import login
import bili_console
import sys
import utils
import aiohttp


if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

fileDir = os.path.dirname(os.path.realpath('__file__'))

ConfigLoader(fileDir)
START = ConfigLoader().dic_user['other_control']['START']
END = ConfigLoader().dic_user['other_control']['END']
default_monitor_roomid = ConfigLoader().dic_user['other_control']['default_monitor_roomid']
danmusender = utils.DanmuSender(default_monitor_roomid)

# print('Hello world.')
printer = Printer()
bilibili()
login.login()
Statistics()

rafflehandler = Rafflehandler()
var_console = bili_console.Biliconsole(loop)


console_thread = threading.Thread(target=var_console.cmdloop)

console_thread.start()

async def fetch_roomid_periodic():
    client_session = None
    list_realroomid = await utils.get_rooms_from_remote(START, END)
    if list_realroomid is None:
        print('中心分发系统错误，初始化失败')
        sys.exit(-1)
    print(list_realroomid[:5])
    list_raffle_connection = []
    for i, room in enumerate(list_realroomid):
        if not (i % 500):
            client_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None))
        list_raffle_connection.append(YjMonitorServer(room, i, client_session))
    for i in list_raffle_connection:
        asyncio.ensure_future(i.run_forever())
    
    asyncio.ensure_future(YjCheckMonitor(default_monitor_roomid, -1, client_session).run_forever())
    while True:
        now = datetime.now()
        print(f'当前时间为 {now.hour:0>2}:{now.minute:0>2}:{now.second:0>2}')
        if (now.minute == 10 or now.minute == 30 or now.minute == 50) and now.second <= 35:
            print('到达设定时间，正在重新查看房间')
            old_rooms = [room.room_id for room in list_raffle_connection]
            new_rooms = await utils.get_rooms_from_remote(START, END)
            if new_rooms is None:
                danmusender.set_refresh_ok(False)
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
            print(len(set_unique_new_rooms), len(list_unique_old_index))
            list_unique_connection = [list_raffle_connection[i] for i in list_unique_old_index]
            for connection, roomid in zip(list_unique_connection, set_unique_new_rooms):
                await connection.reconnect(roomid)
            danmusender.set_refresh_ok(True)
                
            await asyncio.sleep(60)
        
        await asyncio.sleep(30)
tasks = [
    fetch_roomid_periodic(),
    danmusender.run()
    # bili_timer.run(),

]
try:
    loop.run_until_complete(asyncio.wait(tasks))
except KeyboardInterrupt:
    # print(sys.exc_info()[0], sys.exc_info()[1])
    if ConfigLoader().dic_user['other_control']['keep-login']:
        pass
    else:
        response = login.logout()

console_thread.join()

loop.close()
