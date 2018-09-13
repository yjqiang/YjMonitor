from statistics import Statistics
from rafflehandler import Rafflehandler
import asyncio
from cmd import Cmd
    
              
class Biliconsole(Cmd):
    prompt = ''

    def __init__(self, loop):
        self.loop = loop
        Cmd.__init__(self)
        
    def guide_of_console(self):
        print('___________________________')
        print('| 欢迎使用本控制台           |')
        print('|1 输出本次抽奖统计          |')
        print('￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣')
        
    def default(self, line):
        self.guide_of_console()
        
    def emptyline(self):
        self.guide_of_console()
        
    def do_1(self, line):
        Statistics.getlist()
        Statistics.getresult()
        
    def do_check(self, line):
        Rafflehandler.getlist()
        Statistics.checklist()
        
    def append2list_console(self, request):
        asyncio.run_coroutine_threadsafe(self.excute_async(request), self.loop)
        # inst.loop.call_soon_threadsafe(inst.queue_console.put_nowait, request)
        
    async def excute_async(self, i):
        if isinstance(i, list):
            # 对10号单独简陋处理
            for j in range(len(i[0])):
                if isinstance(i[0][j], list):
                    # print('检测')
                    i[0][j] = await i[0][j][1](*(i[0][j][0]))
            if i[1] == 'normal':
                i[2](*i[0])
            else:
                await i[1](*i[0])
        else:
            await i()
    
    
    
