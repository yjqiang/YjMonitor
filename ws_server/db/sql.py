import sqlite3
import hashlib
from os import path
from typing import Optional

import attr
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

import utils


conn = sqlite3.connect(f'{path.dirname(path.realpath(__file__))}/data.db')
password_hasher = PasswordHasher()


@attr.s(slots=True, frozen=True)
class Key:
    key_index = attr.ib(converter=str)  # 对真正的key（password）进行md5哈希，作为index
    key_value = attr.ib(converter=str)  # 真正的key（password）经过argon2处理后的数据
    key_created_time = attr.ib(converter=int)
    key_max_users = attr.ib(default=3, convert=int)
    key_expired_time = attr.ib(default=0, convert=int)

    def as_sql_values(self):
        key_index = str(self.key_index)
        key_value = str(self.key_value)
        key_created_time = int(self.key_created_time)
        key_max_users = str(self.key_max_users)
        key_expired_time = int(self.key_expired_time)
        return key_index, key_value, key_created_time, key_max_users, key_expired_time


class KeysTable:
    def __init__(self):
        sql_create_table = (
            'CREATE TABLE IF NOT EXISTS keys ('
            'key_index TEXT NOT NULL UNIQUE,'
            'key_value TEXT NOT NULL UNIQUE,'
            'key_created_time INTEGER NOT NULL,'
            'key_max_users TEXT NOT NULL,'
            'key_expired_time INTEGER NOT NULL,'
            'PRIMARY KEY (key_index)'
            '); '
        )
        conn.execute(sql_create_table)
        self.conn = conn

    @staticmethod
    def as_key(row):
        return Key(*row)

    def insert_element(self, key: Key):
        with self.conn:
            self.conn.execute('INSERT INTO keys VALUES (?, ?, ?, ?, ?)',
                              key.as_sql_values())

    def select_all(self):
        results = []
        for row in self.conn.execute('SELECT * FROM keys'):
            results.append(self.as_key(row))
        return results

    def select_by_primary_key(self, key_index):
        cursor = self.conn.execute('SELECT * FROM keys WHERE key_index=?', (str(key_index),))
        result = cursor.fetchone()
        if result is None:
            return None
        return self.as_key(result)

    def del_by_primary_key(self, key_index):
        with self.conn:
            self.conn.execute('DELETE FROM keys WHERE key_index=?', (str(key_index),))


keys_table = KeysTable()


def insert_element(key: Key):
    return keys_table.insert_element(key)


def select_all():
    return keys_table.select_all()


def is_key_verified(orig_key: str) -> Optional[Key]:
    key_index = hashlib.md5(orig_key.encode('utf-8')).hexdigest()
    key = keys_table.select_by_primary_key(key_index)
    if key is None:
        return None
    try:
        password_hasher.verify(key.key_value, orig_key)
    except VerifyMismatchError:
        return None
    return key


def is_key_addable(key_index: str, key_value: str):  # md5不同，orig_key肯定不同
    cursor = conn.execute(
        'SELECT 1 FROM keys WHERE key_index = ? OR key_value= ? ', (key_index, key_value))
    return not bool(cursor.fetchone())


def select_and_check():
    with conn:
        conn.execute('DELETE FROM keys WHERE key_expired_time<? and key_expired_time!=0', (utils.curr_time(),))
    return keys_table.select_all()
