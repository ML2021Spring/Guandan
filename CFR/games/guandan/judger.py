# -*- coding: utf-8 -*-
''' Implement Judger class
'''
import numpy as np
import collections
from itertools import combinations
from bisect import bisect_left
import functools

from CFR.games.guandan.utils import CARD_RANK_STR, CARD_RANK_STR_INDEX
from CFR.games.guandan.utils import cards2str, contains_cards


class GuandanJudger:
    """ Determine what cards a player can play
    """

    def __init__(self, players, np_random, officer):
        """
        Initilize the Judger class
        """
        # 4位玩家
        # 当前可以出的牌
        self.playable_cards = [set() for _ in range(4)]
        # 已经出过的牌
        self._recorded_removed_playable_cards = [[] for _ in range(4)]
        self.officer = officer
        for player in players:
            player_id = player.player_id
            # 玩家当前手上的牌
            current_hand = cards2str(player.current_hand)
            # 当前可以出的牌型
            self.playable_cards[player_id] = self.playable_cards_from_hand(current_hand, player.current_hand)

    # 单张顺子
    def solo_chain(self, indexes_list, h_officer_num):
        """
        Find chains for solos
        Args:
            indexes_list: the indexes of cards those have the same count, the count could be 1, 2, or 3.
        Returns:
            list of tuples: [(start_index1, length1), (start_index1, length1), ...]
            :param h_officer_num:
            :param indexes_list:
        """
        chains = []
        for m in range(len(indexes_list)):
            count = 1
            start = indexes_list[m][0]
            prev_index = start
            left_officer = h_officer_num
            officer_index = []
            n = m + 1
            while n < len(indexes_list):
                i = indexes_list[n]
                if count >= 5:
                    break
                if i[0] > 12:  # no chains for 'BR'
                    break
                if i[0] == prev_index + 1 or (prev_index == 12 and i[0] == 0 and count == 1):  # 连续；A可以放在顺子的开头
                    count += 1
                    n += 1
                # 如果中断  可以使用红心参谋替代
                elif left_officer > 0:
                    count += 1
                    left_officer -= 1
                    prev_index += 1
                    officer_index.append(count - 1)
                else:
                    break
                # solo_chain_5
            if count == 5:
                chains.append((start, count, officer_index.copy()))
                for chain in arrange_solo(start, count, officer_index):
                    chains.append(chain)
            elif count < 5 and left_officer + count >= 5:
                for n in range(count, 5):
                    officer_index.append(n)
                chains.append((start, 5, officer_index))
                for chain in arrange_solo(start, 5, officer_index):
                    chains.append(chain)
        return chains

    # 对子顺子
    def pair_chain_indexes(self, indexes_list, h_officer_num, one_index_list):
        """
        Find chains for pairs_chain_3
        Args:
            indexes_list: the indexes of cards those have the same count, the count could be 1, 2, or 3.
        Returns:
            list of tuples: [(start_index1, length1), (start_index1, length1), ...]
            :param h_officer_num:
            :param indexes_list:
        """
        chains = []
        for m in range(len(indexes_list)):
            count = 1
            start = indexes_list[m][0]
            prev_index = start
            left_officer = h_officer_num
            officer_index = []
            n = m + 1
            while n < len(indexes_list):
                i = indexes_list[n]
                if count >= 3:
                    break
                if i[0] > 12:  # no chains for 'BR'
                    break
                if i[0] == prev_index + 1 or (prev_index == 12 and i[0] == 0 and count == 1):  # 连续；A可以放在顺子的开头
                    count += 1
                    n += 1
                # 如果中断  可以使用红心参谋替代
                elif prev_index + 1 in one_index_list and left_officer > 0:
                    count += 1
                    left_officer -= 1
                    prev_index += 1
                    officer_index.append(count - 1)
                elif prev_index + 1 not in one_index_list and left_officer >= 2:
                    count += 1
                    left_officer -= 2
                    prev_index += 1
                    officer_index += [count - 1, count - 1]
                else:
                    break
            # pair_chain_3
            if count == 3:
                chains.append((start, count, officer_index.copy()))
                for chain in arrange_pair(start, count, officer_index):
                    chains.append(chain)
            elif count < 3 and left_officer / 2 + count >= 3:
                for n in range(count, 3):
                    officer_index.append(n)
                chains.append((start, 3, officer_index))
                for chain in arrange_pair(start, 3, officer_index):
                    chains.append(chain)
        return chains

    # 三张顺子
    def trio_chain_indexes(self, indexes_list, h_officer_num, one_index_list, two_index_list):
        """
        Find chains for trios
        Args:
            indexes_list: the indexes of cards those have the same count, the count could be 1, 2, or 3.
        Returns:
            list of tuples: [(start_index1, length1), (start_index1, length1), ...]
            :param two_index_list:
            :param one_index_list:
            :param h_officer_num:
            :param indexes_list:
        """
        chains = []
        for m in range(len(indexes_list)):
            count = 1
            start = indexes_list[m][0]
            prev_index = start
            left_officer = h_officer_num
            officer_index = []
            n = m + 1
            while n < len(indexes_list):
                i = indexes_list[n]
                if count >= 2:
                    break
                if i[0] > 12:  # no chains for 'BR'
                    break
                if i[0] == prev_index + 1 or (prev_index == 12 and i[0] == 0 and count == 1):  # 连续；A可以放在顺子的开头
                    count += 1
                    n += 1
                # 如果中断  可以使用红心参谋替代
                elif prev_index + 1 in two_index_list and left_officer > 0:
                    count += 1
                    left_officer -= 1
                    prev_index += 1
                    officer_index.append(count - 1)
                elif prev_index + 1 in one_index_list and left_officer >= 2:
                    count += 1
                    left_officer -= 2
                    prev_index += 1
                    officer_index += [count - 1, count - 1]
                else:
                    break
            # trio_chain_2
            if count == 2:
                chains.append((start, count, officer_index.copy()))
        return chains

    # 查找当前可以出的牌
    def playable_cards_from_hand(self, current_hand, cards_list):
        """ Get playable cards from hand
        Returns:
            set: set of string of playable cards
        """
        h_officer = self.count_heart_officer(cards_list)

        cards_dict = collections.defaultdict(int)
        for card in current_hand:
            cards_dict[card] += 1
        cards_count = np.array([cards_dict[k] for k in CARD_RANK_STR])
        playable_cards = set()

        # 当前有的牌
        non_zero_indexes = np.argwhere(cards_count > 0)
        # 大于一张的牌
        more_than_1_indexes = np.argwhere(cards_count > 1)
        # 大于两张的牌
        more_than_2_indexes = np.argwhere(cards_count > 2)
        # 大于三张的牌
        more_than_3_indexes = np.argwhere(cards_count > 3)

        # solo
        for i in non_zero_indexes:
            playable_cards.add(CARD_RANK_STR[i[0]])
        # pair
        for i in more_than_1_indexes:
            playable_cards.add(CARD_RANK_STR[i[0]] * 2)
        if h_officer >= 1:
            for i in non_zero_indexes:
                if CARD_RANK_STR.index(self.officer) > i[0]:
                    playable_cards.add(CARD_RANK_STR[i[0]] + self.officer)
                else:
                    playable_cards.add(self.officer + CARD_RANK_STR[i[0]])

        # bomb
        for i in more_than_3_indexes:
            for j in range(4, cards_count[i[0]] + 1):
                cards = CARD_RANK_STR[i[0]] * j
                playable_cards.add(cards)
        #
        if h_officer == 1:
            for i in more_than_2_indexes:
                for j in range(3, cards_count[i[0]] + 1):
                    if CARD_RANK_STR.index(self.officer) > i[0]:
                        cards = CARD_RANK_STR[i[0]] * j + self.officer
                    else:
                        cards = self.officer + CARD_RANK_STR[i[0]] * j
                    playable_cards.add(cards)

        if h_officer == 2:
            for i in more_than_1_indexes:
                for j in range(2, cards_count[i[0]] + 1):
                    if CARD_RANK_STR.index(self.officer) > i[0]:
                        cards = CARD_RANK_STR[i[0]] * j + self.officer * 2
                    else:
                        cards = self.officer * 2 + CARD_RANK_STR[i[0]] * j
                    playable_cards.add(cards)

        # solo_chain_5
        solo_chain_indexes = self.solo_chain(non_zero_indexes, h_officer)
        for (start_index, length, officer_index) in solo_chain_indexes:
            cards = ''
            s = start_index
            if 0 in officer_index:
                cards += self.officer
            while s < start_index + length:
                if s - start_index != 0 and s - start_index in officer_index:
                    cards += self.officer
                else:
                    cards += CARD_RANK_STR[s]
                s += 1
            playable_cards.add(cards)

        one_indexes = []
        for i in non_zero_indexes:
            if i not in more_than_1_indexes:
                one_indexes.append(i)
        # pair_chain_3

        pair_chain_indexes = self.pair_chain_indexes(more_than_1_indexes, h_officer, one_indexes)
        for (start_index, length, officer_index) in pair_chain_indexes:
            s = start_index
            cards = ''
            if officer_index.count(0) == 2:
                cards += self.officer * 2
            elif officer_index.count(0) == 1:
                cards += CARD_RANK_STR[s]
                cards += self.officer
            else:
                cards += CARD_RANK_STR[s] * 3
            s += 1
            while s < start_index + length:
                if s - start_index in officer_index:
                    if officer_index.count(s - start_index) == 2:
                        cards += self.officer * 2
                    elif officer_index.count(s - start_index) == 1:
                        cards += CARD_RANK_STR[s]
                        cards += self.officer
                    else:
                        cards += CARD_RANK_STR[s] * 2
                s += 1
            playable_cards.add(cards)

        # trio and trio_pair
        for i in more_than_2_indexes:
            # trio
            playable_cards.add(CARD_RANK_STR[i[0]] * 3)
            # trio_pair
            for j in more_than_1_indexes:
                if j < i:
                    playable_cards.add(CARD_RANK_STR[j[0]] * 2 + CARD_RANK_STR[i[0]] * 3)
                elif j > i:
                    playable_cards.add(CARD_RANK_STR[i[0]] * 3 + CARD_RANK_STR[j[0]] * 2)

        if h_officer == 2:
            for i in non_zero_indexes:
                playable_cards.add(CARD_RANK_STR[i[0]] + self.officer * 2)
                for j in more_than_1_indexes:
                    if j < i:
                        playable_cards.add(CARD_RANK_STR[i[0]] + self.officer * 2 + CARD_RANK_STR[i[0]] * 3)
                    elif j > i:
                        playable_cards.add(CARD_RANK_STR[i[0]] + self.officer * 2 + CARD_RANK_STR[j[0]] * 2)

            for i in more_than_1_indexes:
                playable_cards.add(CARD_RANK_STR[i[0]] * 2 + self.officer)
                for j in more_than_1_indexes:
                    if j < i:
                        playable_cards.add(CARD_RANK_STR[i[0]] * 2 + self.officer + CARD_RANK_STR[i[0]] * 3)
                    elif j > i:
                        playable_cards.add(CARD_RANK_STR[i[0]] * 2 + self.officer + CARD_RANK_STR[j[0]] * 2)

        two_indexes = []
        for i in more_than_1_indexes:
            if i not in more_than_2_indexes:
                two_indexes.append(i)
        # trio_chain_2
        trio_chain_indexes = self.trio_chain_indexes(more_than_2_indexes, h_officer, one_indexes, two_indexes)
        for (start_index, length, officer_index) in trio_chain_indexes:
            s = start_index
            cards = ''
            while s < start_index + length:
                officer_num = officer_index.count(s - start_index)
                for i in range(3 - officer_num):
                    cards += CARD_RANK_STR[s]
                for i in range(officer_num):
                    cards += self.officer
                s += 1
            playable_cards.add(cards)

        # rocket  王炸
        if cards_count[13] == 2 and cards_count[14] == 2:
            playable_cards.add(CARD_RANK_STR[13] * 2 + CARD_RANK_STR[14] * 2)
        # print("playable_cards", playable_cards)
        return playable_cards

    # 重新计算当前可以出的牌型
    def calc_playable_cards(self, player):
        """
        Recalculate all legal cards the player can play according to his
        current hand.
        Args:
            player (Player object): object of Player
            init_flag (boolean): For the first time, set it True to accelerate
              the preocess.
        Returns:
            list: list of string of playable cards
        """
        removed_playable_cards = []

        player_id = player.player_id
        # 当前手上的牌
        current_hand = cards2str(player.current_hand)
        h_officer_num = self.count_heart_officer(player.current_hand)
        missed = None
        #
        for single in player.singles:
            if single not in current_hand:
                missed = single
                break

        playable_cards = self.playable_cards[player_id].copy()
        # print(playable_cards)
        # 有没有的牌面值
        if missed is not None:
            position = player.singles.find(missed)
            player.singles = player.singles[position + 1:]
            for cards in playable_cards:
                # 如果当前缺少某张牌或者当前没有对应牌型
                if missed in cards or (
                        not contains_cards(current_hand, cards, self.officer, h_officer_num, player.current_hand)):
                    # 移除可出牌型
                    removed_playable_cards.append(cards)
                    self.playable_cards[player_id].remove(cards)
        # 没有缺失的牌
        else:
            for cards in playable_cards:
                if not contains_cards(current_hand, cards, self.officer, h_officer_num, player.current_hand):
                    # del self.playable_cards[player_id][cards]
                    removed_playable_cards.append(cards)
                    self.playable_cards[player_id].remove(cards)
        # 移除的可出牌型
        self._recorded_removed_playable_cards[player_id].append(removed_playable_cards)
        # print("2", self.playable_cards[player_id])
        return self.playable_cards[player_id]

    # 回退当前可出的牌型
    def restore_playable_cards(self, player_id):
        """
        restore playable_cards for judger for game.step_back().
        Args:
            player_id: The id of the player whose playable_cards need to be restored
        """
        # 移除的可出牌型出栈
        removed_playable_cards = self._recorded_removed_playable_cards[player_id].pop()
        # 合并当前手上的牌和出的牌
        self.playable_cards[player_id].update(removed_playable_cards)

    # 获取当前玩家可出的牌
    def get_playable_cards(self, player):
        """ Provide all legal cards the player can play according to his
        current hand.
        Args:
            player (Player object): object of Player
            init_flag (boolean): For the first time, set it True to accelerate
              the preocess.
        Returns:
            list: list of string of playable cards
        """
        return self.playable_cards[player.player_id]

    # 判断当前玩家是否出完牌
    @staticmethod
    def judge_game(players, player_id):
        """
        Args:
            players (list): list of Player objects
            player_id (int): integer of player's id
        """
        player = players[player_id]
        if len(player.current_hand) == 0:
            return True
        return False

    @staticmethod
    def judge_payoffs(winner_id):
        payoffs = np.array([0, 0, 0, 0])
        # 双上
        if len(winner_id) == 2:
            payoffs[winner_id[0]] = 3
            payoffs[winner_id[1]] = 3
        elif len(winner_id) == 3:
            # 1、3
            if winner_id[0] % 2 == winner_id[2] % 2:
                payoffs[winner_id[0]] = 2
                payoffs[winner_id[2]] = 2
            # 1、4
            else:
                payoffs[winner_id[0]] = 1
                for i in range(4):
                    if i not in winner_id:
                        payoffs[i] = 1
        return payoffs

    # 统计红心参谋的数量
    def count_heart_officer(self, cards_list):
        cnt = 0
        for card in cards_list:
            if card.rank == self.officer and card.suit == 'H':
                cnt += 1
        return cnt


#   重排红心参谋的位置
def arrange_solo(start, count, officer_index):
    chains = []
    cnt = 0
    if count - 1 in officer_index:
        cnt += 1
    if count - 2 in officer_index:
        cnt += 1

    if cnt == 1:
        # 加在头部
        tmp = officer_index.copy()
        if count-1 in tmp:
            tmp.remove(count - 1)
        else:
            tmp.remove(count-2)
        chains.append((start, count, [0] + tmp))
        # 取代某一张牌
        for i in range(count):
            if i not in officer_index:
                tmp = officer_index.copy()
                if count-1 in tmp:
                    tmp.remove(count - 1)
                else:
                    tmp.remove(count-2)
                tmp += [i]
                tmp.sort()
                chains.append((start, count - 1, tmp))

    if cnt == 2:
        # 加在头部
        tmp = officer_index.copy()
        tmp.remove(count - 1)
        tmp.remove(count - 2)
        chains.append((start, count, [0, 1] + tmp))

        # 用一张h_officer取代中间某张牌
        for i in range(count):
            if i not in officer_index:
                tmp = officer_index.copy()
                tmp.remove(count - 1)
                tmp += [i]
                tmp.sort()
                chains.append((start, count - 1, tmp))

        # 用两张h_officer取代中间两张牌
        for i in range(count):
            if i in officer_index:
                continue
            for j in range(i + 1, count):
                if j in officer_index:
                    continue

                tmp = officer_index.copy()
                tmp.remove(count - 1)
                tmp.remove(count - 2)
                tmp += [i, j]
                tmp.sort()
                chains.append((start, count - 1, tmp))
    return chains


#   重排红心参谋的位置
def arrange_pair(start, count, officer_index):
    chains = []
    cnt = 0
    if officer_index.count(count - 1) == 2:
        cnt += 1

    if cnt == 1:
        # 放在开头
        tmp = officer_index.copy()
        tmp.remove(count - 1)
        chains.append((start,count,[0] + tmp))

        # 取代某对牌
        for i in range(count):
            if i not in officer_index:
                tmp = officer_index.copy()
                tmp.remove(count - 1)
                tmp += [i]
                tmp.sort()
                chains.append((start, count - 1, tmp))
    return chains
