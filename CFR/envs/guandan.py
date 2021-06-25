import numpy as np

from CFR.envs import Env

DEFAULT_GAME_CONFIG = {
    'game_num_players': 4
}


class GuandanEnv(Env):
    '''  Environment
    '''

    def __init__(self, config):
        from CFR import SPECIFIC_MAP, CARD_RANK_STR
        from CFR import ACTION_LIST, ACTION_SPACE
        from CFR import encode_cards
        from CFR import cards2str, cards2str_with_suit
        from CFR.games.guandan import Game
        self._encode_cards = encode_cards
        self._cards2str = cards2str
        self._cards2str_with_suit = cards2str_with_suit
        self._SPECIFIC_MAP = SPECIFIC_MAP
        self._CARD_RANK_STR = CARD_RANK_STR
        self._ACTION_LIST = ACTION_LIST
        self._ACTION_SPACE = ACTION_SPACE

        self.name = 'guandan'
        self.default_game_config = DEFAULT_GAME_CONFIG

        self.game = Game()
        super().__init__(config)
        # self.state_shape = [7, 5, 15]
        # 减小状态假设空间，加快收敛速度
        self.state_shape = [2, 9, 15]

    def _extract_state(self, state):
        ''' Encode state

        Args:
            state (dict): dict of original state

        Returns:
            numpy array: 6*5*15 array
                         6 : current hand
                             the union of the other two players' hand
                             the recent three actions
                             the union of all played cards
        '''
        # obs = np.zeros((7, 9, 15), dtype=int)
        obs = np.zeros((2, 2, 15), dtype=int)
        for index in range(2):
            obs[index][0] = np.ones(15, dtype=int)
        self._encode_cards(obs[0], state['current_hand'])
        self._encode_cards(obs[1], state['others_hand'])
        # for i, action in enumerate(state['trace'][-4:]):
        #     if action[1] != 'pass':
        #         self._encode_cards(obs[5 - i], action[1])
        # print(state['played_cards'])
        # print(state['played_cards'])
        # if state['played_cards'] != None:
        #     self._encode_cards(obs[6], state['played_cards'])

        extracted_state = {'obs': obs, 'legal_actions': self._get_legal_actions()}
        extracted_state['raw_obs'] = state
        # TODO: state['actions'] can be None, may have bugs
        if state['legal_actions'] == None:
            extracted_state['raw_legal_actions'] = []
        else:
            extracted_state['raw_legal_actions'] = [a for a in state['legal_actions']]

        extracted_state['action_record'] = self.action_recorder
        return extracted_state

    # 获得收益
    def get_payoffs(self):
        ''' Get the payoffs of players. Must be implemented in the child class.

        Returns:
            payoffs (list): a list of payoffs for each player
        '''
        return self.game.judger.judge_payoffs(self.game.winner_id)

    def _decode_action(self, action_id):
        ''' Action id -> the action in the game. Must be implemented in the child class.

        Args:
            action_id (int): the id of the action

        Returns:
            action (string): the action that will be passed to the game engine.
        '''
        abstract_action = self._ACTION_LIST[action_id]
        # without kicker
        if '*' not in abstract_action:
            return abstract_action
        # with kicker
        legal_actions = self.game.state['legal_actions']
        specific_actions = []
        kickers = []
        for legal_action in legal_actions:
            if legal_action not in self._SPECIFIC_MAP:
                continue
            for abstract in self._SPECIFIC_MAP[legal_action]:
                main = abstract.strip('*')
                if abstract == abstract_action:
                    specific_actions.append(legal_action)
                    kickers.append(legal_action.replace(main, '', 1))
                    break
        # choose kicker with minimum score
        player_id = self.game.get_player_id()
        kicker_scores = []
        for kicker in kickers:
            score = 0
            for action in self.game.judger.playable_cards[player_id]:
                if kicker in action:
                    score += 1
            kicker_scores.append(score + self._CARD_RANK_STR.index(kicker[0]))
        min_index = 0
        min_score = kicker_scores[0]
        for index, score in enumerate(kicker_scores):
            if score < min_score:
                min_score = score
                min_index = index
        return specific_actions[min_index]

    def _get_legal_actions(self):
        ''' Get all legal actions for current state

        Returns:
            legal_actions (list): a list of legal actions' id
        '''
        legal_action_id = []
        legal_actions = self.game.state['legal_actions']
        if legal_actions:
            for action in legal_actions:
                if action not in self._SPECIFIC_MAP:
                    continue
                for abstract in self._SPECIFIC_MAP[action]:
                    action_id = self._ACTION_SPACE[abstract]
                    if action_id not in legal_action_id:
                        legal_action_id.append(action_id)
        return legal_action_id

    def get_perfect_information(self):
        ''' Get the perfect information of the current state

        Returns:
            (dict): A dictionary of all the perfect information of the current state
        '''
        state = {}
        state['hand_cards_with_suit'] = [self._cards2str_with_suit(player.current_hand) for player in self.game.players]
        state['hand_cards'] = [self._cards2str(player.current_hand) for player in self.game.players]
        state['landlord'] = self.game.state['landlord']
        state['trace'] = self.game.state['trace']
        state['current_player'] = self.game.round.current_player
        state['legal_actions'] = self.game.state['actions']
        return state
