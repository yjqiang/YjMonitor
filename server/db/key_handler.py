import random
import string

from argon2 import PasswordHasher

import utils
from . import sql
from printer import info as print
from receiver import receivers


class KeyHandlerError(Exception):  # 建立连接之后，ws的错误情况
    pass


class KeyCheckVerificationError(KeyHandlerError):  # KEY错误
    pass


class KeyCheckMaxError(KeyHandlerError):  # 该用户的key同时使用过多错误
    pass


class KeyHandler:
    __slots__ = ('_ph', '_receivers', '_key_seed',)

    def __init__(self):
        self._ph = PasswordHasher()
        self._receivers = receivers
        self._key_seed = f'{string.digits}{string.ascii_letters}!#$%&()*+,-./:;<=>?@[]^_`|~'  # 89个字符，抛弃了一些特殊字符

    def check_key(self, naive_hashed_key: str) -> str:
        key = sql.select_by_primary_key(naive_hashed_key)
        if key is None:
            result0 = '404'
            result1 = f'该KEY目前一共-1个在线连接'
        else:
            result0 = key.as_str()
            result1 = f'该KEY目前一共{self._receivers.count_user_by_key(key.key_index)}个在线连接'
        return f'{result0};{result1}'

    def create_key(self, max_users: int, available_days: int) -> str:
        while True:
            orig_key = ''.join(random.choices(self._key_seed, k=16))  # 100^16 别想着暴力了，各位

            hashed_key: str = self._ph.hash(orig_key)
            naive_hashed_key: str = utils.naive_hash(orig_key)
            if sql.is_key_addable(key_index=naive_hashed_key, key_value=hashed_key):
                key_created_time = 0
                expired_time = 0 if not available_days else key_created_time + available_days*3600*24
                sql.insert_element(sql.Key(
                    key_index=naive_hashed_key,
                    key_value=hashed_key,
                    key_created_time=key_created_time,
                    key_max_users=max_users,
                    key_expired_time=expired_time)
                )
                print(f'创建了一个新的KEY(MAX人数为{max_users:^5}人, 可用天数为{available_days:^5}天): {orig_key}')
                return orig_key

    def verify_key(self, orig_key: str) -> str:
        key = sql.is_key_verified(orig_key)
        if key is not None:
            key_index = key.key_index
            if not key.key_created_time:
                print(f'正在激活 {key_index[:5]}***')
                sql.activate(key_index)  # 只更新 creat 和 expire 时间,后面的返回不需要这么多东西，这里就不需要刷新了
            if self._receivers.can_pass_max_users_test(key_index, key.key_max_users):
                return key_index
            raise KeyCheckMaxError()
        else:
            raise KeyCheckVerificationError()

    def check_key_by_hashed_key(self, naive_hashed_key: str) -> str:
        return self.check_key(naive_hashed_key)

    @staticmethod
    def clean_safely():
        sql.clean_safely()


key_handler = KeyHandler()
