import json
from random import random

from clients.client import Player
import numpy as np
from sklearn import linear_model

class MatchMaker(Player):
    def __init__(self):
        super(MatchMaker, self).__init__(name="Wildcats matchmaker", is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        print('Matchmaker', game_info)
        self.random_candidates_and_scores = game_info['randomCandidateAndScores']
        self.n = game_info['n']
        self.prev_candidate = {'candidate': [], 'score': 0, 'iter': 0}
        self.time_left = 120
        self.round = 0
        self.prev_cand = []
        self.candidates = []
        for i in self.random_candidates_and_scores:
            score = self.random_candidates_and_scores[i]['Score']
            attr = self.random_candidates_and_scores[i]['Attributes']
            self.prev_cand.append(attr)
            self.candidates.append((attr, score))

    def play_game(self):

        while True:
            candidate = self.my_candidate()
            self.client.send_data(json.dumps(candidate))
            response = json.loads(self.client.receive_data(32368*2))
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

    def OLStrain(self):
        for x in np.arange(-1.00, 1.05, 0.05):
            candidate = np.ones(self.n) * x
            score = 0.0
            self.candidates.append((candidate, score))
        # candidates 20 * n
        X = np.array([cand[0] for cand in self.candidates])
        # score 20 * 1
        Y = np.array([np.array(cand[1]) for cand in self.candidates])
        # regularization
        R = np.identity(X.shape[1]) * 0.05
        # weights n * 1
        #print(X.shape, Y.shape, R.shape)
        estimate = np.dot(np.dot(np.linalg.inv(np.dot(X.T, X) + np.dot(R.T, R)), X.T), Y).reshape(self.n)
        return estimate

    def Ridgetrain(self):
        X = np.array([cand[0] for cand in self.candidates])
        y = np.array([np.array(cand[1]) for cand in self.candidates])
        clf = linear_model.Ridge(alpha = 1.0)
        clf.fit(X, y)
        return clf.coef_

    def SGDtrain(self):
        X = np.array([cand[0] for cand in self.candidates])
        y = np.array([np.array(cand[1]) for cand in self.candidates])
        clf = linear_model.SGDRegressor(max_iter = 1000)
        clf.fit(X, y)
        return clf.coef_

    changed_index = []
    def findmin(self, weight):
        pos_minw = 10.0
        neg_minw = 10.0
        pos_id = -1
        neg_id = -1
        for i in range(len(weight)):
            if i in self.changed_index:
                continue
            if weight[i] > 0:
                if weight[i] < pos_minw:
                    pos_minw = weight[i]
                    pos_id = i
            else:
                if abs(weight[i]) < neg_minw:
                    neg_minw = abs(weight[i])
                    neg_id = i
        self.changed_index.append(pos_id)
        self.changed_index.append(neg_id)
        return pos_id, neg_id

    prev_score = -1.0
    this_score = 0
    prev_pid = 0
    prev_nid = 0
    prevp = 0.0
    prevn = 0.0
    def my_candidate(self):
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
        if self.round > 1:
            self.candidates.append((self.prev_candidate['candidate'], self.prev_candidate['score']))
            self.prev_cand.append(self.prev_candidate['candidate'])
            if self.round > 2:
                self.prev_score = self.this_score
            self.this_score = self.prev_candidate['score']
            print(self.prev_score, self.this_score)
            weights1 = self.OLStrain()
            weights2 = self.Ridgetrain()
            weights3 = self.SGDtrain()

        else:
            weights1 = self.OLStrain()
            weights2 = self.Ridgetrain()
            weights3 = self.SGDtrain()
        self.round += 1

        candidate = []
        is_pos = []
        is_neg = []
        could_be_pos = []
        could_be_neg = []

        avg = []
        for i in range(self.n):
            w1 = weights1[i]
            w2 = weights2[i]
            w3 = weights3[i]
            #avg_w = (w1 + w2 + w3) / 3
            avg_w = w3
            avg.append(avg_w)
            if avg_w > 2.5 / self.n:
                candidate.append(1)
                is_pos.append(i)
            elif avg_w > 0:
                candidate.append(1)
                could_be_pos.append(1)
            elif avg_w < -2.5 / self.n:
                candidate.append(0)
                is_neg.append(i)
            else:
                candidate.append(0)
                could_be_neg.append(i)


        if candidate in self.prev_cand:
            if self.round > 5 and self.n > 100 and self.this_score < self.prev_score:
                candidate[self.prev_pid] = self.prevp
                candidate[self.prev_nid] = self.prevn
            pid, nid = self.findmin(avg)
            self.prev_pid, self.prev_nid = pid, nid
            self.prevp = candidate[pid]
            self.prevn = candidate[nid]
            candidate[pid] = -candidate[pid]
            candidate[nid] = -candidate[nid]
            if candidate not in self.prev_cand:
                self.prev_cand.append(candidate)
                return candidate
        else:
            self.prev_cand.append(candidate)
            return candidate
