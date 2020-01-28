import bili_statistics
from tasks.utils import UtilsTask
from .base_class import Forced, DontWait, Multi


class StormRaffleJoinNoReqTask(Forced, DontWait, Multi):
    TASK_NAME = 'join_storm_raffle'

    @staticmethod
    async def check(_, real_roomid, other_raffle_data):
        next_step_settings = []
        raffle_id = other_raffle_data['id']
        if not bili_statistics.is_raffleid_duplicate(raffle_id):
            print('本次获取到的节奏风暴抽奖id为', raffle_id)
            raffle_data = {
                'raffle_id': raffle_id,
                'room_id': real_roomid,
                'raffle_type': 'STORM',
                'end_time': 0,
                'other_raffle_data': other_raffle_data
            }
            next_step_setting = (-2, (0, 0), raffle_data)
            next_step_settings.append(next_step_setting)
            bili_statistics.add2raffle_ids(raffle_id)
        return next_step_settings
            
    @staticmethod
    async def work(user, raffle_data: dict):
        bili_statistics.add2joined_raffles(raffle_data['raffle_type'], user.id)
        await UtilsTask.send2yj_monitor(user, raffle_data)
