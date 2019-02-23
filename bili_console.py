import bili_statistics
import asyncio
import notifier
from cmd import Cmd
import getopt
          
              
class Biliconsole(Cmd):
    prompt = ''
    
    def __init__(self, loop):
        self.loop = loop
        super().__init__()
    
    def guide_of_console(self):
        print(' ＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿ ')
        print('|　　　欢迎使用本控制台　　　　　　　|')
        print('|　１　输出本次统计数据　　　　　　　|')
        print(' ￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣ ')
        
    def default(self, line):
        self.guide_of_console()
        
    def emptyline(self):
        self.guide_of_console()
        
    # pattern = '-u:-p:' u(user_id):0,1…;n(num);p(point)指roomid(烂命名因为-r不合适)
    def parse(self, arg, pattern, default_u=0, set_roomid=False):
        args = arg.split()
        try:
            opts, args = getopt.getopt(args, pattern)
        except getopt.GetoptError:
            return []
        dict_results = {opt_name: opt_value for opt_name, opt_value in opts}
        
        opt_names = pattern.split(':')[:-1]
        results = []
        for opt_name in opt_names:
            opt_value = dict_results.get(opt_name)
            if opt_name == '-u':
                if opt_value is not None and opt_value.isdigit():
                    results.append(int(opt_value))
                else:
                    results.append(default_u)
                    # -2是一个灾难性的东西
                    # results.append(-2)
            elif opt_name == '-n':
                if opt_value is not None and opt_value.isdigit():
                    results.append(int(opt_value))
                else:
                    results.append(0)
            else:
                results.append(opt_value)
        return results
                
    def do_1(self, arg):
        id, = self.parse(arg, '-u:')
        self.exec_func_threads(bili_statistics.coroutine_print_statistics, [id])
        
    # threads指thread safe
    def exec_notifier_func_threads(self, *args):
        asyncio.run_coroutine_threadsafe(self.exec_notifier_func(*args), self.loop)
        
    def exec_func_threads(self, *args):
        asyncio.run_coroutine_threadsafe(self.exec_func(*args), self.loop)
        
    def exec_task_threads(self, *args):
        asyncio.run_coroutine_threadsafe(self.exec_task(*args), self.loop)
        
    # 这里args设置为list
    async def exec_notifier_func(self, id, func, args):
        for i, arg in enumerate(args):
            if isinstance(arg, list):
                args[i] = await notifier.exec_func(*arg)
        await notifier.exec_func(id, func, *args)

    async def exec_func(self, func, args):
        for i, arg in enumerate(args):
            if isinstance(arg, list):
                args[i] = await notifier.exec_func(*arg)
        await func(*args)
        
    async def exec_task(self, id, task, step, args):
        for i, arg in enumerate(args):
            if isinstance(arg, list):
                args[i] = await notifier.exec_func(*arg)
        notifier.exec_task(id, task, step, *args)
        
    
    
    
