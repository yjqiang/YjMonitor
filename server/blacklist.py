import attr
from collections import deque

import utils


@attr.s(slots=True)
class Record:
    LIST_SIZE_LIMITED = 15
    BAN_TIME = 1800
    
    key = attr.ib(validator=attr.validators.instance_of(str))
        
    # 一定是按顺序的从小到大
    times = attr.ib(init=False)

    latest_time = attr.ib(default=0, init=False)
        
    @times.default
    def _times(self):
        return deque(maxlen=Record.LIST_SIZE_LIMITED)

    # “频繁”了就设置为 true。定义是 8s 内尝试 10 次以上
    is_crazy = attr.ib(
        default=False,
        validator=attr.validators.instance_of(bool))

    # 更新记录
    def refresh(self) -> None:
        # 查看是否被 ban。如果确认，记录就冻结状态
        should_be_banned = self.should_be_banned()
        curr_time = utils.curr_time()
        self.latest_time = curr_time
        if should_be_banned:
            return

        # 更新记录
        self.times.append(curr_time)

        # 同步状态
        for i in range(len(self.times) - 9):
            # curr_time-self.times[i+9] < self.BAN_TIME 是保证记录“有效”（一万年前的频繁就不要再追究啦）
            if self.times[i+9] - self.times[i] <= 8 and curr_time-self.times[i+9] <= self.BAN_TIME:
                self.is_crazy = True
                return
        self.is_crazy = False
    
    # “频繁”，ban
    def should_be_banned(self) -> bool:
        if utils.curr_time() - self.latest_time <= self.BAN_TIME:
            return self.is_crazy
        return False


@attr.s(slots=True)
class BlackList:
    LIST_SIZE_LIMITED = 150

    records = attr.ib(init=False)
            
    @records.default
    def _records(self):
        return deque(maxlen=BlackList.LIST_SIZE_LIMITED)

    def refresh(self, ip: str) -> None:
        # 搜索 ip
        for record in self.records:
            if record.key == ip:
                record.refresh()
                return
        # 没有就创建新的
        self.records.append(Record(ip))
    
    def should_be_banned(self, ip: str) -> bool:
        # 搜索 ip
        for record in self.records:
            if record.key == ip:
                return record.should_be_banned()
        # 没有就说明清白
        return False

    def del_record(self, ip) -> None:
        for i, record in enumerate(self.records):
            if record.key == ip:
                del self.records[i]
                return

    # 完全删除
    def clear_all(self) -> None:
        del self.records[:]
