""" The Raging Disspointments Matchmaker Client """

import json
from random import choice, random
import numpy as np
from .prov_client import BasePlayer


class MatchMaker(BasePlayer):
    """ Matchmaker class... """
    def __init__(self):
        super(MatchMaker, self).__init__(name='The Raging Dissapointments', is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        self.init_cands = game_info['randomCandidateAndScores']
        self.num_attrib = game_info['n']
        self.prev_candidates = []
        self.time_left = 120
        self.init_guess = None

    def play_game(self):
        while True:
            candidate = self.my_candidate()
            self.client.send_data(json.dumps(candidate))
            response = json.loads(self.client.receive_data())
            if 'game_over' in response:
                if response['match_found']:
                    print("Perfect Candidate Found")
                    print("Total candidates used = ", response['num_iterations'])
                else:
                    print("Perfect candidate not found - you have failed :(")
                    print("Total candidates used = ", response['total_candidates'])
                exit(0)
            else:
                self.prev_candidates.append(response['prev_candidate'])
                self.time_left = response['time_left']


    def my_candidate(self):
        """
        This method is called for each matchmaker's turn and determines
        the proper strategy to implement based on the turn.
        return:[float] A float array of attribute guesses from [-1, 1]
        """
        data_list = []
        labels_list = []

        for info in self.init_cands.values():
            data_list.append(info['Attributes'])
            labels_list.append(info['Score'])

        for candidate in self.prev_candidates:
            if not candidate['candidate']:
                continue

            data_list.append(candidate['candidate'])
            labels_list.append(candidate['score'])

        best_score = float('inf')
        best_candidate = None

        for idx, candidate in enumerate(data_list):
            if labels_list[idx] == 0:
                continue

            pot_candidate = np.asarray(candidate) / labels_list[idx]

            pot_candidate *= 1000
            pot_candidate %= 10
            pot_score = pot_candidate.sum()

            if pot_score < best_score:
                best_score = pot_score
                best_candidate = np.asarray(candidate) / labels_list[idx]

        return [round(x, 2) for x in best_candidate]


class Player(BasePlayer):
    """
    The Player for The Raging Dissapointments team in The Dating Game.
    """
    def __init__(self):
        super(Player, self).__init__(name='The Raging Dissapointments', is_player=True)
        game_info = json.loads(self.client.receive_data())
        print('Player', game_info)
        self.num_attrib = game_info['n']
        self.weight_history = []
        self.time_left = 120
        self.candidate_history = []
        self.current_weights = []
        self.set_og_weights()
        self.ranges = []

    def play_game(self):
        response = {}
        while True:
            new_weights = self.your_algorithm(0 if not response else self.candidate_history)
            self.client.send_data(json.dumps(new_weights))
            self.current_weights = new_weights
            response = json.loads(self.client.receive_data(size=32368*2))
            if 'game_over' in response:
                print("######## GAME OVER ########")
                if response['match_found']:
                    print("Perfect Candidate Found :D")
                    print("Total candidates used = ", response['num_iterations'])
                else:
                    print("Sorry player :( Perfect candidate not found for you, gotta live with ",
                          response['final_score']*100, "% match... Sighhh")
                    print("Final Score of the best match = ", response['final_score'])
                exit(0)
            else:
                self.time_left = response['time_left']
                self.candidate_history.append(response['new_candidate'])
                self.weight_history = response['weight_history']

    def set_og_weights(self):
        """
        This method sets the initial weight vector for the player.
        """
        pos_left = 1.0
        neg_left = -1.0

        num = self.num_attrib
        while num:
            if pos_left == 0 and neg_left == 0:
                self.current_weights.append(0)
            elif pos_left == 0:
                rand = round(random() * (neg_left / num), 2)
                self.current_weights.append(neg_left if num == 1 else rand)
                neg_left = round(neg_left - rand, 2)
            elif neg_left == 0:
                rand = round(random() * (pos_left / num), 2)
                self.current_weights.append(pos_left if num == 1 else rand)
                pos_left = round(pos_left - rand, 2)
            elif num == 2 and choice([-1, 1]) == -1:
                self.current_weights.append(neg_left)
                neg_left = 0
            elif num == 2:
                self.current_weights.append(pos_left)
                pos_left = 0
            elif choice([-1, 1]) == -1:
                rand = round(random() * (neg_left / num), 2)
                self.current_weights.append(rand)
                neg_left = round(neg_left - rand, 2)
            else:
                rand = round(random() * (pos_left / num), 2)
                self.current_weights.append(rand)
                pos_left = round(pos_left - rand, 2)
            num -= 1


    def your_algorithm(self, _):
        """
        This method plays the player portion of the game.
        candidate_history::[] List of previously sent candidates
        return::[float] The new player array
        """
        return self.current_weights
