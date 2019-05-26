import asyncio
import struct
import json
from time import time
from typing import List, Optional

import attr
from aiohttp import WSMsgType

from printer import info


class ReceiverConn:
    async def send_json(self, dict_body) -> bool:
        return False

    async def close(self) -> bool:
        return True

    async def recv_json(self) -> Optional[dict]:
        return None


class WsReceiverConn(ReceiverConn):
    def __init__(self, conn):
        self._conn = conn

    async def send_json(self, dict_body) -> bool:
        try:
            await asyncio.wait_for(self._conn.send_json(dict_body), timeout=3)
        except:
            return False
        return True

    async def close(self) -> bool:
        try:
            await self._conn.close()
        except:
            pass
        return True

    async def recv_json(self) -> Optional[dict]:
        try:
            msg = await self._conn.receive()
            if msg.type == WSMsgType.TEXT:
                return json.loads(msg.data)
            elif msg.type == WSMsgType.BINARY:
                return json.loads(msg.data.decode('utf8'))
        except:
            return None


class TcpReceiverConn(ReceiverConn):
    def __init__(self, writer, reader):
        self._writer = writer
        self._reader = reader

    async def send_json(self, dict_body) -> bool:
        str_body = json.dumps(dict_body)
        body = str_body.encode('utf8')
        header = struct.pack('!I', len(body))
        data = header + body
        try:
            self._writer.write(data)
            await asyncio.wait_for(self._writer.drain(), timeout=3)
        except:
            return False
        return True

    async def close(self) -> bool:
        try:
            self._writer.close()
        except:
            pass
        return True

    async def recv_json(self) -> Optional[dict]:
        try:
            while True:
                bytes_data = await asyncio.wait_for(self._reader.readexactly(4), timeout=40)
                len_body, = struct.unpack('!I', bytes_data)
                if len_body:
                    body = await asyncio.wait_for(self._reader.readexactly(len_body), timeout=40)
                    json_body = json.loads(body.decode('utf8'))
                    return json_body
                else:
                    self._writer.write(struct.pack('!I', 0))
                    await self._writer.drain()
        except:
            return None


@attr.s(slots=True)
class Receiver:  # ws的每个用户都是一个receiver
    user_conn = attr.ib(validator=attr.validators.instance_of(ReceiverConn))
    user_key_index = attr.ib(validator=attr.validators.instance_of(str))
    user_status = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    user_join_time = attr.ib(default=int(time()), validator=attr.validators.instance_of(int))


class BroadCaster:  # receiver的广播、统计等
    def __init__(self):
        self._receivers: List[Receiver] = []

    def append(self, user: Receiver):
        self._receivers.append(user)

    def remove(self, user: Receiver):
        if user in self._receivers:
            self._receivers.remove(user)
            return True
        return False

    def num_observers(self):
        return len(self._receivers)

    @staticmethod
    async def _send_json(user: Receiver, json_data: dict) -> bool:
        result = await user.user_conn.send_json(json_data)
        user.user_status = result
        return result

    @staticmethod
    async def _close(user: Receiver):
        try:
            await user.user_conn.close()
        except:
            pass

    async def broadcast_raffle(self, json_data: dict):
        # 使用和删除过程中都是“原子操作”（协程不切），所以不需要锁
        if self._receivers:
            tasks = [asyncio.ensure_future(self._send_json(user, json_data))
                     for user in self._receivers if user.user_status]
            if tasks:
                if not all(await asyncio.gather(*tasks)):
                    info('存在发送失败的用户，即将清理')
                    new_observers = []
                    deprecated_observers = []
                    for user in self._receivers:
                        if user.user_status:
                            new_observers.append(user)
                        else:
                            deprecated_observers.append(user)
                    self._receivers = new_observers
                    tasks = [asyncio.ensure_future(self._close(user)) for user in deprecated_observers]
                    if tasks:
                        await asyncio.wait(tasks)
            info(f'已推送抽奖{json_data}')

    async def broadcast_close(self):
        if self._receivers:
            tasks = [asyncio.ensure_future(self._close(user)) for user in self._receivers]
            await asyncio.wait(tasks)
            self._receivers.clear()

    def can_pass_max_users_test(self, key_index: str, key_max_users: int):
        num_same_key = 0
        for user in self._receivers:
            if user.user_key_index == key_index:
                num_same_key += 1
        if num_same_key < key_max_users:
            return True
        return False

    def count(self):
        dict_count = {}  # index: count
        for user in self._receivers:
            dict_count[user.user_key_index] = dict_count.get(user.user_key_index, 0) + 1
        return {key[:5]: value for key, value in dict_count.items()}
