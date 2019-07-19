from typing import Dict
from operator import itemgetter

import attr

from utils import curr_time


@attr.s(slots=True)
class Poster:  # 推送人是一个poster
    user_name = attr.ib(validator=attr.validators.instance_of(str))
    user_latest_post_time = attr.ib(validator=attr.validators.instance_of(int))


class Posters:  # 管理posters的状态
    __slots__ = ('_posters',)

    def __init__(self):
        self._posters: Dict[str, Poster] = {}

    def update(self, name: str) -> None:  # 有该用户更新时间；如果没有该用户，就create新的
        if name in self._posters:
            self._posters[name].user_latest_post_time = curr_time()
        else:
            poster = Poster(user_name=name, user_latest_post_time=curr_time())
            self._posters[name] = poster

    def count(self) -> list:
        return [(key, poster.user_latest_post_time) for key, poster in
                sorted(self._posters.items(), key=itemgetter(0))]

    def clean_safely(self) -> None:
        int_curr_time = curr_time()
        # 过滤删除过于久远的
        self._posters = {key: poster for key, poster in self._posters.items()
                         if poster.user_latest_post_time + 12 * 3600 > int_curr_time}


posters = Posters()
