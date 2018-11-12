import json
import random

from clients.client import Player


class Player(Player):
    def __init__(self):
        super(Player, self).__init__(name="Greedy god player", is_player=True)
        game_info = json.loads(self.client.receive_data(size=32368*2))
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
        if candidate_history == 0:
            return self.__initial_parameters__()
        else:
            return self.__update_parameters__(candidate_history)

    def __initial_parameters__(self):
        n = self.n
        half_n = (n + 1) // 2
        weights = [0.0] * n
        if n < 100:
            # Strategy 1
            for i in range(100):
                rand_idx1 = random.randint(0, half_n - 1)
                rand_idx2 = random.randint(half_n, n - 1)
                weights[rand_idx1] += 0.01
                weights[rand_idx2] -= 0.01
        else:
            # Strategy 2
            idx1, idx2 = (0, 0)
            for i in range(100):
                weights[idx1] += 0.01
                weights[half_n + idx2] -= 0.01
                idx1 = (idx1 + 1) % half_n
                idx2 = (idx2 + 1) % (n - half_n)

        random.shuffle(weights)
        print(weights)
        return [round(weights[i], 2) for i in range(n)]

    def __update_parameters__(self, candidate_history):
        return self.current_weights