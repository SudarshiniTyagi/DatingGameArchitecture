import json
from decimal import *
from random import randint
from time import time
import pickle

from hps.servers import SocketServer

HOST = '127.0.0.1'
PORT = 5000


class GameServer(object):
    def __init__(self, n):
        self.n = int(n)
        # self.randomFile = randomFile
        self.iterations = 20
        self.weights = None
        self.candidate_history = []
        self.score_history = []
        self.weight_history = []
        self.perfect_candidate_found = False
        self.maxScore = 0
        self.previousCandidate = []

        self.player_time_left = self.matchmaker_time_left = 120
        self.web_server = None
        print('Waiting on port %s for players...' % PORT)
        self.accept_player_connections()

    def accept_player_connections(self):
        self.server = SocketServer(HOST, PORT, 2)
        self.server.establish_client_connections()
        self.player_attributes = [json.loads(info) for info in self.server.receive_from_all()]
        self.player_idx = 0 if self.player_attributes[0]['is_player'] else 1
        self.matchmaker_idx = 1 if self.player_attributes[0]['is_player'] else 0
        self.play_game()

    def timed_request(self, request_data, client_idx):
        self.server.send_to(json.dumps(request_data), client_idx)
        start = time()
        vector = json.loads(self.server.receive_from(client_idx))
        stop = time()
        return vector, (stop - start)

    def decrement_time(self, player_time_spent, matchmaker_time_spent):
        self.player_time_left -= player_time_spent
        self.matchmaker_time_left -= matchmaker_time_spent

    def check_time_left(self):
        if self.player_time_left < 0:
            raise Exception('Player ran out of time')

        if self.matchmaker_time_left < 0:
            raise Exception('Matchmaker ran out of time')

    def compute_score(self, weights, candidate):
        score = 0
        for i in range(len(candidate)):
            score += weights[i] * candidate[i]
        return round(score, 4)

    def check_precision(self, candidate):
        getcontext().prec = 4

        for i in range(0, len(candidate)):
            w = candidate[i]
            a = Decimal(w) / Decimal(1)
            if ((float)(a) != w):
                return False
        return True

    def check_weights_validity(self, orig_weights, cur_weights, prev_weights):

        # check weights have atmost precision 2
        getcontext().prec = 2

        for i in range(0, len(cur_weights)):
            w = cur_weights[i]
            a = Decimal(w) / Decimal(1)
            if (float)(a) != w:
                return False

        # check whether change of every weight is in 20% range
        for i in range(0, self.n):
            if abs(cur_weights[i] - orig_weights[i]) > 0.2 * abs(orig_weights[i]):
                return False

        # check atmost 5% of weights changed from previous turn
        modified_weights = 0
        for i in range(self.n):
            if cur_weights[i] != prev_weights[i]:
                modified_weights += 1

        if (modified_weights > 0.05 * self.n):
            return False

        # check pos weights sum to 1, neg weights sum to -1
        pos_sum = Decimal(0)
        neg_sum = Decimal(0)

        for w in cur_weights:
            if w > 0:
                pos_sum += Decimal(w)
            else:
                neg_sum += Decimal(w)

        if pos_sum != 1:
            return False
        if neg_sum != -1:
            return False

        return True

    def load_obj(self, name):
        with open(name, 'rb') as f:
            return pickle.load(f)

    def play_game(self):

        self.weights, player_time_spent = self.timed_request(
            {'n': self.n},
            self.player_idx
        )

        if not self.check_weights_validity(self.weights, self.weights, self.weights):
            raise ValueError('Invalid Weights provided by Player')

        # Generate 40 random candidates and scores

        random_candidates = {}

        for i in range(0, 40):
            # rand_cand = self.load_obj(self.randomFile)
            rand_cand = []
            for j in range(0, self.n):
                r = randint(0, 1)
                rand_cand.append(r)
            cscore = self.compute_score(rand_cand, self.weights)
            random_candidates[i] = {'Score': cscore, 'Attributes': rand_cand}

        self.server.send_to(json.dumps({'n': self.n, 'randomCandidateAndScores': random_candidates}),
                            self.matchmaker_idx)

        iterations = 0
        new_weights = self.weights
        self.weight_history.append(new_weights)
        new_candidate = []
        score = 0

        while iterations < self.iterations and self.perfect_candidate_found == False:
            self.check_time_left()

            new_candidate, matchmaker_time_spent = self.timed_request(
                {'prev_candidate': {'candidate': new_candidate, 'score': score, 'iter': iterations},
                 'time_left': self.matchmaker_time_left},
                self.matchmaker_idx
            )

            if (not self.check_precision(new_candidate)):
                raise ValueError("Invalid precision of candidates")

            self.candidate_history.append(new_candidate)

            new_weights, player_time_spent = self.timed_request(
                {'new_candidate': new_candidate,
                 'weight_history': self.weight_history,
                 'time_left': self.player_time_left},
                self.player_idx
            )

            # check weights validity
            if not self.check_weights_validity(self.weights, new_weights, self.weight_history[-1]):
                print('Invalid Weights provided by Player at iteration {iterations}. Maximum score so far: {self.maxScore}')
                raise ValueError()

            self.weight_history.append(new_weights)


            score = max(self.compute_score(weights=new_weights, candidate=new_candidate),self.compute_score(weights=self.weights, candidate=new_candidate))
            self.score_history.append(score)

            print("**********************************************")
            print("Iteration Number: ", iterations + 1)
            print("New Candidate: ", new_candidate)
            print("New Weights: ", new_weights)
            print("Score History: ", self.score_history)
            print("**********************************************")

            if score > self.maxScore:
                self.maxScore = score

            if score == 1:
                self.perfect_candidate_found = True

            self.decrement_time(player_time_spent, matchmaker_time_spent)

            iterations += 1

        self.server.send_to_all(
            json.dumps({
                'game_over': True,
                'final_score': self.maxScore,
                'match_found': self.perfect_candidate_found,
                'num_iterations': iterations,
                'total_candidates': self.candidate_history.__len__()
            })
        )
