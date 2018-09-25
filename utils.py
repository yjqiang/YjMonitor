
import time
import printer
from bilibili import bilibili
from configloader import ConfigLoader
import asyncio


def CurrentTime():
    currenttime = int(time.time())
    return str(currenttime)

async def send_danmu_msg_web(msg, roomId):
    async def check_send(msg, roomId):
        while True:
            json_response = await bilibili.request_send_danmu_msg_web(msg, roomId)
            if not json_response['code'] and not json_response['msg']:
                print(f'已发送弹幕{msg}到{roomId}')
                return True
            elif not json_response['code'] and json_response['msg'] == '内容非法':
                print('检测非法反馈, 正在进行下一步处理', msg)
                return False
            else:
                print(json_response, msg)
            await asyncio.sleep(2)
            
    def add_special_str(msg):
        list_str = [i+'?' for i in msg]
        return ''.join(list_str)
        
    half_len = int(len(msg) / 2)
    l = msg[:half_len]
    r = msg[half_len:]
    new_l = add_special_str(msg[:half_len])
    new_r = add_special_str(msg[half_len:])
    list_danmu = [msg, new_l+r, l+new_r, new_l+new_r]
    print('本轮次测试弹幕群', list_danmu)
    for i in list_danmu:
        print('_________________________________________')
        if await check_send(i, roomId):
            return
    print('发送失败，请反馈', roomId, msg)
    
    
async def enter_room(roomid):
    json_response = await bilibili.request_check_room(roomid)

    if not json_response['code']:
        data = json_response['data']
        param1 = data['is_hidden']
        param2 = data['is_locked']
        param3 = data['encrypted']
        if any((param1, param2, param3)):
            printer.info([f'抽奖脚本检测到房间{roomid:^9}为异常房间'], True)
            printer.warn(f'抽奖脚本检测到房间{roomid:^9}为异常房间')
            return False
        else:
            # print('房间为真')
            # await bilibili.post_watching_history(roomid)
            return True
            
            
async def getRecommend():
    async def fetch_room(url):
        roomidlist = []
        flag = 0
        for x in range(1, 200):
            try:
                json_data = await bilibili().get_roomids(url, x)
                if not json_data['data']:
                    flag += 1
                if flag > 3:
                    print(x)
                    break
                for room in json_data['data']:
                    roomidlist.append(room['roomid'])
                    # print(room['roomid'])
            except:
                print(url, x)
        print(len(roomidlist))
        unique_list = []
        for id in roomidlist:
            if id not in unique_list:
                unique_list.append(id)
        return unique_list

    urls = [
        'http://api.live.bilibili.com/area/liveList?area=all&order=online&page=',
        'http://api.live.bilibili.com/room/v1/room/get_user_recommend?page=',
    ]

    roomlist0 = await fetch_room(urls[0])
    roomlist1 = await fetch_room(urls[1])
    len_0 = len(roomlist0)
    len_1 = len(roomlist1)
    print(len_0, len_1)
    unique_list = []
    len_sum = (min(len_0, len_1))
    for i in range(len_sum):
        id0 = roomlist0[i]
        id1 = roomlist1[i]
        if id0 not in unique_list:
            unique_list.append(id0)
        if id1 not in unique_list:
            unique_list.append(id1)
    print(f'总获取房间{len(unique_list)}')
    
    roomid_conf = ConfigLoader().list_roomid
    for i in roomid_conf:
        if i not in unique_list:
            unique_list.append(i)
        if len(unique_list) == 6000:
            break
    print(f'总获取房间{len(unique_list)}')
    return unique_list + [0] * (6000 - len(unique_list))


