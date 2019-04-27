import sys
import asyncio


# windows应该启用这个eventloop，cpython3.8才默认启用(mdzz)，uvloop windows暂不支持，别想了
if sys.platform == 'win32':
    asyncio.set_event_loop(asyncio.ProactorEventLoop())

