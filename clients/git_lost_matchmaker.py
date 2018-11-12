import json
import numpy as np
from sklearn.linear_model import LinearRegression  # Ridge, RidgeCV
from clients.client import Player

import warnings
warnings.filterwarnings(action="ignore", module="scipy", message="^internal gelsd")


class MatchMaker(Player):

    def __init__(self):
        super(MatchMaker, self).__init__("Git lost matchmaker", is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        # print('Matchmaker', game_info)  # commented out
        self.random_candidates_and_scores = game_info['randomCandidateAndScores']
        self.n = game_info['n']
        self.prev_candidate = {'candidate': [], 'score': 0, 'iter': 0}
        self.time_left = 120

        # My instance variables
        self.first_turn = True
        self.X = np.zeros((40, self.n))
        self.y = np.zeros(40)
        self.sample_weights = []
        self.certain = [None] * self.n  # None => uncertain, 0 => it's zero or negative, 1 => it's positive
        self.wasted_guesses = set()

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
        """
        PLACE YOUR CANDIDATE GENERATION ALGORITHM HERE
        As the matchmaker, you have access to:
            - self.n = the number of attributes
            - self.random_candidates_and_scores = initial random candidates and their scores
            - self.time_left = your clock time left
            - self.prev_candidate = dictionary of the previous candidate sent, including 'candidate' (previous candidate
            attributes), 'score' (previous candidate score), and 'iter' (iteration number of previous candidate)
        For this function, you must return an array of values that lie between 0 and 1 inclusive and must have four or
        fewer digits of precision. The length of the array should be equal to the number of attributes (self.n)
        """

        # Build dataset on first turn
        if self.first_turn:
            for i, d in enumerate(self.random_candidates_and_scores.values()):
                self.X[i] = np.array(d['Attributes'])  # (40, self.n)
                self.y[i] = d['Score']  # (40,)
            self.sample_weights = [1] * 40
            self.first_turn = False

        # Subsequent turns
        if len(self.prev_candidate['candidate']) > 0:

            # Add previous candidate to the dataset
            self.X = np.vstack((self.X, self.prev_candidate['candidate']))
            self.y = np.append(self.y, self.prev_candidate['score'])
            self.sample_weights += [self.sample_weights[-1] * 10]  # sample weights exopnential

            # If it was a wasted guess, we are certain of the information we got back
            idx_of_nonzeros = [i for i, n in enumerate(self.prev_candidate['candidate']) if n != 0]
            if len(idx_of_nonzeros) == 1:
                idx = idx_of_nonzeros[0]
                if self.prev_candidate['score'] > 0:
                    self.certain[idx] = 1
                else:
                    self.certain[idx] = 0

        # Make and train weighted linear regression model
        # This will give us reg.score(self.X, self.y), reg.coef_, reg.intercept_, reg.predict(np.array([[3, 5]]))
        reg = LinearRegression().fit(self.X, self.y, self.sample_weights)

        # # Make and train weighted ridge regression model that does its own cross-validation
        # # This will give us reg.coef_, reg.intercept_, reg.alpha_, and reg.cv_values_
        # alphas = [0.0, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0]
        # reg = RidgeCV(alphas=alphas).fit(self.X, self.y, self.sample_weights)

        # First several guesses are wasted with candidates that zero in on one quality, i.e. [0, ..., 0, 1, 0, ... 0]
        if len(self.prev_candidate['candidate']) > 0 and 1 <= self.prev_candidate['iter'] <= 15:

            # Find index of coeff closest to 0
            dist = min(abs(0.005 - reg.coef_[0]), abs(-0.005 - reg.coef_[0]))
            idx_of_closest = 0
            for i, coef in enumerate(reg.coef_):
                if min(abs(0.005 - coef), abs(-0.005 - coef)) < dist:
                    dist = min(abs(0.005 - coef), abs(-0.005 - coef))
                    idx_of_closest = i

            # Guess weights are all zeros except at idx_of_closest (as long as we haven't guessed this before)
            if idx_of_closest not in self.wasted_guesses:
                self.wasted_guesses.add(idx_of_closest)
                result = [0] * len(reg.coef_)
                result[idx_of_closest] = 1
                return result

        # Make candidate based on our model's coefficients
        result = []
        for coef in reg.coef_:
            if coef <= 0:
                result += [0]
            else:
                result += [1]

        # Enforce the attributes we're certain of
        for i, val in enumerate(self.certain):
            if val is not None:
                result[i] = val

        # Return result
        return result

# Possibilities:
# - Change number of wasted guesses from 15 to...something else?
# - Make our guesses more nuanced; maybe not just 0s or 1s
#   We're allowed 4 digits of precision.  Remember "without this constraint, there is a way to discover the sign
#   of the weight that P ascribes to each attribute" so maybe there's still some way to take advantage
# - Try several candidates within this function using reg.predict() before we return result
