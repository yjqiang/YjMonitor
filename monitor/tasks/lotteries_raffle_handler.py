import asyncio

import bili_statistics
import utils
from reqs.lotteries_raffle_handler import LotteriesRaffleHandlerReq
from tasks.utils import UtilsTask
from .base_class import Forced, DontWait, Multi


class LotteriesRaffleJoinTask(Forced, DontWait, Multi):  # 负责push
    TASK_NAME = 'join_lotteries_raffle'

    @staticmethod
    async def check(user, real_roomid, sleep_time=0):
        await asyncio.sleep(sleep_time)  # 人为延迟
        json_rsp = await user.req_s(LotteriesRaffleHandlerReq.check, user, real_roomid)

        next_step_settings = []
        for raffle in json_rsp['data']['guard']:
            raffle_id = raffle['id']
            max_wait = raffle['time']
            privilege_type = raffle['privilege_type']

            if privilege_type != 1 and max_wait >= 30 \
                    and (not bili_statistics.is_raffleid_duplicate(raffle_id)):
                print('本次获取到的大航海抽奖id为', raffle_id)
                raffle_data = {
                    'raffle_id': raffle_id,
                    'room_id': real_roomid,
                    'raffle_type': 'GUARD',
                    'end_time': max_wait + utils.curr_time()
                }
                next_step_setting = (-2, (0, 0), raffle_data)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)

        for raffle in json_rsp['data']['pk']:
            raffle_id = raffle['id']
            max_wait = raffle['time']

            if max_wait >= 20 and (not bili_statistics.is_raffleid_duplicate(raffle_id)):
                print('本次获取到的大乱斗抽奖id为', raffle_id)
                raffle_data = {
                    'raffle_id': raffle_id,
                    'room_id': real_roomid,
                    'raffle_type': 'GUARD',
                    'end_time': max_wait + utils.curr_time()
                }
                next_step_setting = (-2, (0, 0), raffle_data)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
        return next_step_settings

    @staticmethod
    async def work(user, raffle_data: dict):
        bili_statistics.add2joined_raffles(raffle_data['raffle_type'], user.id)
        await UtilsTask.send2yj_monitor(user, raffle_data)


class LotteriesRaffleLoadTask(Forced, DontWait, Multi):  # 负责load即保存数据，不会push
    TASK_NAME = 'load_lotteries_raffle'

    @staticmethod
    async def check(_, __, raffle_id):
        if not bili_statistics.is_raffleid_duplicate(raffle_id):
            print('本次收录到的抽奖id为', raffle_id)
            bili_statistics.add2raffle_ids(raffle_id)
        return None

    # 永远不会执行
    @staticmethod
    async def work():
        pass
