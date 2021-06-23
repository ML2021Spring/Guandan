# -*- coding: utf-8 -*-
''' Implement Guandan Player class
'''
import functools

from CFR.games.guandan.utils import get_gt_cards,sort_card
from CFR.games.guandan.utils import cards2str


class GuandanPlayer:
    """
    Player can store cards in the player's hand and the role,
    determine the actions can be made according to the rules,
    and can perfrom corresponding action
    """

    def __init__(self, player_id, np_random):
        ''' Give the player an id in one game
        Args:
            player_id (int): the player_id of a player
        Notes:
            当前轮该玩家出的牌
            1. played_cards: The cards played in one round
            玩家初始的牌
            2. hand: Initial cards
            当前玩家手上的牌
            3. _current_hand: The rest of the cards after playing some of them
        '''
        self.np_random = np_random
        self.player_id = player_id
        self.initial_hand = None
        self._current_hand = []
        self.played_cards = None
        self.singles = '23456789TJQKABR'
        self.tribute_card = None

        # record cards removed from self._current_hand for each play()
        # and restore cards back to self._current_hand when play_back()
        # 每一轮玩家出的牌
        self._recorded_played_cards = []

    # 当前手上的牌
    @property
    def current_hand(self):
        return self._current_hand

    def set_current_hand(self, value):
        self._current_hand = value

    def get_state(self, public, others_hands, num_cards_left, actions):
        state = {}
        state['seen_cards'] = public['seen_cards']
        state['trace'] = public['trace'].copy()
        state['played_cards'] = public['played_cards']
        state['self'] = self.player_id
        state['current_hand'] = cards2str(self._current_hand)
        state['others_hand'] = others_hands
        state['num_cards_left'] = num_cards_left
        state['legal_actions'] = actions

        return state

    # 获取当前可以进行的动作
    def available_actions(self, officer, h_officer_num, greater_player=None, judger=None):
        """
        Get the actions can be made based on the rules
        Args:
            打出当前最大牌的玩家
            greater_player (Player object): player who played current biggest cards.
            judger (Judger object): object of Judger
        Returns:
            list: list of string of actions. Eg: ['pass', '8', '9', 'T', 'J']
        """
        # 之前没有玩家出牌或者自己打出最大牌
        if greater_player is None or greater_player.player_id == self.player_id or len(greater_player.current_hand)==0:
            # 获得当前可以执行的动作
            actions = judger.get_playable_cards(self)
            # print("1",actions)
        # 获得比上一位玩家更大的牌
        else:
            actions = get_gt_cards(self, greater_player,officer,h_officer_num )
        return actions

    # 出牌
    def play(self, action, greater_player=None):
        # print(self.player_id,action)
        # print(self._current_hand)
        # print(len(self._recorded_played_cards))
        """
        Perfrom action
        Args:
            action (string): specific action
            greater_player (Player object): The player who played current biggest cards.
        Returns:
            object of Player: If there is a new greater_player, return it, if not, return None
        """
        # 大小王
        trans = {'B': 'BJ', 'R': 'RJ'}
        # 不出牌
        if action == 'pass':
            # 历史为空
            self._recorded_played_cards.append([])
            return greater_player
        # 出牌
        else:
            removed_cards = []
            # 历史动作
            self.played_cards = action
            for play_card in action:
                # 如果是大小王 B->BJ R->RJ
                if play_card in trans:
                    play_card = trans[play_card]
                # 当前手上的牌
                for _, remain_card in enumerate(self._current_hand):
                    # 2-A
                    if remain_card.rank != '':
                        remain_card = remain_card.rank
                    # 大小鬼
                    else:
                        remain_card = remain_card.suit
                    # print(self.player_id, "current hand", cards2str(self._current_hand))
                    # 移除当前出的牌
                    if play_card == remain_card:
                        removed_cards.append(self.current_hand[_])
                        self._current_hand.remove(self._current_hand[_])
                        # print(self.player_id, "current hand", cards2str(self._current_hand))
                        break
            # 记录当前轮出的牌
            self._recorded_played_cards.append(removed_cards)
            return self

    # 悔牌
    def play_back(self):
        """
        Restore recorded cards back to self._current_hand
        """
        # 悔牌
        removed_cards = self._recorded_played_cards.pop()
        # 加入当前手上的牌
        self._current_hand.extend(removed_cards)
        # 对当前手上的牌排序
        self._current_hand.sort(key=functools.cmp_to_key(sort_card))

    # 当前手上大王的数量
    def count_RJ(self):
        cnt = 0
        for card in self._current_hand:
            if card.suit == 'RJ':
                cnt += 1
        return cnt

    # 获取当前玩家进贡的牌
    def get_tribute_card(self, officer):
        greatest_card = self._current_hand[-1]
        tribute_card = None
        # 进贡除了红心参谋以外最大的牌
        if greatest_card.rank == officer and greatest_card.suit == 'H':
            tribute_card = self._current_hand[-2]
            self._current_hand.remove(tribute_card)
            return tribute_card
        else:
            tribute_card = self._current_hand[-1]
            self._current_hand.remove(tribute_card)
            return tribute_card

    def set_tribute_card(self, card):
        self.tribute_card = card
