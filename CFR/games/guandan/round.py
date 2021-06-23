# -*- coding: utf-8 -*-
""" Implement Guandan Round class
"""

import functools
import numpy as np
import random
import sys

from CFR.games.guandan.utils import cards2str
from CFR.games.guandan.utils import CARD_RANK, CARD_RANK_STR, CARD_RANK_STR_INDEX
from CFR.games.base import Card
from CFR.games.guandan import Dealer

sys.setrecursionlimit(15000)

class GuandanRound:
    """ Round can call other Classes' functions to keep the game running
    """

    def __init__(self, np_random, played_cards, officer):
        self.np_random = np_random
        self.played_cards = played_cards
        self.officer = officer
        self.trace = []

        self.greater_player = None
        self.dealer = Dealer(self.np_random, self)
        self.deck_str = cards2str(self.dealer.deck)
        self.seen_cards = ""
        self.winner_group = None
        self.winners = []
        self.tribute_cards = None
        self.tribute_players = None
        self.detribute = False

    def initiate(self, players, winner_group, winners):
        """
        初始化一轮
        Args:
            :param officer:
            :param winners: 上一小局玩家出完牌的顺序
            :param players: 所有玩家列表
            :param winner_group: 上一小局获胜的组
        """
        self.players = players
        # 上轮赢的组
        self.winner_group = winner_group
        self.winners = winners

        self.dealer.init(self.players)
        # 如果是游戏的第一小局，随机选择一个玩家开始游戏
        if not self.winner_group:
            self.current_player = random.randint(0, 3)
        # 否则进贡
        else:
            # TODO 还贡
            self.current_player, self.detribute = self.pay_tribute()
        self.public = {'deck': self.deck_str, 'seen_cards': self.seen_cards,
                       'winner_group': self.winner_group, 'trace': self.trace,
                       'played_cards': None}

    @staticmethod
    def cards_ndarray_to_str(ndarray_cards):
        # print(ndarray_cards)
        result = ''
        for cards in ndarray_cards:
            _result = []
            for i, _ in enumerate(cards):
                if cards[i] != 0:
                    _result.extend([CARD_RANK_STR[i]] * cards[i])
            result += ''.join(_result)
        return result

    # 更新当前轮
    def update_public(self, action):
        """
        Update public trace and played cards
        Args:
            action(str): string of legal specific action
        """
        # 出牌记录
        self.trace.append((self.current_player, action))
        # 如果当前玩家出牌
        if action != 'pass':
            # 当前玩家出的牌
            # print(action)
            for c in action:
                self.played_cards[self.current_player][CARD_RANK_STR_INDEX[c]] += 1
                # 如果出的是进贡或者还贡的牌，去掉seen_cards
                if c == self.players[self.current_player].tribute_card:
                    self.seen_cards = self.seen_cards.replace(c, '')
                    self.public['seen_cards'] = self.seen_cards
            self.public['played_cards'] = self.cards_ndarray_to_str(self.played_cards)

    # 进行一轮
    def proceed_round(self, player, action):
        """
        Call other Classes's functions to keep one round running
        Args:
            player (object): object of Player
            action (str): string of legal specific action
        Returns:
            object of Player: player who played current biggest cards.
        """
        self.update_public(action)
        # 出牌
        self.greater_player = player.play(action, self.greater_player)
        return self.greater_player

    # 回退到上一步
    def step_back(self, players):
        """
        Reverse the last action
        Args:
            players (list): list of Player objects
        Returns:
            The last player id and the cards played
        """
        # 上一步玩家和出牌出栈
        player_id, cards = self.trace.pop()
        # 回到上一个玩家
        self.current_player = player_id
        # 如果上一个玩家出了牌
        if cards != 'pass':
            for card in cards:
                # self.played_cards.remove(card)
                # 出牌数量-1
                self.played_cards[player_id][CARD_RANK_STR_INDEX[card]] -= 1
            self.public['played_cards'] = self.cards_ndarray_to_str(self.played_cards)
        # 找到上一个出牌的玩家
        greater_player_id = self.find_last_greater_player_id_in_trace()
        # 如果之前有玩家出牌
        if greater_player_id is not None:
            # 上一个出牌的玩家
            self.greater_player = players[greater_player_id]
        else:
            self.greater_player = None
        return player_id, cards

    # 找到出牌最大的玩家
    def find_last_greater_player_id_in_trace(self):
        """ Find the last greater_player's id in trace
        Returns:
            The last greater_player's id in trace
        """
        for i in range(len(self.trace) - 1, -1, -1):
            _id, action = self.trace[i]
            # 找到最后一个出牌的玩家
            if action != 'pass':
                return _id
        return None

    # 找到玩家上一轮出的牌
    def find_last_played_cards_in_trace(self, player_id):
        """
        Find the player_id's last played_cards in trace
        Returns:
            The player_id's last played_cards in trace
        """
        for i in range(len(self.trace) - 1, -1, -1):
            _id, action = self.trace[i]
            if _id == player_id and action != 'pass':
                return action
        return None

    # 按照牌的大小排序
    def sort_card(self, card_1, card_2):
        """ Compare the rank of two cards of Card object

        Args:
            card_1 (object): object of Card
            card_2 (object): object of card
            :param current_officer: 当前的参谋
        """
        key = []
        for card in [card_1, card_2]:
            # print(card)
            if card.rank == '':
                key.append(CARD_RANK.index(card.suit))
            else:
                key.append(CARD_RANK.index(card.rank))

        # #  如果card_1是参谋且card_2不是参谋和大小鬼
        # if card_1.rank == self.officer and card_2.rank != self.officer and key[1] < 13:
        #     return 1
        # # 如果card_2是参谋且card_1不是参谋和大小鬼
        # if card_2.rank == self.officer and card_1.rank != self.officer and key[0] < 13:
        #     return -1

        if key[0] > key[1]:
            return 1
        if key[0] < key[1]:
            return -1
        return 0

    # 进贡
    def pay_tribute(self):
        """
        :return: 下一步进发出动作的玩家，是否为还贡
        """
        # 单贡
        if self.winners >= 3:
            # 进贡的玩家
            tribute_player = None
            # 还牌的玩家
            detribute_player = self.winners[0]
            for player in self.players:
                if player.player_id not in self.winners:
                    tribute_player = player.player_id
                    break
            # 如果抓到2个大王，则抗贡
            if tribute_player.count_RJ() == 2:
                self.seen_cards = cards2str([Card("RJ", ""), Card("RJ", "")])
                # 上游出牌
                return self.winners[0], False
            else:

                self.tribute_cards = [tribute_player.get_tribute_card(self.officer)]
                seen_cards = self.tribute_cards
                seen_cards.sort(key=functools.cmp_to_key(self.sort_card))
                self.seen_cards = cards2str(seen_cards)
                self.tribute_players = [tribute_player]
                # 上游玩家还贡
                return self.winners[0], True
        # 双上
        elif self.winners == 2:
            tribute_players = []
            for player in self.players:
                if player.player_id not in self.winners:
                    tribute_players.append(player)
            # 双下抓到两张大王，抗贡
            if tribute_players[0].count_RJ() + tribute_players[1].count_RJ >= 2:
                return self.winners[0], False
            else:
                self.tribute_cards.append(tribute_players[0].get_tribute_card())
                self.tribute_cards.append(tribute_players[1].get_tribute_card())
                seen_cards = self.tribute_cards
                seen_cards.sort(key=functools.cmp_to_key(self.sort_card))
                self.seen_cards = cards2str(seen_cards)
                self.tribute_players = tribute_players
                # 还贡
                return self.winners[0], True
