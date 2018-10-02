class Statistics:
    __slots__ = ('pushed_raffle',)
    instance = None

    def __new__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Statistics, cls).__new__(cls, *args, **kw)
            cls.instance.pushed_raffle = {}
        return cls.instance

    @staticmethod
    def getlist():
        inst = Statistics.instance
        for k, v in inst.pushed_raffle.items():
            print(f'本次推送{k}次数: {v}')
        
    @staticmethod
    def append2pushed_raffle(type, area_id=0, num=1):
        inst = Statistics.instance
        if '摩天' in type or '金人' in type or '/' in type:
            inst.pushed_raffle[type] = inst.pushed_raffle.get(type, 0) + int(num)
        else:
            if area_id == 1:
                inst.pushed_raffle[type] = inst.pushed_raffle.get(type, 0) + int(num)

