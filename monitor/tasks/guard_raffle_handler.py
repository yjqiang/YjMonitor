import asyncio

import bili_statistics
import utils
from reqs.guard_raffle_handler import GuardRaffleHandlerReq
from tasks.utils import UtilsTask
from .task_func_decorator import normal
from .base_class import ForcedTask


class GuardRafflJoinTask(ForcedTask):
    TASK_NAME = 'join_guard_raffle'
    @staticmethod
    async def check(user, real_roomid, raffle_id=None):
        if raffle_id is not None:
            json_rsp = {'data': [{'id': raffle_id, 'time': 65}]}
        else:
            for i in range(10):
                json_rsp = await user.req_s(GuardRaffleHandlerReq.check, user, real_roomid)
                # print(json_rsp)
                if json_rsp['data']:
                    break
                await asyncio.sleep(1)
            else:
                print(f'{real_roomid}没有guard或者guard已经领取')
                return
        next_step_settings = []
        data = json_rsp['data']
        max_raffleid = max([int(i['id']) for i in data])
        for j in data:
            raffle_id = j['id']
            # 总督长达一天，额外处理
            max_wait = min(j['time'] - 20, 240)
            if not bili_statistics.is_raffleid_duplicate(raffle_id) and raffle_id > max_raffleid - 30:
                print('本次获取到的抽奖id为', raffle_id)
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
    @normal
    async def work(user, raffle_data: dict):
        await UtilsTask.send2yj_monitor(user, raffle_data)
