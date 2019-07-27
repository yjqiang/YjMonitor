import sqlite3
from os import path

import attr

import utils


conn = sqlite3.connect(f'{path.dirname(path.realpath(__file__))}/data.db')


@attr.s(slots=True, frozen=True)
class Key:
    key_index = attr.ib(converter=str)  # 对真正的key（password）进行md5哈希，作为index
    key_value = attr.ib(converter=str)  # 真正的key（password）经过argon2处理后的数据
    key_created_time = attr.ib(converter=int)  # 当 created_time 为 0 时，expire_time 就是有效时间长度；非零就是时间点
    key_max_users = attr.ib(convert=int)
    key_expired_time = attr.ib(convert=int)

    def as_sql_values(self):
        key_index = str(self.key_index)
        key_value = str(self.key_value)
        key_created_time = int(self.key_created_time)
        key_max_users = str(self.key_max_users)
        key_expired_time = int(self.key_expired_time)
        return key_index, key_value, key_created_time, key_max_users, key_expired_time

    def as_str(self):
        return f'key的有效时间:{self.key_created_time}-{self.key_expired_time}, ' \
            f'最多允许同时在线人数为{self.key_max_users}'


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
        return None if result is None else self.as_key(result)

    def del_by_primary_key(self, key_index):
        with self.conn:
            self.conn.execute('DELETE FROM keys WHERE key_index=?', (str(key_index),))


keys_table = KeysTable()


def insert_element(key: Key):
    return keys_table.insert_element(key)


def select_all():
    return keys_table.select_all()


def is_key_addable(key_index: str, key_value: str):  # md5不同，orig_key肯定不同
    cursor = conn.execute(
        'SELECT 1 FROM keys WHERE key_index = ? OR key_value= ? ', (key_index, key_value))
    return not bool(cursor.fetchone())


def clean_safely():
    with conn:
        conn.execute(
            'DELETE FROM keys WHERE key_created_time!=0 and key_expired_time<? and key_expired_time!=0',
            (utils.curr_time(),))


def activate(key_index: str):
    curr_time = utils.curr_time()
    # 永久就是 key_expired_time 为 0，否则是有效时间长度
    with conn:
        conn.execute(
            'UPDATE keys SET key_created_time = ?, key_expired_time = CASE'
            ' WHEN key_expired_time!=0 THEN ? + key_expired_time ELSE 0 END'
            ' WHERE key_index=? and key_created_time=0',
            (curr_time, curr_time, key_index))


def select_by_primary_key(key_index):
    return keys_table.select_by_primary_key(key_index)
