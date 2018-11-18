
import time
import re
from itertools import zip_longest
import printer
from bilibili import bilibili
from configloader import ConfigLoader
import asyncio
import sys


def CurrentTime():
    currenttime = int(time.time())
    return str(currenttime)

        
class DanmuSender:
    instance = None

    def __new__(cls, room_id=None):
        if not cls.instance:
            cls.instance = super(DanmuSender, cls).__new__(cls)
            cls.instance.queue_raffle = asyncio.PriorityQueue()
            cls.instance.room_id = room_id
            cls.instance.__keys = '阝飠牜饣卩卪厸厶厽孓宀巛巜彳廴彡彐忄扌攵氵灬爫犭疒癶礻糹纟罒罓耂虍訁覀兦亼亽亖亗吂卝匸皕旡玊尐幵朩囘囙囜囝囟囡団囤囥囦囧囨囩囪囫囬囮囯困囱囲図囵囶囷囸囹固囻囼图囿圀圁圂圃圄圅圆圇圉圊圌圍圎圏圐圑園圓圔圕圖圗團圙圚圛圜圝圞'
            
            cls.instance.__reverse_keys = {value: i for i, value in enumerate(cls.instance.__keys)}
        return cls.instance
        
    def __dec2base(self, int_x, base=110):
        digits = []
        if not int_x:
            digits = [self.__keys[0]]
        while int_x:
            digits.append(self.__keys[int(int_x % base)])
            int_x = int(int_x / base)
        digits.reverse()
        return ''.join(digits)
        
    async def run(self):
        i = 0
        while True:
            type, raffle_id, room_id = await self.queue_raffle.get()
            if type == -1:
                await self.send(raffle_id)
                await asyncio.sleep(1.5)
            else:
                if type == 0:
                    str_type = '~'
                elif type == 1:
                    str_type = '+'
                l = f'{self.__dec2base(i)}.{self.__dec2base(raffle_id)}{str_type}'
                r = f'{self.__dec2base(i + 1)}.{self.__dec2base(room_id)}{str_type}'
                l_varified = l + self.__keys[109 - self.__reverse_keys[l[0]]]
                r_varified = r + self.__keys[109 - self.__reverse_keys[r[0]]]
                await self.send(l_varified)
                await asyncio.sleep(1.5)
                await self.send(r_varified)
                await asyncio.sleep(1.5)
            i = (i + 2) % 1000
    
    async def check_send(self, msg):
        roomId = self.room_id
        for i in range(15):
            json_response = await bilibili.request_send_danmu_msg_web(msg, roomId)
            code = json_response['code']
            msg_rsp = json_response['msg']
            if not code and not msg_rsp:
                printer.info([f'已发送弹幕{msg}到{roomId}'], True)
                return True
            elif not code and msg_rsp == '内容非法':
                printer.info([f'非法反馈, 准备后续的处理 {msg}'], True)
                return False
            elif not code and msg_rsp == 'msg in 1s':
                printer.info(['弹幕发送频繁提示'], True)
            elif code == -500:
                printer.warn(f'弹幕{msg}提示超出限制长度')
                return False
            else:
                print(json_response, msg)
            await asyncio.sleep(1.5)
        return False
            
    def special_handle(self, msg):
        def add_words(match, num=1, word='?'):
            ori = match.group()
            add = '?' * (num - len(ori) + 2)
            new = ori[:1] + add + ori[1:]
            return new
            
        new = msg
        new = re.sub('04', add_words, new)
        assert new.replace('?', '') == msg
        return new
            
    def add_special_str0(self, msg):
        half_len = int(len(msg) / 2)
        l = msg[:half_len]
        r = msg[half_len:]
        new_l = ''.join([i+'?' for i in l])
        new_r = ''.join([i+'?' for i in r])
        return [msg, new_l+r, l+new_r, new_l+new_r]
        
    def add_special_str1(self, msg):
        len_msg = len(msg)
        return [f'{msg[:i]}??????{msg[i:]}' for i in range(1, len_msg)]
            
    async def send(self, msg):
        print('_________________________________________')
        msg = self.special_handle(msg)
        list_danmu = self.add_special_str0(msg) + self.add_special_str1(msg)
        # print('本轮次测试弹幕群', list_danmu)
        for i in list_danmu:
            if await self.check_send(i):
                print('_________________________________________')
                return True
            await asyncio.sleep(1.5)
            printer.warn(f'弹幕{i}尝试')
        print('发送失败，请反馈', msg)
        printer.warn(f'弹幕{msg}尝试失败，请反馈')
        # sys.exit(-1)
        return False
        
    async def add2queue(self, *args):
        await self.queue_raffle.put(args)
        

# 在这里priority也作为一个type
async def send_danmu_msg_web(*args):
    await DanmuSender().add2queue(*args)
    
    
async def enter_room(roomid):
    json_response = await bilibili.request_check_room(roomid)

    if not json_response['code']:
        data = json_response['data']
        param1 = data['is_hidden']
        param2 = data['is_locked']
        param3 = data['encrypted']
        if any((param1, param2, param3)):
            printer.info([f'抽奖脚本检测到房间{roomid:^9}为异常房间'], True)
            printer.warn(f'抽奖脚本检测到房间{roomid:^9}为异常房间')
            return False
        else:
            # print('房间为真')
            # await bilibili.post_watching_history(roomid)
            return True
            
async def get_rooms_from_remote(start, end):
    json_rsp = await bilibili().get_rooms_from_remote(start, end)
    # print(json_rsp)
    if json_rsp is not None:
        rooms = json_rsp['roomid']
        print('总计获取', len(rooms))
        print('起止指针', start, end)
    else:
        rooms = None
    return rooms
            
            
async def getRecommend():
    async def fetch_room(url):
        roomidlist = []
        should_stop = False
        for x in range(1, 250):
            if not (x % 10):
                print(f'截止第{x}页，获取了{len(roomidlist)}个房间(可能重复)')
            
            json_data = await bilibili().get_roomids(url, x)
            if not json_data['data']:
                break
            for room in json_data['data']:
                if room['online'] <= 100:
                    pass
                    should_stop = True
                    print(room)
                    break
                roomidlist.append(room['roomid'])
            if should_stop:
                print(f'截止第{x}页，获取了{len(roomidlist)}个房间(可能重复)')
                break
            
        print('去重之前', len(roomidlist))

        unique_list = []
        for id in roomidlist:
            if id not in unique_list:
                unique_list.append(id)
        return unique_list

    urls = [
        'http://api.live.bilibili.com/area/liveList?area=all&order=online&page=',
        'http://api.live.bilibili.com/room/v1/room/get_user_recommend?page=',
    ]

    roomlist0 = await fetch_room(urls[0])
    roomlist1 = await fetch_room(urls[1])
    len_0 = len(roomlist0)
    len_1 = len(roomlist1)
    print('两种获取热度房间的方法获得房间数目', len_0, len_1)
    unique_list = []
    for i, j in zip_longest(roomlist0, roomlist1):
        if i is not None and i not in unique_list:
            unique_list.append(i)
        if j is not None and j not in unique_list:
            unique_list.append(j)
    print(f'总获取房间{len(unique_list)}')
    
    roomid_conf = ConfigLoader().list_roomid
    for i in roomid_conf:
        if i not in unique_list:
            unique_list.append(i)
        if len(unique_list) == 6000:
            break
    print(f'总获取房间{len(unique_list)}')
    return unique_list + [0] * (6000 - len(unique_list))


