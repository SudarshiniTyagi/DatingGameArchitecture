import json
import math
import random

from clients.client import Player


class Player(Player):
    def __init__(self):
        super(Player, self).__init__(name="We don't know player", is_player=True)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        print('Player', game_info)
        self.n = game_info['n']
        self.weight_history = []
        self.time_left = 120
        self.candidate_history = []
        self.weights = []

    def play_game(self):
        response = {}
        while True:
            print(self.name)
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
        def up(a):
            return math.ceil(a*100)/100
        def down(a):
            return math.floor(a*100)/100

        if len(self.weights) == 0:
            pos = self.n // 2
            neg = self.n - pos
            posW = []
            negW = []
            sumW = 0
            for i in range(pos-1):
                realSum = i/pos
                if sumW <= realSum:
                    posW.append(up(1/pos))
                else:
                    posW.append(down(1/pos))
                sumW += posW[-1]
            intW = [int(round(x*100)) for x in posW]
            posW.append((100 - sum(intW))/100)

            sumW = 0
            for i in range(neg-1):
                realSum = -i/neg
                if sumW <= realSum:
                    negW.append(up(-1/neg))
                else:
                    negW.append(down(-1/neg))
                sumW += negW[-1]
            intW = [int(round(x*100)) for x in negW]
            negW.append((-100 - sum(intW))/100)
            self.weights = posW + negW
            random.shuffle(self.weights)
            random.shuffle(self.weights)
        # print("My weights:")
        # print(list(enumerate(self.weights)))
        # print("***********")
        return self.weights
