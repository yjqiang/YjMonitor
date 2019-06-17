"""与 run_realtime.py 配合使用，保证只会监听在线的房间
"""
from struct import Struct
import json
import asyncio

from printer import info as print
from .bili_danmu_monitor import DanmuRaffleMonitor as Monitor


lock = asyncio.Semaphore(10)


class DanmuRaffleMonitor(Monitor):
    online_struct = Struct('!I')

    def __init__(
            self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.online = -1

    async def _open(self):
        async with lock:
            return await super()._open()

    async def _prepare_client(self):
        self.online = -1

    async def _read_one(self) -> bool:
        header = await self._conn.read_bytes(16)
        # 本函数对bytes进行相关操作，不特别声明，均为bytes
        if header is None:
            return False

        # 每片data都分为header和body，data和data可能粘连
        # data_l == header_l && next_data_l == next_header_l
        # ||header_l...header_r|body_l...body_r||next_data_l...
        tuple_header = self.header_struct.unpack_from(header)
        len_data, len_header, _, opt, _ = tuple_header

        len_body = len_data - len_header
        body = await self._conn.read_bytes(len_body)
        # 本函数对bytes进行相关操作，不特别声明，均为bytes
        if body is None:
            return False

        # 人气值(或者在线人数或者类似)以及心跳
        if opt == 3:
            online, = self.online_struct.unpack(body)
            if self.online == -1:
                self.online = max(online, 5)
            elif self.online < online:
                self.online = online
            else:
                self.online = online * 0.35 + self.online * 0.65  # 延迟操作
            if self.online <= 1.1:
                print(f'{self._area_id}号数据连接房间下播({self._room_id},{online}, {self.online})')
                self.pause()
                return False
        # cmd
        elif opt == 5:
            if not self.handle_danmu(json.loads(body.decode('utf-8'))):
                return False
        # 握手确认
        elif opt == 8:
            print(f'{self._area_id}号弹幕监控进入房间（{self._room_id}）')
        else:
            print(body)
            return False
        return True
