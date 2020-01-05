import bili_statistics
import utils
from tasks.utils import UtilsTask
from .base_class import Forced, DontWait, Multi


class AnchorRaffleJoinTask(Forced, DontWait, Multi):  # 负责push
    TASK_NAME = 'join_anchor_raffle'

    @staticmethod
    async def check(_, real_roomid, raffle_id, max_wait, other_raffle_data):

        next_step_settings = []

        if not bili_statistics.is_raffleid_duplicate(raffle_id):
            print('本次获取到的天选抽奖id为', raffle_id)
            raffle_data = {
                'raffle_id': raffle_id,
                'room_id': real_roomid,
                'raffle_type': 'ANCHOR',
                'end_time': max_wait + utils.curr_time(),
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
