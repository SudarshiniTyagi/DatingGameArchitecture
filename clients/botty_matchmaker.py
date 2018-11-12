import json
import numpy as np
from sklearn import linear_model, ensemble
# import xgboost as xgb
import random

from clients.client import Player


class MatchMaker(Player):
    def __init__(self):
        super().__init__(name="BottyMcBotFaceMatchmaker", is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        print('Matchmaker', game_info)
        self.random_candidates_and_scores = game_info['randomCandidateAndScores']
        self.n = game_info['n']
        self.prev_candidate = {'candidate': [], 'score': 0, 'iter': 0}
        self.time_left = 120

        self.my_prev_candidates = []
        self.my_prev_scores = []

    def play_game(self):
        while True:
            print(self.name)
            candidate = self.my_candidate()
            self.client.send_data(json.dumps(candidate))
            response = json.loads(self.client.receive_data(size=32368*2))
            if 'game_over' in response:
                if response['match_found']:
                    print("Perfect Candidate Found")
                    print("Total candidates used = ", response['num_iterations'])
                else:
                    print("Perfect candidate not found - you have failed the player")
                    print("Total candidates used = ", response['total_candidates'])
                exit(0)
            else:
                self.prev_candidate = response['prev_candidate']
                self.time_left = response['time_left']


    def my_candidate(self):
        # turn from 0 to 19
        turn = self.prev_candidate['iter']
        w = []
        # print("turn", turn)
        if turn > 0:
            self.my_prev_candidates.append(self.prev_candidate['candidate'])
            self.my_prev_scores.append(self.prev_candidate['score'])
            # print(self.prev_candidate['candidate'])
            # print(self.prev_candidate['score'])
        if turn == 19: # send coefficients of ridge regression
            clf = linear_model.Ridge(alpha=.0001, normalize=True)
            # clf = linear_model.LinearRegression(alpha=.0001, normalize=True)
            candidates = []
            scores = []
            for i in range(len(self.random_candidates_and_scores)):
                candidates.append(self.random_candidates_and_scores[str(i)]['Attributes'])
                scores.append(self.random_candidates_and_scores[str(i)]['Score'])
            for i in range(len(self.my_prev_candidates)):
                candidates.append(self.my_prev_candidates[i])
                scores.append(self.my_prev_scores[i])
            #for i in range(len(candidates)):
                # print(i, len(candidates[i]))
            # print(len(candidates))
            # print(len(scores))
            candidates = np.array(candidates)
            scores = np.array(scores)
            clf.fit(candidates, scores)
            for co in clf.coef_:
                if co > 0:
                    w.append(1)
                else:
                    w.append(0)
        elif turn == 18:
            interval_size = self.n // 19
            prev_interval_sum = 0
            for i in range(turn):
                prev_interval_sum += self.my_prev_scores[i]
                if self.my_prev_scores[i] > 0:
                    w.extend([1] * interval_size)
                else:
                    w.extend([0] * interval_size)
            last_interval_score = -prev_interval_sum
            if last_interval_score > 0:
                for i in range(turn * interval_size, self.n):
                    w.append(1)
            else:
                for i in range(turn * interval_size, self.n):
                    w.append(0)
        else:
            interval_size = self.n // 19
            # print("interval_size", interval_size)
            # print((turn * interval_size), ((turn + 1) * interval_size))
            for i in range(self.n):
                if (i >= (turn * interval_size)) and (i < ((turn + 1) * interval_size)):
                    w.append(1)
                else:
                    w.append(0)
        print("w", len(w))
        print(w)
        return w

        """
        PLACE YOUR CANDIDATE GENERATION ALGORITHM HERE
        As the matchmaker, you have access to the number of attributes (self.n),
        initial random candidates and their scores (self.random_candidates_and_scores),
        your clock time left (self.time_left)
        and a dictionary of the previous candidate sent (self.prev_candidate) consisting of
            'candidate' = previous candidate attributes
            'score' = previous candidate score
            'iter' = iteration num of previous candidate
        For this function, you must return an array of values that lie between 0 and 1 inclusive and must have four or
        fewer digits of precision. The length of the array should be equal to the number of attributes (self.n)
        """



        # return [round(random(), 4) for i in range(self.n)]
