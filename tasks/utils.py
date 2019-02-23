import asyncio
import re
import random
import printer
from reqs.utils import UtilsReq


class UtilsTask:
    @staticmethod
    async def get_rooms_from_remote(user, start, end):
        json_rsp = await user.req_s(UtilsReq.get_rooms_from_remote, user, start, end)
        # print(json_rsp)
        if json_rsp is not None:
            rooms = json_rsp['roomid']
            printer.info([f'本次刷新房间总计获取{len(rooms)}, 请求起止指针{start}-{end}'], True)
        else:
            printer.info([f'本次刷新房间总计获取 None, 请求起止指针{start}-{end}'], True)
            rooms = None
        return rooms

    @staticmethod
    async def send_danmu(user, room_id, raffle_id, raffle_type):
        async with user._send_danmu_lock:
            await send_raffle2room(user, room_id, raffle_id, raffle_type)


class DanmuSender:
    def __init__(self):
        self.__keys = '阝飠牜饣卩卪厸厶厽孓宀巛巜彳廴彡彐忄扌攵氵灬爫犭疒癶礻糹纟罒罓耂虍訁覀兦亼亽亖亗吂卝匸皕旡玊尐幵朩囘囙囜囝囟囡団囤囥囦囧囨囩囪囫囬囮囯困囱囲図囵囶囷囸囹固囻囼图囿圀圁圂圃圄圅圆圇圉圊圌圍圎圏圐圑園圓圔圕圖圗團圙圚圛圜圝圞'
        self.__reverse_keys = {value: i for i, value in enumerate(self.__keys)}
        self.is_refresh_ok = True
        self.check_msg = None
        self.room_id = None
        # 保持用户到id的映射，如果共享，很有可能导致混乱
        self.dict_danmu_id = {}

    def __dec2base(self, int_x, base=110):
        digits = []
        if not int_x:
            digits = [self.__keys[0]]
        while int_x:
            digits.append(self.__keys[int(int_x % base)])
            int_x = int(int_x / base)
        digits.reverse()
        return ''.join(digits)

    async def send_raffle2room(self, user, room_id, raffle_id, raffle_type):
        if raffle_type == -1:
            if self.is_refresh_ok:
                await self.send(user, f'{self.check_msg}{random.choice(self.__keys)}T', room_id)
            else:
                await self.send(user, f'{self.check_msg}{random.choice(self.__keys)}F', room_id)
            await asyncio.sleep(1.5)
        else:
            if raffle_type == 0:
                str_type = '~'
            elif raffle_type == 1:
                str_type = '+'
            else:
                return
            danmu_id = self.dict_danmu_id.get(user, 0)
            print('__________________________________')
            user.info([f'准备发送抽奖弹幕：{room_id}的{raffle_id}号抽奖({raffle_type})，弹幕id为{danmu_id} (舰队的推送与发送弹幕直接有增加人为延迟)'], True)
            l = f'{self.__dec2base(danmu_id)}.{self.__dec2base(raffle_id)}{str_type}'
            r = f'{self.__dec2base(danmu_id + 1)}.{self.__dec2base(room_id)}{str_type}'
            l_varified = l + self.__keys[109 - self.__reverse_keys[l[0]]]
            r_varified = r + self.__keys[109 - self.__reverse_keys[r[0]]]
            await self.send(user, l_varified, room_id)
            await asyncio.sleep(1.5)
            await self.send(user, r_varified, room_id)
            await asyncio.sleep(1.5)
            user.info([f'已发送完抽奖弹幕：{room_id}的{raffle_id}号抽奖({raffle_type})，弹幕id为{danmu_id}'], True)
            self.dict_danmu_id[user] = (danmu_id + 2) % 1000

    async def check_send(self, user, msg):
        room_id = self.room_id
        for i in range(15):
            json_response = await user.req_s(UtilsReq.send_danmu, user, msg, room_id)
            code = json_response['code']
            msg_rsp = json_response['msg']
            if not code and not msg_rsp:
                user.info([f'已发送弹幕{msg}到{room_id}'], True)
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
            await asyncio.sleep(2)
        return False

    @staticmethod
    def special_handle(msg):
        def add_words(match, num=1, word='?'):
            ori = match.group()
            add = '?' * (num - len(ori) + 2)
            return ori[:1] + add + ori[1:]

        new = msg
        new = re.sub('04', add_words, new)
        assert new.replace('?', '') == msg
        return new

    @staticmethod
    def add_special_str0(msg):
        half_len = int(len(msg) / 2)
        l = msg[:half_len]
        r = msg[half_len:]
        new_l = ''.join([i + '?' for i in l])
        new_r = ''.join([i + '?' for i in r])
        return [msg, new_l + r, l + new_r, new_l + new_r]

    @staticmethod
    def add_special_str1(msg):
        len_msg = len(msg)
        return [f'{msg[:i]}??????{msg[i:]}' for i in range(1, len_msg)]

    async def send(self, user, msg, room_id):
        msg = self.special_handle(msg)
        list_danmu = self.add_special_str0(msg) + self.add_special_str1(msg)
        # print('本轮次测试弹幕群', list_danmu)
        for i in list_danmu:
            if await self.check_send(user, i):
                return True
            await asyncio.sleep(1.5)
            printer.warn(f'弹幕{i}尝试')
        print('发送失败，请反馈', msg)
        printer.warn(f'弹幕{msg}尝试失败，请反馈')
        # sys.exit(-1)
        return False

    def set_refresh_ok(self, is_refresh_ok):
        self.is_refresh_ok = is_refresh_ok


danmu_sender = DanmuSender()


async def send_raffle2room(user, room_id, raffle_id, raffle_type):
    await danmu_sender.send_raffle2room(user, room_id, raffle_id, raffle_type)


def set_refresh_ok(is_refresh_ok):
    danmu_sender.set_refresh_ok(is_refresh_ok)


def set_checkmsg(msg):
    danmu_sender.check_msg = msg


def set_roomid(room_id):
    danmu_sender.room_id = room_id

# i这里有致命错误！！！！！！！！！1多个用户同时发，i不安全
