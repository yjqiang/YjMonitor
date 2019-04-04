import bili_statistics
from tasks.utils import UtilsTask


class StormRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return StormRaffleHandlerTask.check
        if step == 1:
            return StormRaffleHandlerTask.send
        return None

    # 为了速度，有时不用等room_id验证就参加,置room_id为0，is_normal_room自然会返回固定值true
    @staticmethod
    async def check(user, room_id, raffle_id):
        json_rsp = {'data': {'id': raffle_id}}
        next_step_settings = []
        data = json_rsp['data']
        if data:
            raffle_id = int(data['id'])
            if not bili_statistics.is_raffleid_duplicate(raffle_id):
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (1, (0, 0), -3, room_id, raffle_id)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
        return next_step_settings
            
    @staticmethod
    async def send(user, room_id, raffle_id):
        raffle_type = 0
        await UtilsTask.send_danmu(user, room_id, raffle_id, raffle_type)
