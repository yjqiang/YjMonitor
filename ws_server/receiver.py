import asyncio
from time import time
from typing import List

import attr
from aiohttp import web

from printer import info


@attr.s(slots=True)
class Receiver:  # ws的每个用户都是一个receiver
    user_rsp = attr.ib(validator=attr.validators.instance_of(web.WebSocketResponse))
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
        try:
            await asyncio.wait_for(user.user_rsp.send_json(json_data), timeout=3)
        except asyncio.TimeoutError:
            user.user_status = False
            return False
        except:
            user.user_status = False
            return False
        return True

    @staticmethod
    async def _close(user: Receiver):
        try:
            await user.user_rsp.close()
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
