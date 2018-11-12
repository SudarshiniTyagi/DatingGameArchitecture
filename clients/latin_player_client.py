import json
import random
import time
import math
import copy

from clients.client import Player


class Player(Player):
    def __init__(self):
        super().__init__(name="Latin Player", is_player=True)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        print('Player', game_info)
        self.n = game_info['n']
        self.weight_history = []
        self.time_left = 120
        self.candidate_history = []
        self.turn = 0
        self.change_counter = 0
        self.neg_denom = -.1

        pos_num = 0
        neg_num = 0
        initial_weights = []
        pos_map = {}
        neg_map = {}


        pos_counter = 0
        neg_counter = 0




        if self.n >= 0:

            pos_dist = 5


            if self.n >= 20 and self.n < 40:
                pos_dist = 10
            elif self.n >= 40 and self.n < 50:
                pos_dist = 20
            elif self.n >= 50 and self.n < 100:
                pos_dist = 25
            elif self.n >= 100 and self.n < 150:
                pos_dist = 50
            elif self.n >= 150:
                pos_dist = 100

            while pos_counter < pos_dist:
                target = random.randint(0, self.n - 1)
                #print(pos_counter)
                if not target in pos_map:
                    #print("not in dic")
                    pos_map[target] = 1
                    pos_counter += 1

            #print("YYYY")
            #print(pos_map, pos_counter)

            if self.n < 20:
                while neg_counter < 5:
                    target = random.randint(0, self.n - 1)

                    if not target in pos_map and not target in neg_map:
                        neg_map[target] = 1
                        neg_counter += 1
            else:
                while neg_counter < 10:
                    target = random.randint(0, self.n - 1)

                    if not target in pos_map and not target in neg_map:
                        neg_map[target] = 1
                        neg_counter += 1

            print(neg_map)

            pos_value = round(1 / pos_dist, 2)

            x = 0

            if self.n < 20:
                self.neg_denom = -.2

            for i in range(0, self.n):
                if i in pos_map:
                    initial_weights.append(pos_value)
                    x += 1
                elif i in neg_map:
                    if self.n < 20:
                        initial_weights.append(self.neg_denom)
                    else:
                        initial_weights.append(self.neg_denom)
                else:
                    initial_weights.append(0)

        self.neg_map = neg_map
        self.pos_map = pos_map



        #print("vvvvvvvvvvvvvvvvvvvvvvvv")
        #print(initial_weights)

        self.initial_weights = initial_weights


        #print("aaaaaaaa", self.n)
        print("game_info", game_info)

    def play_game(self):
        response = {}
        while True:
            new_weights = self.your_algorithm(0 if not response else self.candidate_history)
            #print("LLLL", new_weights)
            print(json.dumps(new_weights))
            time.sleep(1)
            #print("let's go")
            self.client.send_data(json.dumps(new_weights))
            time.sleep(5)
            #print("something happen?")

            self.current_weights = new_weights.copy()


            #print("ummm")
            response = json.loads(self.client.receive_data(size=32368*2))
           # print("HIHI?")

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


        self.turn += 1
        #print("KKKKK")
        #print(self.turn, candidate_history)






        #return [-.89,.89,-.11,.11] + [0 for i in range(self.n - 4)]

        if candidate_history == 0:
            new_list = self.initial_weights.copy()
            return new_list

        #for hist in candidate_history:
         #   print("EEEEEEEEEEEEEEEEEEEEEEEEE")
        #    for i in hist:
         ##       print("lol")
         #       print(i)

        num_attribute_change = int(math.floor(.05 * self.n) / 2)
        #print("num", num_attribute_change)


        if num_attribute_change > 1:

            curr_history = candidate_history[len(candidate_history) - 1]
            #check positive/negative

            matched_neg = []
            unmatched_neg = []



            if self.turn == 9 or self.turn == 8 or self.turn == 7 or self.turn == 6 or self.turn == 3 or self.turn == 2:

                for i in self.neg_map:
                    if curr_history[i] > .5:
                        unmatched_neg.append(i)
                    else:
                        matched_neg.append(i)


            else:
                for i in self.neg_map:
                    if curr_history[i] < .5:
                        unmatched_neg.append(i)
                    else:
                        matched_neg.append(i)



            #print("JJJJJJ", num_attribute_change)


            lower_array = min(len(unmatched_neg), len(matched_neg))

            #print("JJJJ2222", len(unmatched_neg), len(matched_neg))

            swap_count = min(lower_array, num_attribute_change)

            unmatched_target = random.sample(set(unmatched_neg), swap_count)
            matched_target = random.sample(set(matched_neg), swap_count)


            #print(unmatched_target)
            #print(matched_target)

            #print("LLL")
            #print(swap_count)
            #print(self.initial_weights)


            for i in range(0, swap_count):
                limit = round(self.initial_weights[unmatched_target[i]] * .2, 2)
                #print("PPP", limit)


                curr_unmatch = self.current_weights[unmatched_target[i]]
                curr_match = self.current_weights[matched_target[i]]

                #print(curr_unmatch)
                #print(curr_match)


                if curr_unmatch > self.neg_denom and curr_match > self.neg_denom:
                    continue

                if curr_unmatch < self.neg_denom and curr_match < self.neg_denom:
                    continue

                if curr_unmatch != self.neg_denom and curr_match == self.neg_denom:
                    continue

                if curr_unmatch == self.neg_denom and curr_match != self.neg_denom:
                    continue



                unmatch_weight = self.initial_weights[unmatched_target[i]]
                match_weight = self.initial_weights[matched_target[i]]


                self.current_weights[unmatched_target[i]] = round(unmatch_weight + limit, 2)
                self.current_weights[matched_target[i]] = round(match_weight - limit, 2)

            #print(self.initial_weights)
           # print("----------------------------------------")




        return self.current_weights
        #return self.initial_weights

