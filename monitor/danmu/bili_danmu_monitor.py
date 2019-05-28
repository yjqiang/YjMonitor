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

        elif cmd == 'NOTICE_MSG':
            msg_type = data['msg_type']
            real_roomid = data['real_roomid']
            msg_common = data['msg_common'].replace(' ', '')
            msg_common = msg_common.replace('”', '')
            msg_common = msg_common.replace('“', '')
            if msg_type == 3:
                raffle_name = msg_common.split('开通了')[-1][:2]
                print(f'{self._area_id}号数据连接检测到{real_roomid:^9}的{raffle_name}')
                if raffle_name != '总督':
                    raffle_handler.push2queue(GuardRafflJoinTask, real_roomid)
                    bili_statistics.add2pushed_raffles(raffle_name, broadcast_type=2)

        return True
