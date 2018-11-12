import json
import random
import numpy as np

from clients.client import Player


class Player(Player):
    def __init__(self):
        super(Player, self).__init__(name="Redis Player", is_player=True)
        game_info = json.loads(self.client.receive_data(32368*2))
        print('Player', game_info)
        self.n = game_info['n']
        self.original_weights = []
        self.pos_index = []
        self.neg_index = []
        self.first_time = True
        self.weight_history = []
        self.weight_changed = [0 for i in range(self.n)]
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
        if self.first_time:
            self.first_time = False
            # generate original weights randomly
            if self.n % 2 == 0:
                p = np.random.random(int(self.n/2))

            else:
                p = np.random.random(int((self.n/2)+1))
               
            p = np.around((p / np.sum(p)), decimals = 2).tolist()
            n = np.random.random(int(self.n/2))
            n =  np.around(-1*(n / np.sum(n)), decimals = 2).tolist()
            #print("p:"+str(p))
            #print("n:"+str(n))
            result = []
            # check sum and combine
            for i in p:
                result.append(i)

            result[-1] = round(1 - (sum(result)-result[-1]), 2)

            for i in n:
                result.append(i)

            result[-1] = round(0 - (sum(result)-result[-1]), 2)

            random.shuffle(result)
            self.original_weights = result
           
            self.pos_index = [i for i in range(self.n) if result[i] > 0]
            self.neg_index = [i for i in range(self.n) if result[i] < 0]
            return self.original_weights
        else:
            # tweak original weights 
            # pick the weight corresponding to matchmaker's largest attribute
            # decrease by 10%
            # distribute the remaining to make sum(pos weight) = 1 and sum(neg weight) = 1
            '''
            w = self.original_weights.copy()
            if self.n > 40 and 0 in self.weight_changed:
                rand = random.randint(0, 1)
                c1 = 0
                c2 = 0
                if rand == 0:
                    for i in self.pos_index:
                        if self.weight_changed[i] == 0:
                            w[i] = round(w[i] * 1.1, 3)
                            c1 = i
                            break
                    pos_sum = sum([w[i] for i in self.pos_index])
                    remainder = abs(pos_sum - 1.000)
                    for i in self.pos_index:
                        if self.weight_changed[i] == 0 and remainder < abs(0.2 * w[i]):
                            c2 = i
                            w[i] = w[i] - remainder
                            break
                    if sum([i for i in w if i > 0]) == 1:
                        self.weight_changed[c1] = 1
                        self.weight_changed[c2] = 1
                        return w

                else:
                    for i in self.neg_index:
                        if self.weight_changed[i] == 0:
                            w[i] = round(w[i] * 1.1, 3)
                            c1 = i
                            break
                    neg_sum = sum([w[i] for i in self.neg_index])
                    remainder = neg_sum + 1.000
                    for i in self.neg_index:
                        if self.weight_changed[i] == 0 and w[i] != 0 and abs(remainder) < abs(0.2 * w[i]):
                            c2 = i
                            w[i] = w[i] - remainder
                            break
                    if sum([i for i in w if i < 0]) == -1:
                        self.weight_changed[c1] = 1
                        self.weight_changed[c2] = 1
                        return w

                return self.original_weights
            '''

            return self.original_weights


       
