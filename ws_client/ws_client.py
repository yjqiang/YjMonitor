import asyncio
import sys
import aiohttp
import json


class YjMonitorConn:
    def __init__(self, key, loop=None):
        self._is_sharing_session = False
        self._session = aiohttp.ClientSession()
        self._ws = None

        if loop is not None:
            self._loop = loop
        else:
            self._loop = asyncio.get_event_loop()
        self._key = key

        self._conn_lock = asyncio.Lock()
        self._task_main = None
        self._waiting = None
        self._closed = False

    async def _send_json(self, json_data):
        try:
            await self._ws.send_json(json_data)
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0])
            return False
        return True

    async def _read_json(self):
        try:
            # 如果调用aiohttp的bytes read，none的时候，会raise exception
            # timeout目的是b站30s间隔的心跳包会有确认返回，如果没了，当然就是gg
            data = await self._ws.receive()
            if data.type == aiohttp.WSMsgType.TEXT:
                return json.loads(data.data)
            return None
        except:
            print(sys.exc_info()[0])
            return None

    async def _open_conn(self):
        try:
            url = 'ws://127.0.0.1:8001/ws'
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(url, heartbeat=20, receive_timeout=25), timeout=3)
        except asyncio.TimeoutError:
            print('连接超时')
            return False
        except:
            print("连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0])
            return False
        print('弹幕监控已连接服务器')

        return await self._send_json({'code': 0, 'type': 'ask', 'data': {'key': self._key}})

    # 看了一下api，这玩意儿应该除了cancel其余都是暴力处理的，不会raise
    async def _close_conn(self):
        await self._ws.close()

    async def _read_datas(self):
        while True:
            json_data = await self._read_json()
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if json_data is None:
                return
            data_type = json_data['type']
            if data_type == 'raffle':
                if not self.handle_danmu(json_data['data']):
                    return
            # 握手确认
            elif data_type == 'entered':
                print(f'确认监控已经连接')
            elif data_type == 'error':
                print(f'发生致命错误{json_data}')
                await asyncio.sleep(3)

    @staticmethod
    def handle_danmu(body):
        print('raffle', body)
        return True

    async def run_forever(self):
        self._waiting = self._loop.create_future()
        while not self._closed:
            print(f'正在启动弹幕姬')
            async with self._conn_lock:
                if self._closed:
                    break
                if not await self._open_conn():
                    continue
                self._task_main = asyncio.ensure_future(self._read_datas())
            tasks = [self._task_main]
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            print(f'弹幕姬异常或主动断开，正在处理剩余信息')
            await self._close_conn()
            if pending:
                await asyncio.wait(pending)
            print(f'弹幕姬退出，剩余任务处理完毕')
        self._waiting.set_result(True)

    async def close(self):
        if not self._closed:
            self._closed = True
            async with self._conn_lock:
                if self._ws is not None:
                    await self._close_conn()
            if self._waiting is not None:
                await self._waiting
            if not self._is_sharing_session:
                await self._session.close()
            return True
        else:
            return False


async def run():
    await YjMonitorConn(key='').run_forever()


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(run())
loop.close()
