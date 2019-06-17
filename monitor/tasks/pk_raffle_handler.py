import bili_statistics
from reqs.pk_raffle_handler import PkRaffleHandlerReq
from tasks.utils import UtilsTask
from .task_func_decorator import normal
from .base_class import ForcedTask
import utils


class PkRaffleJoinTask(ForcedTask):
    TASK_NAME = 'join_pk_raffle'
    # 这是superuser做的,做完之后就broadcast
    @staticmethod
    async def check(user, real_roomid, raffle_id=None):
        if raffle_id is not None:
            json_response = {'data': [{'id': raffle_id, 'time': 110}]}
        else:
            json_response = await user.req_s(PkRaffleHandlerReq.check, user, real_roomid)
        # print(json_response['data']['list'])
        list_raffles = json_response['data']
        if not list_raffles:  # sb可能返回None
            return None
        next_step_settings = []
        for raffle in list_raffles:
            raffle_id = raffle['id']
            max_wait = raffle['time']
            # 处理一些重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                raffle_data = {
                    'raffle_id': raffle_id,
                    'room_id': real_roomid,
                    'raffle_type': 'PK',
                    'end_time': utils.curr_time() + max_wait
                }
                next_step_setting = (-2, (0, 0), raffle_data)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
                
        return next_step_settings
        
    @staticmethod
    @normal
    async def work(user, raffle_data: dict):
        bili_statistics.add2joined_raffles('大乱斗(合计)', user.id)
        await UtilsTask.send2yj_monitor(user, raffle_data)