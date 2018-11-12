import time
from itertools import product

import numpy as np

from scipy.optimize import minimize

import json
from random import random

from clients.client import Player

from ga import SAT

def loss(theta, X, y):
    return 1/2 * np.linalg.norm(X.dot(theta) - y)**2

class MatchMaker(Player):
    def __init__(self):
        #print("YOYOYO")
        super().__init__(name="Latin Matchmaker", is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*8))
        #print("YOYOYO222")
        self.random_candidates_and_scores = game_info['randomCandidateAndScores']
        self.data = np.array([[v['Score']]+v['Attributes'] for k,v in self.random_candidates_and_scores.items()])
        #print(self.data, "DDDDDDDDDDDDDDDD")
        self.n = game_info['n']
        self.prev_candidate = {'candidate': [], 'score': 0, 'iter': 0}
        self.time_left = 120
        self.con = [{'type':'eq', 'fun':lambda x: x.sum()}]
        self.bounds = [(-1,1) for i in range(self.n)]
        self.turn  = 0

    def play_game(self):

        while True:
            print("************************************************")
            candidate = self.my_candidate()
            print("################################################")
            print(candidate)
            print("################################################")
            time.sleep(1)
            self.client.send_data(json.dumps(candidate))
            #time.sleep(1)
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
        if self.turn != 0:
            #print("CCCC")
            new_result = [self.prev_candidate['score']] + self.prev_candidate['candidate'] 
            self.data = np.vstack((self.data, new_result))
            X, y= self.data[:,1:], self.data[:,0]

            #print("CCCC222")

            test_weights = minimize(fun=loss, x0=np.zeros(self.n), args=(X,y), constraints=self.con, bounds=self.bounds).x

            ga = SAT(test_weights, 50, 100, 0.95, 0.1)
            ga.evolve()

            #print("CCC3333")
            tmp = ga.best_chrm.tolist()
            #print("1111111", tmp)

            return ga.best_chrm.tolist()
        else:
           # print("CCC444")
            X, y= self.data[:,1:], self.data[:,0]
            #print("CCC5555")
            test_weights = minimize(fun=loss, x0=np.zeros(self.n), args=(X,y), constraints=self.con, bounds=self.bounds).x

            ga = SAT(test_weights, 50, 100, 0.95, 0.1)
            ga.evolve()

            #print("CCCC666")

            tmp = ga.best_chrm.tolist()
            #print("222222222", tmp)

            return tmp
