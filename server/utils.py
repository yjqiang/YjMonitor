from time import time
import hashlib
from functools import lru_cache


def curr_time():
    return int(time())


@lru_cache(maxsize=25)
def naive_hash(orig_key: str):  # 快速哈希，目的用于数据快速查找等，不考虑安全！！很容易碰撞
    return hashlib.md5(orig_key.encode('utf-8')).hexdigest()[:16]
