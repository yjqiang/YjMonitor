import connect
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


if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

fileDir = os.path.dirname(os.path.realpath('__file__'))

ConfigLoader(fileDir)
START = ConfigLoader().dic_user['other_control']['START']
END = ConfigLoader().dic_user['other_control']['END']
danmusender = utils.DanmuSender(ConfigLoader().dic_user['other_control']['default_monitor_roomid'])

# print('Hello world.')
printer = Printer()
bilibili()
login.login()
Statistics()


list_realroomid = None
# list_realroomid = ConfigLoader().dic_roomid['roomid']
list_realroomid = loop.run_until_complete(asyncio.gather(utils.getRecommend()))[0]
print(list_realroomid[:5])

rafflehandler = Rafflehandler()
var_console = bili_console.Biliconsole(loop)


list_raffle_connection = [connect.RaffleConnect(i - START + 1, list_realroomid[i]) for i in range(START, END)]
list_raffle_connection_task = [i.run() for i in list_raffle_connection]

yjchecking = connect.RaffleConnect(-1, None)

console_thread = threading.Thread(target=var_console.cmdloop)

console_thread.start()

async def fetch_roomid_periodic():
    while True:
        now = datetime.now()
        print(f'当前时间为 {now.hour:0>2}:{now.minute:0>2}:{now.second:0>2}')
        if (now.minute == 15 or now.minute == 45) and now.second <= 35:
            print('到达设定时间，正在重新查看房间')
            list_realroomid = await utils.getRecommend()
            for connection, roomid in zip(list_raffle_connection, list_realroomid[START: END]):
                await connection.reconnect(roomid)
        
        await asyncio.sleep(30)
tasks = [
    fetch_roomid_periodic(),
    yjchecking.run(),
    danmusender.run()
    # bili_timer.run(),

]
try:
    loop.run_until_complete(asyncio.wait(tasks + list_raffle_connection_task))
except KeyboardInterrupt:
    # print(sys.exc_info()[0], sys.exc_info()[1])
    if ConfigLoader().dic_user['other_control']['keep-login']:
        pass
    else:
        response = login.logout()

console_thread.join()

loop.close()
