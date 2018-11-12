import json

import time
import random
import math
from clients.client import Player

class Candidate:
    def __init__(self, iter, score, atts):
        self.score = score
        self.n = len(atts)
        self.atts = atts
        self.iter = iter
    def remove(self, sure):
        for ind in sure:
            if self.atts[ind] > 0:
                self.score -= 1.0/self.n
            else:
                self.score += 1.0/self.n
        self.atts = [x for ind,x in enumerate(self.atts) if ind not in sure]
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        s = "Candidate " + str(self.iter) + " has score " + str(self.score) + "\n"
        s += "Attributes: " + str(self.atts)
        return s


class MatchMaker(Player):
    def __init__(self):
        super(MatchMaker, self).__init__(name="We don't know matchmaker", is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        # print('Matchmaker', game_info)
        self.random_candidates_and_scores = game_info['randomCandidateAndScores']

        self.candidates = []
        for iter in self.random_candidates_and_scores:
            candi = self.random_candidates_and_scores[iter]
            self.candidates.append(Candidate(int(iter), candi['Score'], candi['Attributes']))

        self.n = game_info['n']
        self.prev_candidate = {'candidate': [], 'score': 0, 'iter': 0}
        self.time_left = 120
        self.randomTime = 7
        self.svmTime = 10

        self.cand = {}
        self.max_score = -1
        self.max_score_candidate = []

        self.weight = [-(1.0/(self.n/2))]*int(self.n/2) + [(1.0/(self.n - self.n/2))]*(self.n - int(self.n/2))
        self.train = []
        self.dev = []
        self.best_weight = self.weight

        self.round_n = 1
        self.maxTime = 0


        random.shuffle(self.weight)
        print(len(self.weight))



        for item in self.random_candidates_and_scores:
            att = self.random_candidates_and_scores[item]["Attributes"]
            score = self.random_candidates_and_scores[item]["Score"]
            negative_att = [(1 - i) for i in att]
            negative_score = 0 - score
            self.cand[tuple(att)] = score
            self.cand[tuple(negative_att)] = negative_score

        self.data_set = []

    def get_atts_score(self, candi1, candi2):
        n = len(candi1.atts)
        atts = [0]*n
        score = candi1.score*candi2.score
        if score > 0:
            for i in range(n):
                if candi1.atts[i] == candi2.atts[i]:
                    if candi1.score > 0:
                        if candi1.atts[i] == 1:
                            atts[i] += score
                        else:
                            atts[i] -= score
                    else:
                        if candi1.atts[i] == 1:
                            atts[i] -= score
                        else:
                            atts[i] += score
        else:
            for i in range(n):
                if candi1.atts[i] != candi2.atts[i]:
                    if candi1.score > 0: #candi2.score < 0
                        if candi1.atts[i] == 1:
                            atts[i] += abs(score)
                        else:
                            atts[i] -= abs(score)
                    else:
                        if candi1.atts[i] == 1:
                            atts[i] -= abs(score)
                        else:
                            atts[i] += abs(score)
        return atts

    def get_reputation(self, candis):
        n = len(candis[0].atts)
        repu = [0]*n
        maxAbs = 0
        for candi in candis:
            maxAbs = max(maxAbs, abs(candi.score))
        threshHold = maxAbs*0.4
        selects = []
        for candi in candis:
            if abs(candi.score) >= threshHold:
                selects.append(candi)
        assert len(selects) > 1, "Bad situation"
        for i in range(len(selects)):
            for j in range(len(selects)):
                if i < j:
                    candi1 = selects[i]
                    candi2 = selects[j]
                    atts = self.get_atts_score(candi1, candi2)
                    for k in range(n):
                        repu[k] += atts[k]
        return repu

    def play_game(self):
        self.pre_process()
        self.svm(1, 200)
        while True:
            print(self.name)
            candidate = self.my_candidate()
            self.client.send_data(json.dumps(candidate))
            response = json.loads(self.client.receive_data(size=32368*2))
            self.round_n+=1
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


    def sgd(self, lr):
        random.shuffle(self.train)
        for item in self.train:
            inp = item[0]
            ans = item[1]
            expected_ans = sum([inp[i]*self.weight[i] for i in list(range(self.n))])
            learned = -lr*(expected_ans - ans)
            self.weight = [self.weight[i]+learned*inp[i] for i in list(range(self.n))]
            return self.weight




    def train_data(self, iteration, lr):
        lr = lr / (math.sqrt(self.n)*math.sqrt((float(iteration))))
        weight = self.sgd(lr)
        total_false = 0
        for item in self.dev:
            inp = item[0]
            ans = item[1]
            expected_ans = sum([inp[i]*self.weight[i] for i in list(range(self.n))])
            # print("True value:", ans)
            # print("Predicted: ", expected_ans)
            difference = abs(ans - expected_ans)
            total_false+=difference
        total_false = total_false/len(self.dev)
        print("false rate is:", total_false)
        return total_false

    def svm(self, lr, iterations):
        false_rate = 1
        for i in range(iterations):
            print("Iteration: ", i)
            false_rate_it = self.train_data(i+1, lr)
            if false_rate_it<false_rate:
                false_rate = false_rate_it
                self.best_weight = self.weight



    def both_own_both_not_own(self, a, b):
        own = []
        not_own = []
        for i in range(len(a)):
            if a[i] == b[i] and a[i] == 1:
                own.append(1)
                not_own.append(0)
            elif a[i] == b[i] and a[i] == 0:
                own.append(0)
                not_own.append(1)
            else:
                own.append(0)
                not_own.append(0)
        return own, not_own

    def pre_process(self):
        for a in self.cand:
            for b in self.cand:
                if a!=b:
                    own, not_own = self.both_own_both_not_own(a, b)
                    ## ---------------important -------------------------------
                    ## so remember, the attributes they both not own minus the attributes they both own is the score we have
                    difference = -self.cand[a] - self.cand[b]
                    if difference>0:
                        difference = 1
                    else:
                        difference = -1
                    p = []
                    for i in range(len(own)):
                        p.append(0)

                    for i in range(len(own)):
                        if own[i] == 1:
                            p[i] = -1
                        elif not_own[i] == 1:
                            p[i] = 1
                    self.data_set.append((p, difference))

        # self.data_set += [(x, self.cand[x]) for x in self.cand]

        random.shuffle(self.data_set)
        self.train = self.data_set[0:int(0.8*len(self.data_set))]
        # self.dev = [(x, self.cand[x]) for x in self.cand]
        self.dev = self.data_set[int(0.8*len(self.data_set)):]






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
        if len(self.prev_candidate['candidate']) == self.n:
            self.candidates.append(Candidate(len(self.candidates), self.prev_candidate['score'], self.prev_candidate['candidate']))
        print("TIME LEFT:", self.time_left, "s")
        if self.randomTime > 0:
            self.randomTime -= 1
            cand = []
            for i in range(self.n):
                val = random.random()
                if val > 0.5:
                    cand.append(1)
                else:
                    cand.append(0)
            return cand
        if self.time_left > self.maxTime*2+2 and self.svmTime > 0:
            self.svmTime -=1
            start = time.time()
            if len(self.prev_candidate["candidate"])!=0:
                print(11111111111111111111111111111111111)
                prev_cand = self.prev_candidate["candidate"]
                prev_score = self.prev_candidate["score"]
                negative_cand = [1-x for x in prev_cand]
                negative_score = - prev_score

                for a in self.cand:
                    b = tuple(prev_cand)
                    if (a!=b):
                        own, not_own = self.both_own_both_not_own(a, b)
                        difference = -self.cand[a] - prev_score
                        if difference>0:
                            difference = 1
                        else:
                            difference = -1
                        p = []
                        for i in range(len(own)):
                            p.append(0)

                        for i in range(len(own)):
                            if own[i] == 1:
                                p[i] = -1
                            elif not_own[i] == 1:
                                p[i] = 1
                        self.data_set.append((p, difference))
                random.shuffle(self.data_set)
                self.train = self.data_set[0:int(0.8*len(self.data_set))]
                # self.dev = [(x, self.cand[x]) for x in self.cand]
                self.dev = self.data_set[int(0.8*len(self.data_set)):]
                self.svm(1/self.round_n, 200)
            end = time.time()
            print("TOOK ", end-start, "s")
            self.maxTime = max(self.maxTime, end-start)
            cand = []
            for item in self.weight:
                if item>0:
                    cand.append(1)
                else:
                    cand.append(0)
            return cand
        else:
            start = time.time()
            repu = self.get_reputation(self.candidates)
            end = time.time()
            print("ONLY TOOK", end-start, "s")
            cand = []
            for item in repu:
                if item>0:
                    cand.append(1)
                else:
                    cand.append(0)
            return cand
