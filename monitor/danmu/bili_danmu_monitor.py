from printer import info as print
import bili_statistics
from .bili_danmu import WsDanmuClient
from tasks.storm_raffle_handler import StormRaffleJoinNoReqTask
from tasks.pk_raffle_handler import PkRaffleJoinNoReqTask
from tasks.anchor_raffle_handler import AnchorRaffleJoinNoReqTask
from tasks.tv_raffle_handler import TVRaffleJoinNoReqTask
from tasks.guard_raffle_handler import GuardRaffleJoinNoReqTask
from . import raffle_handler


class DanmuRaffleMonitor(WsDanmuClient):
    def handle_danmu(self, data: dict):
        if 'cmd' in data:
            cmd = data['cmd']
        elif 'msg' in data:
            data = data['msg']
            cmd = data['cmd']
        else:
            return True  # 预防未来sbb站

        if cmd == 'SPECIAL_GIFT':
            if 'data' in data and '39' in data['data'] and data['data']['39']['action'] == 'start':
                data = data['data']['39']
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的节奏风暴')
                raffle_handler.exec_at_once(StormRaffleJoinNoReqTask, self._room_id, data)
                bili_statistics.add2pushed_raffles('节奏风暴', broadcast_type=2)
                print(data)
        elif cmd == 'PK_LOTTERY_START':
            data = data['data']
            print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的大乱斗')
            raffle_handler.exec_at_once(PkRaffleJoinNoReqTask, self._room_id, data)
            bili_statistics.add2pushed_raffles('大乱斗', broadcast_type=2)
        elif cmd == 'GUARD_LOTTERY_START':
            data = data['data']['lottery']
            print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的大航海（API4）')
            raffle_handler.exec_at_once(GuardRaffleJoinNoReqTask, self._room_id, data)
            bili_statistics.add2pushed_raffles('大航海（API4）', broadcast_type=2)
        elif cmd == 'ANCHOR_LOT_START':
            data = data['data']
            print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的天选抽奖')
            raffle_handler.exec_at_once(AnchorRaffleJoinNoReqTask, self._room_id, data)
            bili_statistics.add2pushed_raffles('天选抽奖', broadcast_type=2)
        elif cmd == 'RAFFLE_START':
            data = data['data']
            # 33地图-GIFT_30405 .
            # 小电视图-GIFT_30406 .
            # 蘑菇别跑-GIFT_30448 .
            tv_type = data['type']
            if tv_type in ('GIFT_30405', 'GIFT_30406', 'GIFT_30448'):
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的小电视({tv_type})')
                raffle_handler.exec_at_once(TVRaffleJoinNoReqTask, self._room_id, data)
                bili_statistics.add2pushed_raffles('小电视', broadcast_type=2)
        '''
        elif cmd == 'NOTICE_MSG':
            msg_type = data['msg_type']
            real_roomid = data['real_roomid']
            msg_common = data['msg_common'].replace(' ', '')
            msg_common = msg_common.replace('”', '')
            msg_common = msg_common.replace('“', '')
            if msg_type == 3:
                raffle_name = msg_common.split('开通了')[-1][:2]
                if raffle_name != '总督':
                    print(f'{self._area_id}号数据连接检测到{real_roomid:^9}的提督/舰长（API0）')
                    # raffle_handler.push2queue(LotteriesRaffleJoinTask, real_roomid, 5)
                    bili_statistics.add2pushed_raffles('提督/舰长（API0）', broadcast_type=2)
        elif cmd == 'GUARD_MSG':
            if 'buy_type' in data and data['buy_type'] != 1:
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的提督/舰长（API1）')
                # raffle_handler.push2queue(LotteriesRaffleJoinTask, self._room_id, 5)
                bili_statistics.add2pushed_raffles('提督/舰长（API1）', broadcast_type=2)
        '''
        return True
