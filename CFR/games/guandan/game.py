import functools
from heapq import merge
import numpy as np

from CFR.games.guandan.utils import cards2str, CARD_RANK_STR
from CFR.games.guandan import Player
from CFR.games.guandan import Round
from CFR.games.guandan import Judger


class GuandanGame:
    """
    Provide game APIs for env to run guandan and get corresponding state
    information.
    """

    def __init__(self, allow_step_back=False):
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        self.num_players = 4
        self.winner_id = []

    def configure(self, game_config):
        self.num_players = game_config['game_num_players']

    # 初始化游戏
    def init_game(self):
        """
        Initialize players and state.
        Returns:
            dict: first state in one game
            int: current player's id
        """
        # initialize public variables
        self.winner_group = None
        self.history = []
        # 当前两组玩家的参谋
        self.group_officer = ['2', '2']

        # initialize players
        self.players = [Player(num, self.np_random)
                        for num in range(self.num_players)]

        # 出过的牌
        # CARD_RANK_STR为所有牌面值
        self.played_cards = [np.zeros((len(CARD_RANK_STR),), dtype=np.int)
                             for _ in range(self.num_players)]
        # 初始化第一局
        self.round = Round(self.np_random, self.played_cards, '2')
        self.round.initiate(self.players, self.winner_group, self.winner_id)

        # 初始化裁判
        self.judger = Judger(self.players, self.np_random, '2')

        # get state of first player
        player_id = self.round.current_player
        # print(player_id)
        self.state = self.get_state(player_id)

        return self.state, player_id

    def step(self, action):
        """
        Perform one draw of the game
        Args:
            action (str): specific action of doudizhu. Eg: '33344'
        Returns:
            dict: next player's state
            int: next player's id
        """

        # perfrom action
        player = self.players[self.round.current_player]
        self.round.proceed_round(player, action)
        print(player.player_id,action)
        print(cards2str(player.current_hand))


        # 如果出牌
        if action != 'pass':
            # 当前可以出的牌
            self.judger.calc_playable_cards(player)
        #
        if self.judger.judge_game(self.players, self.round.current_player):
            self.winner_id.append(self.round.current_player)
        # 轮到下一位玩家出牌
        next_id = (player.player_id + 1) % len(self.players)
        while len(self.players[next_id].current_hand) == 0:
            if next_id not in self.winner_id:
                self.winner_id.append(next_id)
            next_id = (next_id + 1) % len(self.players)
        self.round.current_player = next_id

        # 获得下一位玩家的状态
        state = self.get_state(next_id)
        self.state = state

        return state, next_id

    # 回退到上一步
    def step_back(self):
        """
        Return to the previous state of the game
        Returns:
            (bool): True if the game steps back successfully
        """
        # 如果当前记录为空，无法回退
        if not self.round.trace:
            return False

        # 回退
        player_id, cards = self.round.step_back(self.players)
        if player_id in self.winner_id:
            self.winner_id.remove(player_id)

        # 找到当前玩家上一轮出的牌
        if cards != 'pass':
            self.players[player_id].played_cards = self.round.find_last_played_cards_in_trace(player_id)
        self.players[player_id].play_back()

        # 更新当前可以出的牌
        if cards != 'pass':
            self.judger.restore_playable_cards(player_id)

        # 获取当前玩家的状态
        self.state = self.get_state(self.round.current_player)
        return True

    # 获取当前玩家的状态
    def get_state(self, player_id):
        """
        Return player's state
        Args:
            player_id (int): player id
        Returns:
            (dict): The state of the player
        """
        player = self.players[player_id]
        # 其他玩家当前手上的牌
        others_hands = self._get_others_current_hand(player)
        # 当前所有玩家手上的牌的数量
        num_cards_left = [len(self.players[i].current_hand) for i in range(self.num_players)]

        # 如果当前小局结束
        if self.is_over():
            # 清空当前动作
            actions = []
        # 如果当前小局没有结束
        else:
            actions = list(
                player.available_actions(self.round.officer, self.judger.count_heart_officer(player.current_hand),
                                         self.round.greater_player, self.judger))

        # 获得当前状态
        state = player.get_state(self.round.public, others_hands, num_cards_left, actions)
        return state

    # 获得所有动作的数量
    @staticmethod
    def get_num_actions():
        """ Return the total number of abstract acitons
        Returns:
            int: the total number of abstract actions of guandan
        """
        return 322

    # 获得当前玩家的id
    def get_player_id(self):
        """
        Return current player's id
        Returns:
            int: current player's id
        """
        return self.round.current_player

    # 返回当前玩家的数量
    def get_num_players(self):
        """ Return the number of players in guandan
        Returns:
            int: the number of players in guandan
        """
        return self.num_players

    # 判断当前轮是否结束
    def is_over(self):
        """ Judge whether a game is over
        Returns:
            Bool: True(over) / False(not over)
        """
        # 只有一位玩家出完牌
        if len(self.winner_id) < 2:
            return False
        elif len(self.winner_id) == 2:
            player1 = self.winner_id[0]
            player2 = self.winner_id[1]
            # 双上
            if (player1 % 2) == (player2 % 2):
                return True
            # 不是双上，要等第三位玩家出完牌
            else:
                return False
        # 前三位玩家都已经出完牌，当前小局结束
        elif len(self.winner_id) >= 3:
            return True
        return False

    # 获取其他玩家当前手上的牌
    def _get_others_current_hand(self, player):
        other_players = []
        for p in self.players:
            if p.player_id != player.player_id:
                other_players.append(p)

        others_hand = []
        for p in other_players:
            others_hand = merge(others_hand, p.current_hand, key=functools.cmp_to_key(self.round.sort_card))
        return cards2str(others_hand)
