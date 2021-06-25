ENG2CH = {
    "Single": "单张",
    "Pair": "对子",
    "Trips": "三张",
    "ThreePair": "三连对",
    "ThreeWithTwo": "三带二",
    "TwoTrips": "钢板",
    "Straight": "顺子",
    "StraightFlush": "同花顺",
    "Bomb": "炸弹",
    "PASS": "过"
}


class Action(object):
    def __init__(self):
        self.action = []
        self.act_range = -1

    def parse(self, message):
        self.action = message['actionList']
        self.act_range = message['indexRange']
        print(self.action)
        print("可选动作范围为0至{}".format(self.act_range))

    def available_actions(self):
        return self.action
