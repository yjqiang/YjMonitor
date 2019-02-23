import bili_statistics
from tasks.utils import UtilsTask


class CheckRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return CheckRaffleHandlerTask.check
        if step == 1:
            return CheckRaffleHandlerTask.send
        return None

    # 为了速度，有时不用等room_id验证就参加,置room_id为0，is_normal_room自然会返回固定值true
    @staticmethod
    async def check(user, room_id):
        next_step_settings = []
        next_step_setting = (1, (0, 0), -3, room_id, 0)
        next_step_settings.append(next_step_setting)
        return next_step_settings
            
    @staticmethod
    async def send(user, room_id, raffle_id):
        raffle_type = -1
        await UtilsTask.send_danmu(user, room_id, raffle_id, raffle_type)
