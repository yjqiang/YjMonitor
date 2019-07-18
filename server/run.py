import sys
import json
import base64
import asyncio
import random
import string
from os import path

import rsa
from aiohttp import web

from argon2 import PasswordHasher

from db import sql
import utils
from printer import info
import json_req_exceptions
import tcp_req_exception
from receiver import TcpReceiverConn, Receiver, BroadCaster
from poster import PostOffice
from bili_statistics import DuplicateChecker
from blacklist import BlackList


class BroadCastHandler:
    def __init__(self, super_admin_pubkey: rsa.PublicKey, admin_pubkey: rsa.PublicKey):
        self._super_admin_pubkey = super_admin_pubkey
        self._admin_pubkey = admin_pubkey
        self._broadcaster = BroadCaster()
        self._post_office = PostOffice()
        self._key_seed = f'{string.digits}{string.ascii_letters}!#$%&()*+,-./:;<=>?@[]^_`|~'  # 89个字符，抛弃了一些特殊字符
        self._ph = PasswordHasher()
        self._blacklist = BlackList()
        self._lock_open_conn = asyncio.Semaphore(2)
        self._duplicate_checker = DuplicateChecker()

    async def clean_rubbish(self):
        while True:
            info('正在执行清理工作')
            sql.clean_safely()
            self._blacklist.clear_all()
            await asyncio.sleep(3600*6)

    def _create_key(self, max_users: int = 3, available_days: int = 30) -> str:
        while True:
            orig_key = ''.join(random.choices(self._key_seed, k=16))  # 100^16 别想着暴力了，各位
            encrypted_key = base64.b64encode(
                rsa.encrypt(orig_key.encode('utf8'), self._super_admin_pubkey)
            ).decode('utf8')
            hashed_key: str = self._ph.hash(orig_key)
            naive_hashed_key: str = utils.naive_hash(orig_key)
            if sql.is_key_addable(key_index=naive_hashed_key, key_value=hashed_key):
                curr_time = utils.curr_time()
                expired_time = 0 if not available_days else curr_time + available_days*3600*24
                sql.insert_element(sql.Key(
                    key_index=naive_hashed_key,
                    key_value=hashed_key,
                    key_created_time=curr_time,
                    key_max_users=max_users,
                    key_expired_time=expired_time)
                )
                info(f'创建了一个新的KEY(MAX人数{max_users:^5}): {orig_key}')
                return encrypted_key

    async def _broadcast_raffle(self, json_data: dict):
        await self._broadcaster.broadcast_raffle(json_data)

    # 验证json请求签名正确性
    @staticmethod
    async def _verify_json_req(request, pubkey: rsa.PublicKey) -> tuple:
        """
        {
            'code': 0,
            'type': 'raffle',
            'verification':
                {'signature': f'Hello World. This is {name} at {time}.', 'name': name, 'time': int},
            'data': {...}
        }
        """
        try:
            json_data = await request.json()
        except json.JSONDecodeError:
            raise json_req_exceptions.ReqFormatError()
        except:
            raise json_req_exceptions.OtherError()

        if 'verification' in json_data and 'data' in json_data:
            verification = json_data['verification']
            if isinstance(verification, dict) and 'signature' in verification and 'time' in verification:
                try:
                    cur_time0 = int(verification['time'])
                    cur_time1 = utils.curr_time()
                    if -1200 <= cur_time0 - cur_time1 <= 1200:
                        # 缺省name表示为super_admin，需要使用超管签名校验，其他的用管理员校验
                        name = verification.get("name", "super_admin")
                        text = f'Hello World. This is {name} at {cur_time0}.'.encode('utf-8')
                        rsa.verify(
                            text,
                            base64.b64decode(verification['signature'].encode('utf8')),
                            pubkey)
                        data = json_data['data']
                        if isinstance(data, dict):
                            return name, data
                        raise json_req_exceptions.DataError
                    else:
                        raise json_req_exceptions.TimeError
                except rsa.VerificationError:
                    raise json_req_exceptions.VerificationError
                except json_req_exceptions.JsonReqError:
                    raise
                except:
                    raise json_req_exceptions.DataError
        raise json_req_exceptions.DataError

    async def _verify_tcp_req(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Receiver:
        conn = TcpReceiverConn(writer=writer, reader=reader)
        addr, _ = writer.get_extra_info('peername')
        info(f'接收到来自 IP {addr}的 tcp 连接请求')

        try:
            if isinstance(addr, str) and self._blacklist.should_be_banned(addr):
                self._blacklist.refresh(addr)
                raise tcp_req_exception.BanError(conn)

            json_data = await conn.recv_json()
            if json_data is not None:
                orig_key = json_data['data']['key']
                key = sql.is_key_verified(orig_key)
                if key is not None:
                    if self._broadcaster.can_pass_max_users_test(key.key_index, key.key_max_users):
                        user = Receiver(user_conn=conn, user_key_index=key.key_index)
                        return user
                    else:
                        info(f'KEY({key.key_index[:5]}***...)用户过多')
                        raise tcp_req_exception.MaxError(conn)
                else:
                    self._blacklist.refresh(addr)
                    raise tcp_req_exception.VerificationError(conn)
            else:
                raise tcp_req_exception.DataError(conn)

        except tcp_req_exception.TcpReqError:
            raise
        except:
            raise tcp_req_exception.OtherError(conn)

    # 普通管理员权限
    async def check_handler(self, request):
        try:
            _, data = await self._verify_json_req(request, self._admin_pubkey)
            search_results = {}
            if 'naive_hashed_key' in data:
                key = sql.select_by_primary_key(data['naive_hashed_key'])
                result = key.as_str() if key is not None else '404'
                search_results['key_searched_by_naive_hash'] = result

            if 'check_ip' in data:
                search_results['is_ip_banned'] = self._blacklist.should_be_banned(data['check_ip'])

            if 'clean_ip' in data:
                self._blacklist.del_record(data['clean_ip'])
                search_results['is_ip_cleaned'] = True

            return web.json_response({
                'code': 0,
                'type': 'server_status',
                'data': {
                    'version': '0.1.2',
                    'observers_num': f'当前用户共{self._broadcaster.num_observers()}',
                    # 'observers_count': self._broadcaster.count(),
                    'posters_count': self._post_office.count(),
                    'curr_db': '',
                    'search_results': search_results,
                    'curr_time': utils.curr_time(),
                    'encrypted_msg2admin': [],  # 管理员信息需要私钥解密
                    'encrypted_msg2super_admin': []  # 超管信息需要超管私钥解密
                }
            })
        except json_req_exceptions.JsonReqError as e:
            return web.json_response(e.RSP_SUGGESTED)

    # 超管权限
    async def create_key_handler(self, request):
        try:
            _, data = await self._verify_json_req(request, self._super_admin_pubkey)
            max_users = data.get('max_users', 3)
            available_days = data.get('available_days', 30)
            if not isinstance(max_users, int):
                raise json_req_exceptions.DataError()
            return web.json_response({'code': 0,
                                      'type': '',
                                      'data': {'encrypted_key': self._create_key(max_users, available_days)}})
        except json_req_exceptions.JsonReqError as e:
            return web.json_response(e.RSP_SUGGESTED)

    # 普通管理员权限
    async def post_raffle_handler(self, request):
        try:
            name, data = await self._verify_json_req(request, self._admin_pubkey)
            self._post_office.update(name)
            info(f'接收到抽奖{data}')
            sending_json_data = {
                'code': 0,
                'type': 'raffle',
                'data': data
            }
            if 'raffle_id' in data:
                raffle_id = int(data['raffle_id'])
                if self._duplicate_checker.add2checker(raffle_id):
                    asyncio.ensure_future(self._broadcast_raffle(sending_json_data))
            return web.json_response({'code': 0, 'type': '', 'data': {}})
        except json_req_exceptions.JsonReqError as e:
            return web.json_response(e.RSP_SUGGESTED)

    async def on_shutdown(self, _):
        await self._broadcaster.broadcast_close()

    async def tcp_receiver_handle(self, reader, writer):
        async with self._lock_open_conn:
            try:
                user = await self._verify_tcp_req(writer=writer, reader=reader)
            except tcp_req_exception.TcpReqError as e:
                if e.conn is not None:
                    await asyncio.sleep(0.25)
                    await e.conn.send_json(e.RSP_SUGGESTED)
                    await e.conn.close()
                return

        self._broadcaster.append(user)
        info(f'用户{user.user_key_index[:5]}加入')

        try:
            if not await user.user_conn.send_json({'code': 0, 'type': 'entered', 'data': {}}):
                return
            while True:
                dict_data = await user.user_conn.recv_json()
                if dict_data is None:
                    return
                info(dict_data)
        except asyncio.CancelledError:
            return
        except:
            info(sys.exc_info()[0], sys.exc_info()[1])
            return
        finally:
            self._broadcaster.remove(user)
            info(f'用户{user.user_key_index[:5]}删除')
            await asyncio.shield(user.user_conn.close())


def main():
    key_path = f'{path.dirname(path.realpath(__file__))}/key'
    with open(f'{key_path}/super_admin_pubkey.pem', 'rb') as f:
        super_admin_pubkey = rsa.PublicKey.load_pkcs1(f.read())
    with open(f'{key_path}/admin_pubkey.pem', 'rb') as f:
        admin_pubkey = rsa.PublicKey.load_pkcs1(f.read())

    broadcast_handler = BroadCastHandler(
        super_admin_pubkey=super_admin_pubkey,
        admin_pubkey=admin_pubkey)

    loop = asyncio.get_event_loop()
    loop.create_task(broadcast_handler.clean_rubbish())
    coro = asyncio.start_server(broadcast_handler.tcp_receiver_handle, '0.0.0.0', 8002, loop=loop)
    loop.run_until_complete(coro)

    app = web.Application()
    app.router.add_route('GET', '/check', broadcast_handler.check_handler)
    app.router.add_route('GET', '/create_key', broadcast_handler.create_key_handler)
    app.router.add_route('POST', '/post_raffle', broadcast_handler.post_raffle_handler)
    app.on_shutdown.append(broadcast_handler.on_shutdown)
    web.run_app(app, port=8001)


if __name__ == '__main__':
    main()
