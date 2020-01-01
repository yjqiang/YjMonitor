from collections import deque

import attr


@attr.s(slots=True)
class DuplicateChecker:
    LIST_SIZE_LIMITED = 3000

    number = attr.ib(default=0, init=False)
    ids = attr.ib(init=False)

    @ids.default
    def _ids(self):
        return deque(maxlen=DuplicateChecker.LIST_SIZE_LIMITED)

    def add2checker(self, new_id: int, need_check_duplicated: bool = True) -> bool:
        if need_check_duplicated and self.is_duplicated(new_id):
            return False
        self.number += 1
        self.ids.append(new_id)
        return True

    def is_duplicated(self, new_id: int):
        return new_id in self.ids

    def result(self):
        return f'一共 {self.number} 个几乎不重复的 id'
