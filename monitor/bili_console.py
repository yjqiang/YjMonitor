import bili_statistics
import asyncio
from typing import Optional
from cmd import Cmd
import getopt


class FuncCore:
    def __init__(self, function, *args):
        self.function = function
        self.args = args

    async def exec(self):
        args = list(self.args)
        # 递归
        for i, arg in enumerate(args):
            if isinstance(arg, FuncCore):
                args[i] = await arg.exec()
        if asyncio.iscoroutinefunction(self.function):
            return await self.function(*args)
        return self.function(*args)


def convert2int(orig) -> Optional[int]:
    try:
        return int(orig)
    except (ValueError, TypeError):
        return None


class BiliConsole(Cmd):
    prompt = ''
    
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        super().__init__()
    
    @staticmethod
    def guide_of_console():
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
                int_value = convert2int(opt_value)
                if int_value is not None:
                    results.append(int_value)
                else:
                    results.append(default_u)
                    # -2是一个灾难性的东西
                    # results.append(-2)
            elif opt_name == '-n':
                int_value = convert2int(opt_value)
                if int_value is not None:
                    results.append(int_value)
                else:
                    results.append(0)
            else:
                results.append(opt_value)
        return results
                
    def do_1(self, arg):
        user_id, = self.parse(arg, '-u:')
        self.exec_func_threads(
            FuncCore(bili_statistics.print_statistics, user_id))

    # 直接执行，不需要user_id
    def exec_func_threads(self, func_core: FuncCore):
        asyncio.run_coroutine_threadsafe(self.exec_func(func_core), self.loop)

    @staticmethod
    async def exec_func(func_core: FuncCore):
        await func_core.exec()
