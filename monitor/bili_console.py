import asyncio
import re
import argparse
from cmd import Cmd
from distutils.util import strtobool

import bili_statistics


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


class ArgumentParserError(Exception):
    pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    # https://github.com/python/cpython/blob/3.7/Lib/argparse.py
    def exit(self, status=0, message=None):
        raise ArgumentParserError(message)

    def error(self, message):
        raise ArgumentParserError(message)


class BiliConsole(Cmd):
    PARSE_RE = re.compile(r'(--\w{2,})/(-[A-Za-z]) {(int|str|bool|room_id)(?:\?(\S*|%\S+))?}')
    prompt = ''

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

        # || 用于分割，其中首个是标号，后面是全是一个个参数
        # 参数格式是"--长指令/-短指令 {参数类型?默认值}"，其中默认值可以省略
        self.__parser_1 = self.compile_parser('1 || --user_id/-u {int?0}')

        super().__init__()

    def compile_parser(self, text: str) -> ThrowingArgumentParser:
        entries = [entry.strip() for entry in text.split('||')]
        result = ThrowingArgumentParser(prog=entries[0], add_help=False)
        for entry in entries[1:]:
            long_ctrl, short_ctrl, str_value_type, default = self.PARSE_RE.fullmatch(entry).groups()
            # print(f'{long_ctrl}, {short_ctrl}, {str_value_type}, {default}')
            if default is None:
                required = True
                help_msg = f'(必填: 类型 {str_value_type})'
            else:
                required = False
                help_msg = f'(可缺: 类型 {str_value_type} 默认 %(default)s)'

            if str_value_type == 'int':
                convert = self.str2int
            elif str_value_type == 'bool':
                convert = self.str2bool
            else:  # 其他的忽略，全部为str
                convert = str
            result.add_argument(long_ctrl, short_ctrl, required=required, help=help_msg, default=default, type=convert)
        return result

    @staticmethod
    def parse(arg: str, parser: ThrowingArgumentParser):
        try:
            result = parser.parse_args(arg.split())
            # print('parse_result', result, parser)
            return tuple(vars(result).values())
        except ArgumentParserError as e:
            print('解析错误', e)
            parser.print_help()
            raise

    @staticmethod
    def str2int(orig: str) -> int:
        return int(orig)

    @staticmethod
    def str2bool(orig: str) -> bool:
        return bool(strtobool(orig))

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

    def onecmd(self, *args, **kwargs):
        try:
            return super().onecmd(*args, **kwargs)
        except ArgumentParserError:
            # print('test_onecmd', args, kwargs)
            pass

    def postcmd(self, stop, line):
        # print('test_post_cmd', stop, line)
        if line == 'EOF':
            return True
        # 永远不退出
        return None

    def do_1(self, arg):
        user_id, = self.parse(arg, self.__parser_1)
        self.exec_func_threads(
            FuncCore(bili_statistics.print_statistics, user_id))

    # 直接执行，不需要user_id
    def exec_func_threads(self, func_core: FuncCore):
        asyncio.run_coroutine_threadsafe(self.exec_func(func_core), self.loop)

    @staticmethod
    async def exec_func(func_core: FuncCore):
        await func_core.exec()
