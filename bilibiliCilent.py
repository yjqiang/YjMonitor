from statistics import Statistics
from configloader import ConfigLoader
import printer
from printer import Printer
import rafflehandler
import asyncio
import struct
import json
import sys
import aiohttp


class bilibiliClient():
    __slots__ = ('ws', 'roomid', 'area_id', 'loop_func', 'client', 'target')
    structer = struct.Struct('!I2H2I')

    def __init__(self, roomid=None, area_id=None):
        self.client = aiohttp.ClientSession()
        self.loop_func = self.DanMuraffle
        self.roomid = roomid
        self.area_id = area_id
        self.target = ConfigLoader().dic_user['other_control']['default_monitor_roomid']

    # 待确认
    async def close_connection(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        printer.info([f'{self.area_id}号弹幕收尾模块状态{self.ws.closed}'], True)

    async def connectServer(self):
        try:
            url = 'wss://broadcastlv.chat.bilibili.com:443/sub'
            self.ws = await asyncio.wait_for(self.client.ws_connect(url), timeout=10)
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        printer.info([f'{self.area_id}号弹幕监控已连接b站服务器'], True)
        body = f'{{"uid":0,"roomid":{self.roomid},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        return (await self.SendSocketData(opt=7, body=body))
        
    def set_real_room(self, roomid):
        if roomid == 0:
            self.roomid = 23058
            self.loop_func = self.printDanMu
            print('0检测所以，事实上收拾收拾')
        else:
            self.roomid = roomid
            self.loop_func = self.DanMuraffle

    async def HeartbeatLoop(self):
        # printer.info([f'{self.area_id}号弹幕监控开始心跳（心跳间隔30s，后续不再提示）'], True)
        try:
            while True:
                if self.area_id == 1:
                    printer.info([f'{self.area_id}号弹幕监控心跳'], True)
                if not (await self.SendSocketData(opt=2, body='')):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            printer.info([f'{self.area_id}号弹幕监控心跳模块主动取消'], True)

    async def SendSocketData(self, opt, body, len_header=16, ver=1, seq=1):
        remain_data = body.encode('utf-8')
        len_data = len(remain_data) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        data = header + remain_data
        try:
            await self.ws.send_bytes(data)
        except asyncio.CancelledError:
            printer.info([f'{self.area_id}号弹幕监控发送模块主动取消'], True)
            return False
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        return True

    async def ReadSocketData(self):
        bytes_data = None
        try:
            msg = await asyncio.wait_for(self.ws.receive(), timeout=35.0)
            bytes_data = msg.data
        except asyncio.TimeoutError:
            # print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            print('请联系开发者')
            return None
        # print(tmp)

        # print('测试0', bytes_data)
        return bytes_data

    async def ReceiveMessageLoop(self):
        while True:
            bytes_datas = await self.ReadSocketData()
            if bytes_datas is None:
                break
            len_read = 0
            len_bytes_datas = len(bytes_datas)
            loop_time = 0
            while len_read != len_bytes_datas:
                loop_time += 1
                if loop_time > 100:
                    print('请联系作者', bytes_datas)
                state = None
                split_header = self.structer.unpack(bytes_datas[len_read:16+len_read])
                len_data, len_header, ver, opt, seq = split_header
                remain_data = bytes_datas[len_read+16:len_read+len_data]
                # 人气值/心跳 3s间隔
                if opt == 3:
                    # self._UserCount, = struct.unpack('!I', remain_data)
                    printer.debug(f'弹幕心跳检测{self.area_id}')
                # cmd
                elif opt == 5:
                    messages = remain_data.decode('utf-8')
                    dic = json.loads(messages)
                    state = self.loop_func(dic)
                # 握手确认
                elif opt == 8:
                    printer.info([f'{self.area_id}号弹幕监控进入房间（{self.roomid}）'], True)
                else:
                    printer.warn(bytes_datas[len_read:len_read + len_data])

                if state is not None and not state:
                    return
                len_read += len_data

    def printDanMu(self, dic):
        cmd = dic['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            # print(dic)
            Printer().print_danmu(dic)
            return

    def DanMuraffle(self, dic):
        cmd = dic['cmd']
        if cmd == 'SPECIAL_GIFT':
            if 'data' in dic and '39' in dic['data'] and dic['data']['39']['action'] == 'start':
                printer.info([f'房间号{self.roomid}有节奏风暴'], True)
                rafflehandler.Rafflehandler.Put2Queue((self.target, self.roomid, dic['data']['39']['id']), rafflehandler.handle_1_room_storm)
                Statistics.append2pushed_raffle('节奏风暴', 1)

        if cmd == 'GUARD_MSG':
            if 'buy_type' in dic and dic['buy_type'] != 1:
                # print(dic)
                printer.info([f'{self.area_id}号弹幕监控检测到{self.roomid:^9}的提督/舰长'], True)
                rafflehandler.Rafflehandler.Put2Queue((self.target, self.roomid), rafflehandler.handle_1_room_guard)
                Statistics.append2pushed_raffle('提督/舰长', area_id=self.area_id)
