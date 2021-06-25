import os
import json
from collections import OrderedDict
import threading
import collections

import CFR

# Read required docs
ROOT_PATH = CFR.__path__[0]

# a map of action to abstract action
with open(os.path.join(ROOT_PATH, 'jsondata/specific_map.json'), 'r') as file:
    SPECIFIC_MAP = json.load(file, object_pairs_hook=OrderedDict)

# a map of abstract action to its index and a list of abstract action
with open(os.path.join(ROOT_PATH, 'jsondata/action_space.json'), 'r') as file:
    ACTION_SPACE = json.load(file, object_pairs_hook=OrderedDict)
    ACTION_LIST = list(ACTION_SPACE.keys())

# a map of card to its type. Also return both dict and list to accelerate
with open(os.path.join(ROOT_PATH, 'jsondata/card_type.json'), 'r') as file:
    data = json.load(file, object_pairs_hook=OrderedDict)
    CARD_TYPE = (data, list(data), set(data))

# a map of type to its cards
with open(os.path.join(ROOT_PATH, 'jsondata/type_card.json'), 'r') as file:
    TYPE_CARD = json.load(file, object_pairs_hook=OrderedDict)

# rank list of solo character of cards
CARD_RANK_STR = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K',
                 'A', 'B', 'R']
CARD_RANK_STR_INDEX = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5,
                       '8': 6, '9': 7, 'T': 8, 'J': 9, 'Q': 10,
                       'K': 11, 'A': 12, 'B': 13, 'R': 14}
# rank list
CARD_RANK = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K',
             'A', 'BJ', 'RJ']

INDEX = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5,
         '8': 6, '9': 7, 'T': 8, 'J': 9, 'Q': 10,
         'K': 11, 'A': 12, 'B': 13, 'R': 14}
INDEX = OrderedDict(sorted(INDEX.items(), key=lambda t: t[1]))


def doudizhu_sort_str(card_1, card_2, cur_):
    """ Compare the rank of two cards of str representation

    Args:
        card_1 (str): str representation of solo card
        card_2 (str): str representation of solo card

    Returns:
        int: 1(card_1 > card_2) / 0(card_1 = card2) / -1(card_1 < card_2)
    """
    key_1 = CARD_RANK_STR.index(card_1)
    key_2 = CARD_RANK_STR.index(card_2)
    if key_1 > key_2:
        return 1
    if key_1 < key_2:
        return -1
    return 0


def get_landlord_score(current_hand):
    ''' Roughly judge the quality of the hand, and provide a score as basis to
    bid landlord.

    Args:
        current_hand (str): string of cards. Eg: '56888TTQKKKAA222R'

    Returns:
        int: score
    '''
    score_map = {'A': 1, '2': 2, 'B': 3, 'R': 4}
    score = 0
    # rocket
    if current_hand[-2:] == 'BR':
        score += 8
        current_hand = current_hand[:-2]
    length = len(current_hand)
    i = 0
    while i < length:
        # bomb
        if i <= (length - 4) and current_hand[i] == current_hand[i + 3]:
            score += 6
            i += 4
            continue
        # 2, Black Joker, Red Joker
        if current_hand[i] in score_map:
            score += score_map[current_hand[i]]
        i += 1
    return score


def get_optimal_action(probs, legal_actions, np_random):
    ''' Determine the optimal action from legal actions
    according to the probabilities of abstract actions.

    Args:
        probs (list): list of probabilities of abstract actions
        legal_actions (list): list of legal actions

    Returns:
        str: optimal legal action
    '''
    abstract_actions = [SPECIFIC_MAP[action] for action in legal_actions]
    action_probs = []
    for actions in abstract_actions:
        max_prob = -1
        for action in actions:
            prob = probs[ACTION_SPACE[action]]
            if prob > max_prob:
                max_prob = prob
        action_probs.append(max_prob)
    optimal_prob = max(action_probs)
    optimal_actions = [legal_actions[index] for index,
                                                prob in enumerate(action_probs) if prob == optimal_prob]
    if len(optimal_actions) > 1:
        return np_random.choice(optimal_actions)
    return optimal_actions[0]


def cards2str_with_suit(cards):
    ''' Get the corresponding string representation of cards with suit

    Args:
        cards (list): list of Card objects

    Returns:
        string: string representation of cards
    '''
    return ' '.join([card.suit + card.rank for card in cards])


def cards2str(cards):
    """
    Get the corresponding string representation of cards

    Args:
        cards (list): list of Card objects

    Returns:
        string: string representation of cards
    """
    response = ''
    for card in cards:
        if card.rank == '':
            response += card.suit[0]
        else:
            response += card.rank
    return response


class LocalObjs(threading.local):
    def __init__(self):
        self.cached_candidate_cards = None


_local_objs = LocalObjs()


def contains_cards(candidate, target, officer, h_officer_num, cards_list):
    """
    Check if cards of candidate contains cards of target.

    Args:
        candidate (string): A string representing the cards of candidate
        target (string): A string representing the number of cards of target

    Returns:
        boolean
    """
    # In normal cases, most continuous calls of this function
    #   will test different targets against the same candidate.
    # So the cached counts of each card in candidate can speed up
    #   the comparison for following tests if candidate keeps the same.
    if not _local_objs.cached_candidate_cards or _local_objs.cached_candidate_cards != candidate:
        _local_objs.cached_candidate_cards = candidate
        cards_dict = collections.defaultdict(int)
        # 当前所有牌
        for card in candidate:
            cards_dict[card] += 1
        _local_objs.cached_candidate_cards_dict = cards_dict
    cards_dict = _local_objs.cached_candidate_cards_dict
    # 如果目标牌型为空
    if target == '':
        return True

    curr_card = target[0]
    # 第一张牌
    # for i in range(len(target)):
    #     if target[i] != officer:
    #         curr_card = target[i]
    #         break
    curr_count = 0
    for card in target:
        # if card == officer:
        #     h_officer_num -= 1
        #     if h_officer_num < 0:
        #         return False
        #     continue
        if card != curr_card:
            if cards_dict[curr_card] < curr_count:
                return False
            curr_card = card
            curr_count = 1
        else:
            curr_count += 1
    if cards_dict[curr_card] < curr_count:
        return False
    return True


# 对牌进行编码
def encode_cards(plane, cards):
    """
    Encode cards and represerve it into plane.

    Args:
        cards (list or str): list or str of cards, every entry is a
    character of solo representation of card
    """
    # 如果没有牌
    # print(cards)
    if not cards:
        return None
    layer = 1
    # 如果只有一张牌
    if len(cards) == 1:
        rank = CARD_RANK_STR.index(cards[0])
        # 当前牌有一张
        plane[layer][rank] = 1
        plane[0][rank] = 0
    # 大于一张牌
    else:
        for index, card in enumerate(cards):
            if index == 0:
                continue
            #
            # if card == cards[index - 1]:
            #     layer += 1
            # else:
            rank = CARD_RANK_STR.index(cards[index - 1])
            if plane[layer][rank] == 0:
                plane[layer][rank] = 1
                layer = 1
                plane[0][rank] = 0
        rank = CARD_RANK_STR.index(cards[-1])
        if plane[layer][rank] == 0:
            plane[layer][rank] = 1
            plane[0][rank] = 0


# 获得比之前玩家出的牌更大的牌
def get_gt_cards(player, greater_player, officer, h_officer_num):
    """
    Provide player's cards which are greater than the ones played by
    previous player in one round

    Args:
        player (Player object): the player waiting to play cards
        greater_player (Player object): the player who played current biggest cards.

    Returns:
        list: list of string of greater cards

    Note:
        1. return value contains 'pass'
    """
    # add 'pass' to legal actions
    gt_cards = []
    if len(greater_player.current_hand) > 0:
        gt_cards = ['pass']
    current_hand = cards2str(player.current_hand)
    target_cards = greater_player.played_cards

    target_types = CARD_TYPE[0][target_cards]
    type_dict = {}
    for card_type, weight in target_types:
        if card_type not in type_dict:
            type_dict[card_type] = weight

    # 如果上个玩家出四大天王，没有牌比它大
    if 'rocket' in type_dict:
        return gt_cards

    # 炸弹
    type_dict['rocket'] = -1

    for i in range(11, 4):
        if i == 5:
            if "straight_flush" not in type_dict:
                type_dict["straight_flush"] = -1
            else:
                break
        if "bomb_" + str(i) not in type_dict:
            type_dict["bomb_" + str(i)] = -1
        else:
            break

    for card_type, weight in type_dict.items():
        candidate = TYPE_CARD[card_type]
        for can_weight, cards_list in candidate.items():
            if int(can_weight) > int(weight):
                for cards in cards_list:
                    if cards not in gt_cards and contains_cards(current_hand, cards, officer, h_officer_num,
                                                                player.current_hand):
                        # if self.contains_cards(current_hand, cards):
                        gt_cards.append(cards)
    return gt_cards


# 按照牌的大小排序
def sort_card(card_1, card_2):
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

# Test json order
# if __name__ == '__main__':
#    for action, index in ACTION_SPACE.items():
#        if action != ACTION_LIST[index]:
#            print('order error')
