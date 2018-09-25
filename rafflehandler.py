from bilibili import bilibili
from statistics import Statistics
from configloader import ConfigLoader
import utils
import asyncio
import time
import string


def CurrentTime():
    currenttime = int(time.time())
    return currenttime


class Rafflehandler:
    __slots__ = ('list_raffle_id')
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Rafflehandler, cls).__new__(cls, *args, **kw)
            cls.instance.list_raffle_id = []
        return cls.instance

    @staticmethod
    def Put2Queue(value, func):
        # print('welcome to appending')
        asyncio.ensure_future(func(*value))
        # Rafflehandler.instance.queue_raffle.put_nowait((value, func))
        # print('appended')
        return

    def add2raffle_id(self, raffle_id):
        self.list_raffle_id.append(raffle_id)
        if len(self.list_raffle_id) > 150:
            # print(self.list_raffle_id)
            del self.list_raffle_id[:75]
            # print(self.list_raffle_id)

    def check_duplicate(self, raffle_id):
        return (raffle_id in self.list_raffle_id)


def dec2base(int_x, base):
    digs = string.digits + string.ascii_letters
    if int_x < 0:
        sign = -1
    elif int_x == 0:
        return digs[0]
    else:
        sign = 1

    int_x *= sign
    digits = []

    while int_x:
        digits.append(digs[int(int_x % base)])
        int_x = int(int_x / base)

    if sign < 0:
        digits.append('-')

    digits.reverse()

    return ''.join(digits)

async def handle_1_room_storm(target, roomid, stormid):
    result = await utils.enter_room(roomid)
    if result:
        if not Rafflehandler().check_duplicate(stormid):
            Rafflehandler().add2raffle_id(stormid)
            stormid = dec2base(int(stormid), 62)
            roomid = dec2base(int(roomid), 62)
            await utils.send_danmu_msg_web(f'{roomid}~{stormid}', target)

async def handle_1_room_check(target):
    START = ConfigLoader().dic_user['other_control']['START']
    END = ConfigLoader().dic_user['other_control']['END']
    await utils.send_danmu_msg_web(f'{START}={END} v1.1', target)

async def handle_1_room_guard(target, roomid):
    result = await utils.enter_room(roomid)
    if result:
        for i in range(20):
            json_response1 = await bilibili.get_giftlist_of_guard(roomid)
            # print(json_response1)
            if not json_response1['data']:
                await asyncio.sleep(1)
            else:
                break
        if not json_response1['data']:
            print(f'{roomid}没有guard或者guard已经领取')
            return
        list_available_raffleid = []
        for j in json_response1['data']:
            print('获取到编号', j['id'])
            id = j['id']
            if not Rafflehandler().check_duplicate(id):
                Rafflehandler().add2raffle_id(id)
                id = dec2base(int(id), 62)
                list_available_raffleid.append(id)
        roomid = dec2base(int(roomid), 62)
        for raffleid in list_available_raffleid:
            await utils.send_danmu_msg_web(f'{roomid}+{raffleid}', target)
