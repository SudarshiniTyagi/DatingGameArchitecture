import json
import random

from clients.client import Player
from decimal import *
import numpy as np

class Player(Player):
    def __init__(self):
        super(Player, self).__init__(name="Wildcats player", is_player=True)
        game_info = json.loads(self.client.receive_data(32368*2))
        print('Player', game_info)
        self.n = game_info['n']
        self.weight_history = []
        self.time_left = 120
        self.candidate_history = []

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

    def your_algorithm(self, candidate_history):
        """
        PLACE YOUR ALGORITHM HERE
        As the player, you have access to the number of attributes (self.n),
        the history of candidates (candidate_history)
        and clock time left (self.time_left).
        You must return an array of weights.
        The weights may be positive or negative ranging from -1 to 1 and
        specified as decimal values having at most two digits to the right of the decimal point, e.g. 0.13 but not 0.134
        Also the sum of negative weights must be -1 and the sum of positive weights must be 1.
        """
        getcontext().prec = 2
        if not self.weight_history:   ## no zero
            pos_num = random.randrange(1, min(100, self.n))
            neg_num = self.n - pos_num
            print(pos_num, neg_num)
            pos_pool = [Decimal(0.01) for i in range(pos_num)]
            neg_pool = [Decimal(-0.01) for i in range(neg_num)]
            for i in range(100 - pos_num):
                choose_index = random.randrange(0, pos_num)
                pos_pool[choose_index] += Decimal(0.01)
            for i in range(100 - neg_num):
                choose_index = random.randrange(0, neg_num)
                neg_pool[choose_index] += Decimal(-0.01)
            weight_pool = pos_pool + neg_pool
            ideal = []
            for i in range(self.n):
                pop_range = len(weight_pool)
                choose_index = random.randrange(0, pop_range)
                temp = weight_pool.pop(choose_index)
                ideal.append(float(temp))
            self.ideal = ideal
            print("ideal = ", ideal)
            return ideal
        else:
            return self.ideal


        if not self.candidate_history: ## first round
            getcontext().prec = 2
            divide = self.n //2
            zero_num = self.n - divide * 2
            ideal = []
            if 50 < divide <= 100:
                fraction = Decimal(0.01)
                # rest = int((1 - 0.01 * divide) / 0.01)
                rest = 100 - divide
            elif 25 < divide <= 50:
                fraction = Decimal(0.02)
                rest = 50 - divide
            elif 20 < divide <= 25:
                fraction = Decimal(0.04)
                rest = 25 - divide
            elif 10 < divide <= 20:
                fraction = Decimal(0.05)
                rest = 20 - divide
            else:
                fraction = Decimal(0.10)
                rest = 10 - divide
            pos_set = [fraction for i in range(divide)]
            neg_set = [-fraction for i in range(divide)]
            for i in range(rest):
                # while(1):
                choose_pos_index = random.randrange(0, divide)
                #     if(pos_set[choose_pos_index] != 1):
                #         break
                # while(1):
                choose_neg_index = random.randrange(0, divide)
                    # if(pos_set[choose_neg_index] != -1):
                    #     break
                pos_set[choose_pos_index] += fraction
                neg_set[choose_neg_index] -= fraction

            for i in range(divide):
                ideal.append(pos_set[i])
                ideal.append(neg_set[i])

            for i in range(zero_num):
                choose_zero_index = random.randrange(0, self.n)
                ideal.insert(choose_zero_index, 0)


            for i in range(self.n):
                ideal[i] = float(ideal[i])
                # float(format(pos_set[choose_pos_index], '.2f'))
            pos = 0
            neg = 0
            for i in range(self.n):
                if ideal[i] < 0:
                    neg += ideal[i]
                else:
                    pos += ideal[i]
            self.ideal = ideal
            print("POS = ", pos)
            print("NEG = ", neg)
            print("ideal = ", ideal)
            return ideal
        else:
            return self.ideal
