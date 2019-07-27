import json
import asyncio
from typing import Tuple

from aiohttp import web
from aiojobs.aiohttp import atomic, setup

from db.key_handler import key_handler, KeyCheckVerificationError, KeyCheckMaxError
from key.rsa_handler import rsa_handler, RsaHandlerVerificationError, RsaHandlerTimeError
import utils
from printer import info as print
import json_req_exceptions
import tcp_req_exception
from receiver import TcpReceiverConn, Receiver, receivers
from poster import posters
from bili_statistics import DuplicateChecker
from blacklist import BlackList


class BroadCastHandler:
    def __init__(self):
        self._rsa_handler = rsa_handler
        self._key_handler = key_handler

        self._receivers = receivers
        self._posters = posters

        self._blacklist = BlackList()
        self._lock_open_conn = asyncio.Semaphore(2)
        self._duplicate_checker = DuplicateChecker()

    async def clean_rubbish(self):
        while True:
            print('正在执行清理工作')
            self._key_handler.clean_safely()
            self._blacklist.clear_all()
            self._posters.clean_safely()
            await asyncio.sleep(3600*1)

    async def _broadcast_raffle(self, json_data: dict) -> None:
        await self._receivers.broadcast_raffle(json_data)

    # 验证json请求签名正确性
    @staticmethod
    async def _verify_json_req(request: web.Request, verify_func) -> Tuple[str, dict]:
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

        if isinstance(json_data, dict) and 'verification' in json_data and 'data' in json_data:
            verification = json_data['verification']
            if isinstance(verification, dict) and 'signature' in verification and 'time' in verification:
                try:
                    time = int(verification['time'])
                    name = str(verification.get('name', 'super_admin'))
                    verify_func(name=name, time=time, signature=verification['signature'])

                    data = json_data['data']
                    if isinstance(data, dict):
                        return name, data
                except RsaHandlerVerificationError:
                    raise json_req_exceptions.VerificationError()
                except RsaHandlerTimeError:
                    raise json_req_exceptions.TimeError()
                except:
                    raise json_req_exceptions.DataError()
        raise json_req_exceptions.DataError()

    async def _verify_tcp_req(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Receiver:
        conn = TcpReceiverConn(writer=writer, reader=reader)
        addr, _ = writer.get_extra_info('peername')
        if isinstance(addr, str) and self._blacklist.should_be_banned(addr):
            print(f'拒绝黑名单用户 IP {addr} 连接请求')
            self._blacklist.refresh(addr)
            raise tcp_req_exception.BanError(conn)

        json_data = await conn.recv_json()

        if json_data is not None and isinstance(json_data, dict) and 'data' in json_data:
            data = json_data['data']
            if isinstance(data, dict) and 'key' in data:
                try:
                    orig_key = str(data['key'])
                    key_index = self._key_handler.verify_key(orig_key)
                    print(f'来自 IP {addr}的用户 {key_index[:5]} 成功验证身份')
                    return Receiver(user_conn=conn, user_key_index=key_index)
                except KeyCheckMaxError:
                    print(f'IP {addr} 使用的 key 已连接用户过多')
                    raise tcp_req_exception.MaxError(conn)
                except KeyCheckVerificationError:
                    self._blacklist.refresh(addr)
                    print(f'IP {addr} 错误尝试 key')
                    raise tcp_req_exception.VerificationError(conn)
                except:
                    raise tcp_req_exception.DataError(conn)
        raise tcp_req_exception.DataError(conn)

    # 超管权限
    async def check_handler(self, request: web.Request) -> web.StreamResponse:
        try:
            _, data = await self._verify_json_req(request, self._rsa_handler.verify_super_admin)
        except json_req_exceptions.JsonReqError as e:
            return web.json_response(e.RSP_SUGGESTED)

        search_results = {}
        if 'naive_hashed_key' in data:
            result = self._key_handler.check_key_by_hashed_key(data['naive_hashed_key'])
            search_results['key_searched_by_naive_hash'] = result

        if 'check_ip' in data:
            search_results['is_ip_banned'] = self._blacklist.should_be_banned(data['check_ip'])

        if 'clean_ip' in data:
            self._blacklist.del_record(data['clean_ip'])
            search_results['is_ip_cleaned'] = True

        return web.json_response({
            'code': 0,
            'type': '',
            'data': {
                'version': '0.2.0b3',
                'observers_num': f'当前用户共{self._receivers.num_observers()}',
                'posters_count': self._posters.count(),
                'search_results': search_results,
                'curr_time': utils.curr_time(),
            }
        })

    # 超管权限
    async def create_key_handler(self, request: web.Request) -> web.StreamResponse:
        try:
            _, data = await self._verify_json_req(request, self._rsa_handler.verify_super_admin)
            max_users = data.get('max_users', 1)
            available_days = data.get('available_days', 30)
            if not isinstance(max_users, int) or not isinstance(available_days, int):
                raise json_req_exceptions.DataError()
        except json_req_exceptions.JsonReqError as e:
            return web.json_response(e.RSP_SUGGESTED)

        orig_key = self._key_handler.create_key(max_users, available_days)
        encrypted_key = self._rsa_handler.encrypt_super_admin(orig_key)
        return web.json_response({'code': 0,
                                  'type': '',
                                  'data': {'encrypted_key': encrypted_key}})

    # 普通管理员权限
    async def post_raffle_handler(self, request: web.Request) -> web.StreamResponse:
        try:
            name, data = await self._verify_json_req(request, self._rsa_handler.verify_admin)
        except json_req_exceptions.JsonReqError as e:
            return web.json_response(e.RSP_SUGGESTED)

        self._posters.update(name)
        print(f'接收到抽奖{data}')
        if 'raffle_id' in data:
            raffle_id = int(data['raffle_id'])
            if self._duplicate_checker.add2checker(raffle_id):
                sending_json_data = {
                    'code': 0,
                    'type': 'raffle',
                    'data': data
                }
                asyncio.ensure_future(self._broadcast_raffle(sending_json_data))
        return web.json_response({'code': 0, 'type': '', 'data': {}})

    async def on_shutdown(self, _):
        await self._receivers.broadcast_close()

    async def tcp_receiver_handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            async with self._lock_open_conn:
                user = await self._verify_tcp_req(writer=writer, reader=reader)
        except tcp_req_exception.TcpReqError as e:
            sleep_time = 2.0 if \
                isinstance(e, (tcp_req_exception.BanError, tcp_req_exception.OtherError, tcp_req_exception.MaxError)) \
                else 0.4
            await asyncio.sleep(sleep_time)
            await e.conn.send_json(e.RSP_SUGGESTED)
            await e.conn.close()
            return

        if await user.user_conn.send_json({'code': 0, 'type': 'entered', 'data': {}}):
            self._receivers.append(user)
            while await user.user_conn.recv_json() is not None:
                pass
            self._receivers.remove(user)
            await user.user_conn.close()


broadcast_handler = BroadCastHandler()
loop = asyncio.get_event_loop()


@atomic
async def check_handler(request) -> web.StreamResponse:
    return await broadcast_handler.check_handler(request)


@atomic
async def create_key_handler(request) -> web.StreamResponse:
    return await broadcast_handler.create_key_handler(request)


@atomic
async def post_raffle_handler(request) -> web.StreamResponse:
    return await broadcast_handler.post_raffle_handler(request)


loop.create_task(broadcast_handler.clean_rubbish())

tcp_core = asyncio.start_server(broadcast_handler.tcp_receiver_handle, '0.0.0.0', 8002, loop=loop)
loop.run_until_complete(tcp_core)

app = web.Application()
setup(app)

app.router.add_route('GET', '/check', check_handler)
app.router.add_route('GET', '/create_key', create_key_handler)
app.router.add_route('POST', '/post_raffle', post_raffle_handler)
app.on_shutdown.append(broadcast_handler.on_shutdown)
web.run_app(app, port=8001)
