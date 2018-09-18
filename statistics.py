class Statistics:
    __slots__ = ('activity_id_list', 'TV_id_list', 'result', 'pushed_raffle', 'joined_raffle')
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Statistics, cls).__new__(cls, *args, **kw)
            cls.instance.activity_id_list = []
            # cls.instance.activity_time_list = []
            cls.instance.TV_id_list = []
            # cls.instance.TV_time_list = []
            cls.instance.pushed_raffle = {}
            
            cls.instance.joined_raffle = {}
            cls.instance.result = {}
            # cls.instance.TVsleeptime = 185
            # cls.instance.activitysleeptime = 125
        return cls.instance

    @staticmethod
    def add_to_result(type, num):
        inst = Statistics.instance
        inst.result[type] = inst.result.get(type, 0) + int(num)

    @staticmethod
    def getlist():
        inst = Statistics.instance
        for k, v in inst.pushed_raffle.items():
            print(f'本次推送{k}次数: {v}')
            
        print()
        for k, v in inst.joined_raffle.items():
            print(f'本次参与{k}次数: {v}')

    @staticmethod
    def getresult():
        inst = Statistics.instance
        print('本次参与抽奖结果为：')
        for k, v in inst.result.items():
            print(f'{k}X{v}')

    @staticmethod
    def append_to_activitylist(raffleid, text1, time=''):
        inst = Statistics.instance
        inst.activity_id_list.append((text1, raffleid))
        # inst.activity_time_list.append(int(time))
        # inst.activity_time_list.append(int(CurrentTime()))
        inst.append2joined_raffle('活动(合计)')
        # print("activity加入成功", inst.joined_event)

    @staticmethod
    def append_to_TVlist(raffleid, real_roomid, time=''):
        inst = Statistics.instance
        inst.TV_id_list.append((real_roomid, raffleid))
        # inst.TV_time_list.append(int(time)+int(CurrentTime()))
        # inst.TV_time_list.append(int(CurrentTime()))
        inst.append2joined_raffle('小电视(合计)')
        # print("tv加入成功", inst.joined_TV)
        
    @staticmethod
    def append_to_captainlist():
        inst = Statistics.instance
        inst.append2joined_raffle('总督(合计)')
        
    @staticmethod
    def append2joined_raffle(type, num=1):
        inst = Statistics.instance
        inst.joined_raffle[type] = inst.joined_raffle.get(type, 0) + int(num)
        
    @staticmethod
    def append2pushed_raffle(type, area_id=0, num=1):
        inst = Statistics.instance
        if '摩天' in type or '金人' in type or '/' in type:
            inst.pushed_raffle[type] = inst.pushed_raffle.get(type, 0) + int(num)
        else:
            if area_id == 1:
                inst.pushed_raffle[type] = inst.pushed_raffle.get(type, 0) + int(num)
                    
    @staticmethod
    def check_TVlist(real_roomid, raffleid):
        inst = Statistics.instance
        if (real_roomid, raffleid) not in inst.TV_id_list:
            return True
        return False

    @staticmethod
    def check_activitylist(real_roomid, raffleid):
        inst = Statistics.instance
        if (real_roomid, raffleid) not in inst.activity_id_list:
            return True
        return False
        
    @staticmethod
    def checklist():
        print('目前activity任务队列状况:', Statistics.instance.activity_id_list)
        print('TV:', Statistics.instance.TV_id_list)
