import copy
import asyncio
import hashlib
from itertools import count
from typing import Optional

import printer
import conf_loader
import exceptions
from web_session import WebSession
from tasks.login import LoginTask


class User:
    _ids = count(0)
    __slots__ = (
        'id', 'name', 'password', 'alias',

        'bililive_session', 'login_session', 'other_session',

        'dict_bili', 'app_params',
        '_waiting_login', '_loop'
    )

    def __init__(
            self, dict_user: dict, dict_bili: dict):
        self.id = next(self._ids)
        self.name = dict_user['username']
        self.password = dict_user['password']
        self.alias = dict_user.get('alias', self.name)

        self.bililive_session = WebSession()
        self.login_session = WebSession()
        self.other_session = WebSession()

        # 每个user里面都分享了同一个dict，必须要隔离，否则更新cookie这些的时候会互相覆盖
        self.dict_bili = copy.deepcopy(dict_bili)
        self.app_params = [
            f'actionKey={dict_bili["actionKey"]}',
            f'appkey={dict_bili["appkey"]}',
            f'build={dict_bili["build"]}',
            f'device={dict_bili["device"]}',
            f'mobi_app={dict_bili["mobi_app"]}',
            f'platform={dict_bili["platform"]}',
        ]
        self.update_login_data(dict_user)

        self._waiting_login = None
        self._loop = asyncio.get_event_loop()

    def update_login_data(self, login_data):
        for i, value in login_data.items():
            self.dict_bili[i] = value
            if i == 'cookie':
                self.dict_bili['pcheaders']['cookie'] = value
                self.dict_bili['appheaders']['cookie'] = value
        conf_loader.write_user(login_data, self.id)

    def is_online(self):
        return self.dict_bili['pcheaders']['cookie'] and self.dict_bili['appheaders']['cookie']

    def info(
            self,
            *objects,
            with_userid=True,
            **kwargs):
        if with_userid:
            printer.info(
                *objects,
                **kwargs,
                extra_info=f'用户id:{self.id} 名字:{self.alias}')
        else:
            printer.info(*objects, **kwargs)

    def infos(self):
        pass

    def warn(self, *objects, **kwargs):
        printer.warn(
            *objects,
            **kwargs,
            extra_info=f'用户id:{self.id} 名字:{self.alias}')

    def sort_and_sign(self, extra_params: Optional[list] = None) -> str:
        if extra_params is None:
            text = "&".join(self.app_params)
        else:
            text = "&".join(sorted(self.app_params+extra_params))
        text_with_appsecret = f'{text}{self.dict_bili["app_secret"]}'
        sign = hashlib.md5(text_with_appsecret.encode('utf-8')).hexdigest()
        return f'{text}&sign={sign}'

    async def req_s(self, func, *args):
        while True:
            if self._waiting_login is None:
                try:
                    return await func(*args)
                except exceptions.LogoutError:  # logout
                    if self._waiting_login is None:  # 当前没有处理的运行
                        self.info('判定出现了登陆失败，且未处理')
                        self._waiting_login = self._loop.create_future()
                        try:
                            await LoginTask.handle_login_status(self)
                            self.info('已经登陆了')
                        except asyncio.CancelledError:  # 登陆中取消，把waiting_login设置，否则以后的req会一直堵塞
                            raise
                        finally:
                            self._waiting_login.set_result(-1)
                            self._waiting_login = None
                    else:  # 已有处理的运行了
                        self.info('判定出现了登陆失败，已经处理')
                        await self._waiting_login
                except exceptions.ForbiddenError:
                    await asyncio.sleep(600)  # 这里简单sleep
            else:
                await self._waiting_login

    def print_status(self):
        self.info('当前用户的状态：', None)
