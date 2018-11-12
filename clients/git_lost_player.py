import json
import random
from clients.client import Player


class Player(Player):

    def __init__(self):
        super(Player, self).__init__("Git lost player", is_player=True)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        # print('Player', game_info)  # commented out
        self.n = game_info['n']
        self.weight_history = []
        self.time_left = 120
        self.candidate_history = []
        self.current_weights = None  # will be filled in during play_game()

        # My instance variables
        self.originals = []
        self.indices_to_alter = []

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

    def rand_list(self, cap, length):
        """
        Return a list of length 'length' of random numbers that sum to 1.
        """

        # Get entries in array
        lst = [random.randint(1, cap) for _ in range(length)]

        # Try to get entries to sum to 1
        lst_sum = sum(lst)
        lst = [n/lst_sum for n in lst]

        # Round to 2 decimal places
        lst = [max(round(n, 2), 0.01) for n in lst]

        # Continue adjusting sum, then rounding
        while round(sum(lst), 2) != 1.0:
            while round(sum(lst), 2) < 1.0:
                idx = random.randint(0, len(lst) - 1)
                lst[idx] += 0.01
            while round(sum(lst), 2) > 1.0:
                idx = random.randint(0, len(lst) - 1)
                if lst[idx] - 0.01 > 0.0:
                    lst[idx] -= 0.01
            lst = [max(round(n, 2), 0.01) for n in lst]

        return lst

    def your_algorithm(self, candidate_history):
        """
        PLACE YOUR ALGORITHM HERE
        As the player, you have access to
            - self.n = the number of attributes
            - candidate_history = the history of candidates
            - self.time_left = clock time left
        You must return an array of weights. The weights may be positive or negative ranging from -1 to 1 and
        specified as decimal values having at most two digits to the right of the decimal point. The sum of negative
        weights must be -1 and the sum of positive weights must be 1.
        """

        # First turn: make original weights
        # Strategy: values are close to or equal to 0 to avoid M detecting which are positive/negative
        if len(self.originals) == 0:

            # Decide how many entries will be zero, positive, or negative
            percent_pos = random.randint(36, 41)
            num_pos = int(self.n * percent_pos / 100)
            percent_neg = random.randint(17, 23)
            num_neg = int(self.n * percent_neg / 100)
            num_zeros = self.n - num_pos - num_neg

            # Get different parts of the list
            zeros = [0 for _ in range(num_zeros)]
            pos = self.rand_list(18, num_pos)
            neg = self.rand_list(23, num_neg)
            neg = [-1.0*n for n in neg]  # negate

            # Put parts of the array together and shuffle--these will be our original weights
            together = zeros + pos + neg
            random.shuffle(together)

            # Set instance variables
            self.originals = together
            self.indices_to_alter = [i for i in range(len(self.originals)) if self.originals[i] != 0]

            # Return chosen weights
            return self.originals

        # Subsequent turns: fine tune weights
        # Rule 1: no more than 5% of the weights can change with respect to the previous round
        # Rule 2: no weight can deviate by more than 20% from its original value
        else:

            # Make result
            result = self.originals[:]

            # Find which 5% of entries to randomly alter (pick ones we haven't altered yet)
            num_to_alter = int(self.n * 0.05)
            indices = random.sample(self.indices_to_alter, min(len(self.indices_to_alter), num_to_alter))
            for idx in indices:
                self.indices_to_alter.remove(idx)

            # Randomly make tradeoffs between pairs of those indices
            for _ in range(10):
                # Take some from result[idx1] and give it to result[idx2]
                if len(indices) < 2:
                    break
                idx1, idx2 = random.sample(indices, 2)
                if result[idx1] < result[idx2]:
                    temp = idx1
                    idx1 = idx2
                    idx2 = temp
                shift = min(result[idx1] - 0.8 * self.originals[idx1], 1.2 * self.originals[idx2] - result[idx2], 1.0)
                delta = round(int((0.85 * shift) * 100.0) / 100.0, 2)
                if 0.8 * self.originals[idx1] <= round(result[idx1] - delta, 2) <= 1.2 * self.originals[idx1] \
                        and 0.8 * self.originals[idx2] <= round(result[idx2] + delta, 2) <= 1.2 * self.originals[idx2]:
                    result[idx1] = round(result[idx1] - delta, 2)
                    result[idx2] = round(result[idx2] + delta, 2)

            # Return chosen weights
            return result

# Possibilities:
# - Change the values I chose arbitrarily
# - Make it so indices can be altered more than once
# - Take M's previous guesses into account (candidate_history)
