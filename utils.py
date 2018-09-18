
import time
import printer
from bilibili import bilibili
import asyncio


def CurrentTime():
    currenttime = int(time.time())
    return str(currenttime)

async def send_danmu_msg_web(msg, roomId):
    while True:
        json_response = await bilibili.request_send_danmu_msg_web(msg, roomId)
        print(json_response)
        if not json_response['code'] and not json_response['msg']:
            print(f'已发送弹幕{msg}到{roomId}')
            return
        await asyncio.sleep(1)
    
    
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
                print(newurl)
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
    return unique_list + [0] * (6000 - len(unique_list))

