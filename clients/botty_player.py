import json
import random
import math
from collections import deque, namedtuple
from decimal import *

from .client import Player


class Player(Player):
    def __init__(self):
        getcontext().prec = 6
        super().__init__(name="BottyMcBotFace", is_player=True)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        print('Player', game_info)
        self.n = game_info['n']
        self.weight_history = []
        self.time_left = 120
        self.candidate_history = []

    def play_game(self):
        response = {}
        while True:
            new_weights = self.your_algorithm(self.candidate_history)
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
        # print(f"Generating Candidate #{len(self.candidate_history) + 1}...")
        if len(self.candidate_history) == 0:
            cand = self.generateFirst()
        else:
            cand = self.generateModified()
        cand = [float(Decimal(i) / Decimal(100)) for i in cand]
        print(f"Candidate #{len(self.candidate_history) + 1}:", cand)
        return cand

    def generateFirst(self):
        v = [0.0] * self.n
        pos = 100
        neg = 100
        while pos != 0 or neg != 0:
            empty = [ind for ind in range(self.n) if v[ind] == 0.0]
            if len(empty) == 2:
                v[empty[0]] = pos
                v[empty[1]] = -neg
                return v
            ind = random.choice(empty)
            if random.randint(1, 2) == 1:
                partial = random.randint(0, min(int(400 / self.n), pos))
                v[ind] = partial
                pos -= partial
            else:
                partial = random.randint(0, min(int(400 / self.n), neg))
                v[ind] = partial * -1
                neg -= partial
        return v

    def generateModified(self):
        first = [i * 100 for i in self.weight_history[0]]
        last_cand = [i * 100 for i in self.candidate_history[-1]]
        last = [i * 100 for i in self.weight_history[-1]]
        new = last[:]

        diffs = [(last[i] * last_cand[i], i) for i in range(self.n) if last[i] > 0]
        diffs = sorted(diffs, reverse=True)

        max_modified = math.floor(.05 * self.n)
        modified = 0

        while modified < max_modified and len(diffs) > 0:
            _, ind = diffs.pop(0)
            inds_to_incr = []

            new_val = math.ceil(first[ind] * .8)

            difference = abs(last[ind] - new_val)
            if difference == 0:
                continue

            for _, i in reversed(diffs):
                new_incr_val = min(last[i] + difference, math.floor(first[i] * 1.2))
                difference -= abs(new_incr_val - last[i])
                inds_to_incr.append((i, new_incr_val))
                if difference == 0:
                    break

            if len(inds_to_incr) + 1 + modified <= max_modified and difference == 0:
                print(f"CHANGED INDEX {ind} SOMETHING")
                temp = new[:]
                modified += 1 + len(inds_to_incr)

                for i, v in inds_to_incr:
                    temp[i] = v
                temp[ind] = new_val

                excluded = [i for i, v in inds_to_incr]
                new_diffs = []
                for i in range(len(diffs)):
                    if i not in excluded:
                        new_diffs.append(diffs[i])

                pos_sum = sum([i for i in temp if i > 0])
                neg_sum = sum([i for i in temp if i < 0])
                if pos_sum == 100 and neg_sum == -100:
                    new = temp

                diffs = new_diffs

        # if not self.isValidModification([i / 100.0 for i in new]):
            # print("Warning: Not a valid candidate")
        return new

    def isValidModification(self, v):
        first_v = self.candidate_history[0]
        num_modifed = 0
        for i, j in zip(v, first_v):
            if i != j:
                if i > 1.2 * j or i < .8 * j:
                    print("Modified a weight more than 20%")
                    return False
                num_modifed += 1
        if num_modifed > math.floor(self.n * .05):
            print("Modified too many weights")
            return False
        return True
