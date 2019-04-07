import asyncio
import struct
import sys
import json


class YjMonitorConn:
    structer = struct.Struct('!I')

    def __init__(self, key, loop=None):
        self._key = key
        if loop is not None:
            self._loop = loop
        else:
            self._loop = asyncio.get_event_loop()
        
        # 建立连接过程中难以处理重设置房间或断线等问题
        self._conn_lock = asyncio.Lock()
        self._task_main = None
        self._waiting = None
        self._closed = False
        self._bytes_heartbeat = self._encapsulate(str_body='')
        
    def _encapsulate(self, str_body):
        body = str_body.encode('utf-8')
        len_body = len(body)
        header = self.structer.pack(len_body)
        return header + body

    async def _send_bytes(self, bytes_data):
        try:
            self._writer.write(bytes_data)
            await self._writer.drain()
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0])
            return False
        return True

    async def _read_bytes(self, n):
        if n <= 0:
            return b''
        try:
            bytes_data = await asyncio.wait_for(
                self._reader.readexactly(n), timeout=40)
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0])
            return None
                
        return bytes_data
        
    async def _open_conn(self):
        try:
            url = '192.168.0.107'
            port = 8002
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(url, port), timeout=10)
        except asyncio.TimeoutError:
            print('连接超时')
            return False
        except:
            print("连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0])
            return False
        print(f'弹幕监控已连接服务器')
    
        dict_enter = {
            'code': 0,
            'type': 'ask',
            'data': {'key': self._key}
            }
        str_enter = json.dumps(dict_enter)
        bytes_enter = self._encapsulate(str_body=str_enter)
        
        return await self._send_bytes(bytes_enter)
        
    async def _close_conn(self):
        self._writer.close()
        # py3.7 才有（妈的你们真的磨叽）
        # await self._writer.wait_closed()
        
    async def _heart_beat(self):
        try:
            while True:
                if not await self._send_bytes(self._bytes_heartbeat):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            return
            
    async def _read_datas(self):
        while True:
            header = await self._read_bytes(4)
            if header is None:
                return
            
            # 每片data都分为header和body，data和data可能粘连
            # data_l == header_l && next_data_l == next_header_l
            # ||header_l...header_r|body_l...body_r||next_data_l...
            len_body, = self.structer.unpack_from(header)
            
            body = await self._read_bytes(len_body)
            if body is None:
                return
            
            if not body:
                continue
            json_data = json.loads(body.decode('utf-8'))
            # 人气值(或者在线人数或者类似)以及心跳
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
                
    def handle_danmu(self, body):
        print(body)
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
                task_heartbeat = asyncio.ensure_future(self._heart_beat())
            tasks = [self._task_main, task_heartbeat]
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            print('弹幕姬异常或主动断开，正在处理剩余信息')
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self._close_conn()
            await asyncio.wait(pending)
            print('弹幕姬退出，剩余任务处理完毕')
        self._waiting.set_result(True)
            
    async def close(self):
        if not self._closed:
            self._closed = True
            async with self._conn_lock:
                if self._writer is not None:
                    await self._close_conn()
            if self._waiting is not None:
                await self._waiting
            return True
        else:
            return False
            
            
async def run():
    await YjMonitorConn(key='').run_forever()


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(run())
loop.close()
