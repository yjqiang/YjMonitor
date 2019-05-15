import bili_statistics
from reqs.storm_raffle_handler import StormRaffleHandlerReq
from tasks.utils import UtilsTask
from .task_func_decorator import normal
from .base_class import ForcedTask


class StormRaffleJoinTask(ForcedTask):
    TASK_NAME = 'join_storm_raffle'
    # 为了速度，有时不用等room_id验证就参加,置room_id为0，is_normal_room自然会返回固定值true
    @staticmethod
    async def check(user, room_id, raffle_id=None):
        if raffle_id is not None:
            json_rsp = {'data': {'id': raffle_id}}
        else:
            json_rsp = await user.req_s(StormRaffleHandlerReq.check, user, room_id)
        next_step_settings = []
        data = json_rsp['data']
        if data:
            raffle_id = data['id']
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                raffle_data = {
                    'raffle_id': raffle_id,
                    'room_id': room_id,
                    'raffle_type': 'STORM',
                    'end_time': 0
                }
                next_step_setting = (-2, (0, 0), raffle_data)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
        return next_step_settings
            
    @staticmethod
    @normal
    async def work(user, raffle_data: dict):
        await UtilsTask.send2yj_monitor(user, raffle_data)
