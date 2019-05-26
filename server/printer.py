import sys
import time


class Printer:
    @staticmethod
    def timestamp():
        return time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())

    def infos(self, list_msgs, need_timestamp):
        if need_timestamp:
            print(self.timestamp(), end=' ')
        if list_msgs:
            print(list_msgs[0])
            for i in list_msgs[1:]:
                print(f'# {i}')
        else:
            print('NULL')

    def info(self, *objects, need_timestamp):
        if need_timestamp:
            print(self.timestamp(), end=' ')
        if objects:
            print(objects[0])
            for i in objects[1:]:
                print(f'# {i}')
        else:
            print('NULL')

    def warn(self, *objects):
        time_stamp = self.timestamp()
        print(self.timestamp(), file=sys.stderr, end=' ')
        if objects:
            print(objects[0], file=sys.stderr)
            for i in objects[1:]:
                print(f'# {i}', file=sys.stderr)
        else:
            print('NULL', file=sys.stderr)

        with open('bili.log', 'a', encoding='utf-8') as f:
            f.write(f'{time_stamp} ')
            if objects:
                f.write(f'# {objects[0]}\n')
                for i in objects[1:]:
                    f.write(f'# {i}\n')
            else:
                f.write(f'NULL\n')

    def debug(self, *objects):
        self.warn(*objects)

    def error(self, *objects):
        self.warn(*objects)
        sys.exit(-1)


printer = Printer()


def info(*objects, need_timestamp: bool = True):
    printer.info(*objects, need_timestamp=need_timestamp)


def infos(list_msgs, need_timestamp: bool = True):
    printer.info(list_msgs, need_timestamp=need_timestamp)


def warn(*objects):
    printer.warn(*objects)


def error(*objects):
    printer.error(*objects)


def debug(*objects):
    printer.debug(*objects)
