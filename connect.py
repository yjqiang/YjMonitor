import asyncio
import utils
from bilibiliCilent import bilibiliClient
import printer

        
class RaffleConnect():
    
    def __init__(self, areaid, roomid=0):
        self.danmuji = None
        self.roomid = roomid
        self.areaid = areaid
        
    async def run(self):
        self.danmuji = bilibiliClient(0, self.areaid)
        self.danmuji.set_real_room(self.roomid)
        while True:
            printer.info(['# 正在启动抽奖监控弹幕姬'], True)
            time_start = int(utils.CurrentTime())
            connect_results = await self.danmuji.connectServer()
            # print(connect_results)
            if not connect_results:
                continue
            task_main = asyncio.ensure_future(self.danmuji.ReceiveMessageLoop())
            task_heartbeat = asyncio.ensure_future(self.danmuji.HeartbeatLoop())
            
            finished, pending = await asyncio.wait([task_main, task_heartbeat], return_when=asyncio.FIRST_COMPLETED)

            printer.info([f'{self.areaid}号弹幕姬异常或主动断开，正在处理剩余信息'], True)
            time_end = int(utils.CurrentTime())
            if not task_heartbeat.done():
                task_heartbeat.cancel()
           
            task_terminate = asyncio.ensure_future(self.danmuji.close_connection())
            await asyncio.wait(pending)
            await asyncio.wait([task_terminate])
            printer.info([f'{self.areaid}号弹幕姬退出，剩余任务处理完毕'], True)
            if time_end - time_start < 5:
                print('# 当前网络不稳定，为避免频繁不必要尝试，将自动在5秒后重试')
                await asyncio.sleep(5)
            
    async def reconnect(self, roomid):
        print(f'{self.areaid}已经切换roomid')
        self.roomid = roomid
        if self.danmuji is not None:
            self.danmuji.set_real_room(roomid)
            await self.danmuji.close_connection()

            
            

        
                    
