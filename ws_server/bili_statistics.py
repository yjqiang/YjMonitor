import attr


@attr.s(slots=True)
class DuplicateChecker:
    LIST_SIZE_LIMITED = 1500
    CLEAN_LIST_CYCLE = 350

    number = attr.ib(
        default=0,
        validator=attr.validators.instance_of(int))
    ids = attr.ib(
        factory=list,
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(int),
            iterable_validator=attr.validators.instance_of(list)))

    def add2checker(self, new_id: int, need_check_duplicated: bool = True) -> bool:
        if need_check_duplicated and self.is_duplicated(new_id):
            return False
        self.number += 1
        self.ids.append(new_id)
        # 定期清理，防止炸掉
        if len(self.ids) > self.CLEAN_LIST_CYCLE + self.LIST_SIZE_LIMITED:
            del self.ids[:self.CLEAN_LIST_CYCLE]
        return True

    def is_duplicated(self, new_id: int):
        return new_id in self.ids

    def result(self):
        return f'一共 {self.number} 个几乎不重复的 id'
