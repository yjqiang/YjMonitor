from printer import info as print
import bili_statistics
from .bili_danmu import WsDanmuClient
from tasks.storm_raffle_handler import StormRaffleJoinTask
from tasks.lotteries_raffle_handler import LotteriesRaffleJoinTask
from tasks.anchor_raffle_handler import AnchorRaffleJoinTask
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
                if raffle_name != '总督':
                    print(f'{self._area_id}号数据连接检测到{real_roomid:^9}的提督/舰长（API0）')
                    raffle_handler.push2queue(LotteriesRaffleJoinTask, real_roomid, 5)
                    bili_statistics.add2pushed_raffles('提督/舰长（API0）', broadcast_type=2)
        elif cmd == 'GUARD_MSG':
            if 'buy_type' in data and data['buy_type'] != 1:
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的提督/舰长（API1）')
                raffle_handler.push2queue(LotteriesRaffleJoinTask, self._room_id, 5)
                bili_statistics.add2pushed_raffles('提督/舰长（API1）', broadcast_type=2)
        elif cmd == "USER_TOAST_MSG":  # 这个 api 有明显的瞎 jb 乱报现象，即报了，但没有
            if data['data']['guard_level'] != 1:
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的提督/舰长（API2）')
                raffle_handler.push2queue(LotteriesRaffleJoinTask, self._room_id, 5)
                bili_statistics.add2pushed_raffles('提督/舰长（API2）', broadcast_type=2)
        elif cmd == "GUARD_BUY":
            if data['data']['guard_level'] != 1:
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的提督/舰长（API3）')
                raffle_handler.push2queue(LotteriesRaffleJoinTask, self._room_id, 5)
                bili_statistics.add2pushed_raffles('提督/舰长（API3）', broadcast_type=2)
        elif cmd == 'PK_LOTTERY_START':
            print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的PK大乱斗')
            raffle_handler.exec_at_once(LotteriesRaffleJoinTask, self._room_id, data['data']['pk_id'])
            bili_statistics.add2pushed_raffles('PK大乱斗', broadcast_type=2)
        elif cmd == 'GUARD_LOTTERY_START':
            if data['data']['privilege_type'] != 1:
                print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的提督/舰长（API4）')
                raffle_handler.push2queue(LotteriesRaffleJoinTask, self._room_id, 5)
                bili_statistics.add2pushed_raffles('提督/舰长（API4）', broadcast_type=2)
        elif cmd == 'ANCHOR_LOT_START':
            data = data['data']
            print(f'{self._area_id}号数据连接检测到{self._room_id:^9}的天选抽奖')
            raffle_handler.exec_at_once(AnchorRaffleJoinTask, self._room_id, data['id'], data['time'], data)
            bili_statistics.add2pushed_raffles('天选抽奖', broadcast_type=2)

        return True
