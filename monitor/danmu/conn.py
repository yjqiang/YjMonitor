import json
import asyncio
from typing import Optional, Any
from urllib.parse import urlparse

from aiohttp import ClientSession, WSMsgType


class Conn:
    # receive_timeout 推荐为heartbeat间隔加10/5
    def __init__(self, receive_timeout: Optional[float] = None):
        self._receive_timeout = receive_timeout

    async def open(self) -> bool:
        return False

    async def close(self) -> bool:
        return True

    # 用于永久close之后一些数据清理等
    async def clean(self):
        pass

    async def send_bytes(self, bytes_data) -> bool:
        return True

    async def read_bytes(self) -> Optional[bytes]:
        return None

    async def read_json(self) -> Any:
        return None


class TcpConn(Conn):
    # url 格式 tcp://hostname:port
    def __init__(self, url: str, receive_timeout: Optional[float] = None):
        super().__init__(receive_timeout)
        result = urlparse(url)
        assert result.scheme == 'tcp'
        self._host = result.hostname
        self._port = result.port
        self._reader = None
        self._writer = None

    async def open(self) -> bool:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=15)
        except asyncio.TimeoutError:
            return False
        except Exception as e:
            print(e)
            return False
        return True

    async def close(self) -> bool:
        if self._writer is not None:
            self._writer.close()
            # py3.7 才有（妈的你们真的磨叽）
            # await self._writer.wait_closed()
        return True

    async def clean(self):
        pass

    async def send_bytes(self, bytes_data) -> bool:
        try:
            self._writer.write(bytes_data)
            await self._writer.drain()
        except asyncio.CancelledError:
            return False
        except Exception as e:
            print(e)
            return False
        return True

    async def read_bytes(
            self,
            n: Optional[int] = None) -> Optional[bytes]:
        if n is None or n <= 0:
            return b''
        try:
            bytes_data = await asyncio.wait_for(
                self._reader.readexactly(n), timeout=self._receive_timeout)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            print(e)
            return None

        return bytes_data

    async def read_json(
            self,
            n: Optional[int] = None) -> Any:
        data = await self.read_bytes(n)
        if not data:
            return None
        try:
            dict_data = json.loads(data.decode('utf8'))
        except Exception as e:
            print(e)
            return None
        return dict_data
