import sys
import json
import base64
import asyncio
import random
import hashlib
import string
from os import path
from time import time
from typing import Dict

import rsa
from aiohttp import web, WSMsgType

from argon2 import PasswordHasher

from db import sql
import utils
from printer import info
import json_req_exceptions
import ws_req_exceptions
from receiver import Receiver, BroadCaster
from poster import PostOffice


class BroadCastHandler:
    def __init__(self, super_admin_pubkey: rsa.PublicKey, admin_pubkey: rsa.PublicKey):
        self._super_admin_pubkey = super_admin_pubkey
        self._admin_pubkey = admin_pubkey
        self._broadcaster = BroadCaster()
        self._post_office = PostOffice()
        self._key_seed = f'{string.digits}{string.ascii_letters}!#$%&()*+,-./:;<=>?@[]^_`|~'  # 89个字符，抛弃了一些特殊字符
        self._ph = PasswordHasher()
        self._conn_list: Dict[str, int] = {}

    @staticmethod
    async def ws_test_handle(_):
        return web.json_response({'code': 0,  'type': 'test ws-server', 'data': {}})

    def _can_pass_ip_test(self, ip):
        curr_time = int(time())
        if ip in self._conn_list:
            latest_time = self._conn_list[ip]
            if -2 <= curr_time - latest_time <= 2:
                return False
            self._conn_list[ip] = curr_time
            return True
        self._conn_list = {ip: latest_time for ip, latest_time in self._conn_list.items()
                           if -10 <= curr_time - latest_time <= 10}
        self._conn_list[ip] = curr_time
        return True

    def _create_key(self, max_users: int = 3) -> str:
        while True:
            orig_key = ''.join(random.choices(self._key_seed, k=16))  # 100^16 别想着暴力了，各位
            encrypted_key = base64.b64encode(
                rsa.encrypt(orig_key.encode('utf8'), self._super_admin_pubkey)
            ).decode('utf8')
            hashed_key: str = self._ph.hash(orig_key)
            md5ed_key: str = hashlib.md5(orig_key.encode('utf-8')).hexdigest()
            if sql.is_key_addable(key_index=md5ed_key, key_value=hashed_key):
                sql.insert_element(sql.Key(
                    key_index=md5ed_key,
                    key_value=hashed_key,
                    key_created_time=utils.curr_time(),
                    key_max_users=max_users)
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
                    if -10 <= cur_time0 - cur_time1 <= 10:
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

    async def _verify_ws_req(self, rsp: web.WebSocketResponse, request) -> Receiver:
        try:
            await rsp.prepare(request)
            data = await rsp.receive()
            if data.type == WSMsgType.TEXT:  # 这段是ws的开头，需要验证key
                json_data = json.loads(data.data)
                orig_key = json_data['data']['key']
                key = sql.is_key_verified(orig_key)
                if key is not None:
                    if self._broadcaster.can_pass_max_users_test(key.key_index, key.key_max_users):
                        user = Receiver(user_rsp=rsp, user_key_index=key.key_index)
                        return user
                    else:
                        info(f'KEY({key.key_index[:5]}***...)用户过多')
                        raise ws_req_exceptions.MaxError()
                else:
                    info('有人恶意尝试KEY')
                    raise ws_req_exceptions.VerificationError()
            else:
                raise ws_req_exceptions.DataError()

        except ws_req_exceptions.WsReqError:
            raise
        except:
            raise ws_req_exceptions.OtherError()

    # 普通管理员权限
    async def check_handler(self, request):
        try:
            await self._verify_json_req(request, self._admin_pubkey)
            return web.json_response({
                'code': 0,
                'type': 'server_status',
                'data': {
                    'observers_num': f'当前用户共{self._broadcaster.num_observers()}',
                    'observers_count': self._broadcaster.count(),
                    'posters_count': self._post_office.count(),
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
            if not isinstance(max_users, int):
                raise json_req_exceptions.DataError()
            return web.json_response({'code': 0,
                                      'type': '',
                                      'data': {'encrypted_key': self._create_key(max_users)}})
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
            asyncio.ensure_future(self._broadcast_raffle(sending_json_data))
            return web.json_response({'code': 0, 'type': '', 'data': {}})
        except json_req_exceptions.JsonReqError as e:
            return web.json_response(e.RSP_SUGGESTED)

    async def on_shutdown(self, _):
        await self._broadcaster.broadcast_close()

    async def ws_receiver_handler(self, request):
        ip = request.remote
        info(f'IP({ip:^15})请求建立推送连接')
        if isinstance(ip, str) and not self._can_pass_ip_test(ip):
            info(f'拒绝来自{ip}的连接请求')
            try:
                await asyncio.sleep(3)
            except asyncio.CancelledError:
                pass
            return web.Response(status=403, body='403', content_type='application/json')

        resp = web.WebSocketResponse(heartbeat=20, receive_timeout=25)
        if not resp.can_prepare(request):
            return resp

        try:
            user = await self._verify_ws_req(resp, request)
        except ws_req_exceptions.WsReqError as e:
            try:
                await resp.send_json(e.RSP_SUGGESTED)
                await resp.close()
            except:
                pass
            return resp

        self._broadcaster.append(user)
        info(f'IP({ip:^15})用户{user.user_key_index[:5]}加入')

        try:
            await resp.send_json({'code': 0, 'type': 'entered', 'data': {}})
            while True:
                msg = await resp.receive()
                if msg.type == WSMsgType.TEXT:
                    info(json.loads(msg.data))
                else:
                    info('接受到ws数据', user, msg)
                    return resp
        except asyncio.CancelledError:
            # aiohttp正常逻辑（反正就会中断。。。）
            return resp
        except:
            info(sys.exc_info()[0], sys.exc_info()[1])
            return resp
        finally:
            self._broadcaster.remove(user)
            info(f'用户{user.user_key_index[:5]}删除')
            # https://aiohttp.readthedocs.io/en/stable/web_advanced.html#web-handler-cancellation
            await asyncio.shield(resp.close())


def main():
    key_path = f'{path.dirname(path.realpath(__file__))}/key'
    with open(f'{key_path}/super_admin_pubkey.pem', 'rb') as f:
        super_admin_pubkey = rsa.PublicKey.load_pkcs1(f.read())
    with open(f'{key_path}/admin_pubkey.pem', 'rb') as f:
        admin_pubkey = rsa.PublicKey.load_pkcs1(f.read())

    broadcast_handler = BroadCastHandler(
        super_admin_pubkey=super_admin_pubkey,
        admin_pubkey=admin_pubkey)

    app = web.Application()
    app.router.add_route('GET', '/ws_test', broadcast_handler.ws_test_handle)
    app.router.add_route('GET', '/check', broadcast_handler.check_handler)
    app.router.add_route('GET', '/create_key', broadcast_handler.create_key_handler)
    app.router.add_route('POST', '/post_raffle', broadcast_handler.post_raffle_handler)
    app.router.add_route('GET', '/ws', broadcast_handler.ws_receiver_handler)
    app.on_shutdown.append(broadcast_handler.on_shutdown)
    web.run_app(app, port=8001)


if __name__ == '__main__':
    main()
