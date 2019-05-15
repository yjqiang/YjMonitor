from printer import info as print
import bili_statistics
from .bili_danmu import WsDanmuClient
from tasks.guard_raffle_handler import GuardRafflJoinTask
from tasks.storm_raffle_handler import StormRaffleJoinTask
from . import raffle_handler


class DanmuRaffleMonitor(WsDanmuClient):
    def handle_danmu(self, data: dict):
        cmd = data['cmd']

        if cmd == 'SPECIAL_GIFT':
            if 'data' in data and '39' in data['data'] and data['data']['39']['action'] == 'start':
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的节奏风暴')
                raffle_handler.exec_at_once(StormRaffleJoinTask, self._room_id, data['data']['39']['id'])
                bili_statistics.add2pushed_raffles('节奏风暴', broadcast_type=2)

        elif cmd == 'GUARD_MSG':
            if 'buy_type' in data and data['buy_type'] != 1:
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的提督/舰长')
                raffle_handler.exec_at_once(GuardRafflJoinTask, self._room_id)
                bili_statistics.add2pushed_raffles('提督/舰长', broadcast_type=2)

        return True
