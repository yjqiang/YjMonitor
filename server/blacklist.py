import attr
from collections import deque

import utils


@attr.s(slots=True)
class Record:
    LIST_SIZE_LIMITED = 15
    BAN_TIME = 3600
    
    key = attr.ib(
        validator=attr.validators.instance_of(str))
        
    # 一定是按顺序的从小到大
    times = attr.ib(
        factory=deque,
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(int),
            iterable_validator=attr.validators.instance_of(deque)))

    latest_time = attr.ib(
        default=0,
        validator=attr.validators.instance_of(int))

    # “频繁”了就设置为 true。仅与 times 有关。定义是 7s 内尝试 10 次以上
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
        if len(self.times) >= self.LIST_SIZE_LIMITED:
            self.times.popleft()
        self.times.append(curr_time)

        # 同步状态
        for i in range(len(self.times) - 9):
            if self.times[i] - self.times[i + 9] <= 7:
                self.is_crazy = True
                break
    
    # “频繁”，ban 600s
    def should_be_banned(self) -> bool:
        if utils.curr_time() - self.latest_time <= self.BAN_TIME:
            return self.is_crazy
        return False

    # 是否可以直接删除了
    def can_be_clean_safely(self) -> bool:
        return utils.curr_time() - self.latest_time >= self.BAN_TIME + 300


@attr.s(slots=True)
class BlackList:
    LIST_SIZE_LIMITED = 120
    CLEAN_LIST_CYCLE = 30

    records = attr.ib(
        factory=list,
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Record),
            iterable_validator=attr.validators.instance_of(list)))

    def refresh(self, ip: str) -> None:
        for record in self.records:
            if record.key == ip:
                record.refresh()
                return
        self.records.append(Record(ip))
        # 定期清理，防止炸掉
        if len(self.records) > self.CLEAN_LIST_CYCLE + self.LIST_SIZE_LIMITED:
            del self.records[:self.CLEAN_LIST_CYCLE]
    
    def should_be_banned(self, ip: str) -> bool:
        for record in self.records:
            if record.key == ip:
                return record.should_be_banned()
        return False

    def del_record(self, ip) -> None:
        for i, record in enumerate(self.records):
            if record.key == ip:
                del self.records[i]
                return

    # 完全删除
    def clear_all(self) -> None:
        del self.records[:]
