import asyncio
import bili_statistics
from reqs.guard_raffle_handler import GuardRaffleHandlerReq
from tasks.utils import UtilsTask


class GuardRaffleHandlerTask:
    @staticmethod
    def target(step):
        if step == 0:
            return GuardRaffleHandlerTask.check
        if step == 1:
            return GuardRaffleHandlerTask.send
        return None
        
    @staticmethod
    async def check(user, real_roomid):
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
        for j in json_rsp['data']:
            raffle_id = int(j['id'])
            # 总督长达一天，额外处理
            max_wait = min(j['time'] - 15, 6)
            # 特殊的过滤，即id相差过大，就认为很老了，不再重复
            if not bili_statistics.is_raffleid_duplicate(raffle_id) and raffle_id > max_raffleid - 25:
                print('本次获取到的抽奖id为', raffle_id)
                next_step_setting = (1, (0, max_wait), -3, real_roomid, raffle_id)
                next_step_settings.append(next_step_setting)
                bili_statistics.add2raffle_ids(raffle_id)
        return next_step_settings
        
    @staticmethod
    async def send(user, room_id, raffle_id):
        raffle_type = 1
        await UtilsTask.send_danmu(user, room_id, raffle_id, raffle_type)
