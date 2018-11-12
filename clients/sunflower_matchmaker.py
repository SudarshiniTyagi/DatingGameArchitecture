import json
import random
import numpy as np
from sklearn import linear_model
from heapq import heappush, heappop
from clients.client import Player
# from client import Player


class MatchMaker(Player):
    def __init__(self):
        super(MatchMaker, self).__init__("Sunflower matchmaker", is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        print('Matchmaker', game_info)
        self.random_candidates_and_scores = game_info['randomCandidateAndScores']
        self.n = game_info['n']
        self.prev_candidate = {'candidate': [], 'score': 0, 'iter': 0}
        self.time_left = 120
        self.best_score = float(0)
        self.used = 0
        self.best_cand = []
        self.next_cand = []
        self.inti_coef = []
        self.W = np.random.normal(0, 0.001, self.n)
        self.learning_rate = 0.1
        self.Ridge_res = []
        self.init()

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
        if self.used == 0:
            self.next_cand = self.best_cand
        elif self.used == 1:
            self.next_cand = self.Ridge_res
        else:
            # not initial case
            if self.prev_candidate['score'] > self.best_score:
                self.best_score = self.prev_candidate['score']
                self.best_cand = self.prev_candidate['candidate']
                #do some gradient
                print("gradient desent!")
                newscore = self.prev_candidate['score']
                best_cand = self.best_cand.copy()
                X = np.array(best_cand)
                preds = np.dot(self.W, best_cand)
                self.W = self.W - (preds - newscore)*X
                new_cand = []
                for i in range(0, self.n):
                    if np.round(self.W[i], 4) > 0:
                        new_cand.append(1)
                    else:
                        new_cand.append(0)
                self.next_cand = new_cand

            else:
                #do some gradient
                newscore = self.prev_candidate['score']
                best_cand = self.best_cand.copy()
                X = np.array(best_cand)
                preds = np.dot(self.W, best_cand)
                self.W = self.W - (preds - newscore)*X

                new_cand = self.best_cand.copy()
                #new_cand = self.prev_candidate['candidate'].copy()
                candidate_neg = [i for i in range(0, self.n) if self.best_cand[i] == 0]
                candidate_pos = [i for i in range(0, self.n) if self.best_cand[i] > 0]
                random.Random(self.used*self.used).shuffle(candidate_neg)
                random.shuffle(candidate_pos)
                for i in range(0, self.n):
                    if i in candidate_neg[:int(len(candidate_neg)/5)]:
                        new_cand[i] = 1
                    #if i in candidate_pos[:int(len(candidate_pos)/2)]:
                        #new_cand[i] = 0
                self.next_cand = new_cand

        self.used += 1
        print(self.used)
        print(self.next_cand)
        return self.next_cand

    def init(self):

        random_candidates_score = []
        random_candidates_attr = []
        random_candidates = {}
        for _, cand in self.random_candidates_and_scores.items():
            if float(cand['Score']) > self.best_score:
                self.best_score = float(cand['Score'])
                self.best_cand = cand['Attributes']
            #print(cand['Attributes'])
            if cand['Score'] - 1 == 0:
                print(cand['Attributes'])
                print("Best match found by random!")

            random_candidates_attr.append(cand['Attributes'])
            random_candidates_score.append(float(cand['Score']))

        clf = linear_model.Ridge(alpha=0.001, normalize=True, fit_intercept=False, max_iter=5000)
        clf.fit(random_candidates_attr,random_candidates_score)
        
        result = np.where(clf.coef_ > 0)[0].tolist()
        new_cand = []
        for i in range(0, self.n):
            if i in list(result):
                new_cand.append(1)
            else:
                new_cand.append(0)

        self.Ridge_res = new_cand
        self.inti_coef = clf.coef_
        self.W = clf.coef_

        # we also do the initial SDG during the initial time
    # rand_cand = self.load_obj(self.randomFile)


def main():

    # n = sys.argv[1]
    # randomFile = sys.argv[2]

    # player_1 = Process(target=init_matchmaker, args=('Player Sam',))
    # player_1.start()
    # # player_2 = Process(target=init_player, args=('Matchmaker Inav',))
    # # player_2.start()

    # controller = GameServer(n)
    player = MatchMaker(name="Bar")
    player.play_game()

if __name__ == '__main__':
    main()









