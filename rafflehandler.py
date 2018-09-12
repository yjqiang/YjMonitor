from bilibili import bilibili
from statistics import Statistics
import utils
import asyncio
import time


def CurrentTime():
    currenttime = int(time.time())
    return currenttime


class Rafflehandler:
    __slots__ = ('queue_raffle', 'list_raffle_id')
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Rafflehandler, cls).__new__(cls, *args, **kw)
            cls.instance.queue_raffle = asyncio.Queue()
            cls.instance.list_raffle_id = []
        return cls.instance

    async def run(self):
        while True:
            raffle = await self.queue_raffle.get()
            await asyncio.sleep(0.5)
            list_raffle0 = [self.queue_raffle.get_nowait() for i in range(self.queue_raffle.qsize())]
            list_raffle0.append(raffle)
            list_raffle = list(set(list_raffle0))

            # print('过滤完毕')
            # if len(list_raffle) != len(list_raffle0):
            # print('过滤机制起作用')

            tasklist = []
            for i in list_raffle:
                i = list(i)
                i[0] = list(i[0])
                for j in range(len(i[0])):
                    if isinstance(i[0][j], tuple):
                        # print('检测')
                        # i[0] = list(i[0])
                        i[0][j] = await i[0][j][1](*(i[0][j][0]))
                # print(i)
                task = asyncio.ensure_future(i[1](*i[0]))
                tasklist.append(task)

            # await asyncio.wait(tasklist, return_when=asyncio.ALL_COMPLETED)

    @staticmethod
    def Put2Queue(value, func):
        # print('welcome to appending')
        Rafflehandler.instance.queue_raffle.put_nowait((value, func))
        # print('appended')
        return

    @staticmethod
    async def Put2Queue_wait(value, func):
        # print('welcome to appending')
        await Rafflehandler.instance.queue_raffle.put((value, func))
        # print('appended')
        return

    @staticmethod
    def getlist():
        print('目前TV任务队列状况', Rafflehandler.instance.queue_raffle.qsize())

    def add2raffle_id(self, raffle_id):
        self.list_raffle_id.append(raffle_id)
        if len(self.list_raffle_id) > 150:
            # print(self.list_raffle_id)
            del self.list_raffle_id[:75]
            # print(self.list_raffle_id)

    def check_duplicate(self, raffle_id):
        return (raffle_id in self.list_raffle_id)


async def handle_1_room_storm(target, roomid, stormid):
    result = await utils.enter_room(roomid)
    if result:
        if not Rafflehandler().check_duplicate(stormid):
            Rafflehandler().add2raffle_id(stormid)
            await utils.send_danmu_msg_web(f'{roomid}~{stormid}', target)


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
        # guard这里领取后，list对应会消失，其实就没有status了，这里是为了统一
        for j in json_response1['data']:
            print('获取到编号', j['id'])
            id = j['id']
            if not Rafflehandler().check_duplicate(id):
                Rafflehandler().add2raffle_id(id)
                list_available_raffleid.append(id)

        for raffleid in list_available_raffleid:
            await utils.send_danmu_msg_web(f'{roomid}-{raffleid}', target)
