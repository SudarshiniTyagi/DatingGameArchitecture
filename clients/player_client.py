import json
from random import randint

from clients.client import Player


class Player(Player):
    def __init__(self, name):
        super(Player, self).__init__(name=name, is_player=True)
        game_info = json.loads(self.client.receive_data())
        print('Player', game_info)
        self.n = game_info['n']
        self.initial_weights = [None]*self.n
        self.current_weights = [None]*self.n

    def play_game(self):
        response = {}
        while True:
            new_weights = self.your_algorithm(response['candidate_history'])
            self.client.send_data(json.dumps({"new_weights": new_weights}))
            self.current_weights = new_weights
            response = json.loads(self.client.receive_data())
            print("New Candidate Received")
            if 'game_over' in response:
                if 'match_found' in response:
                    print("Perfect Candidate Found")
                    print("Total candidates used = ", response['final_score'])
                else:
                    print("Perfect candidate not found")
                    print("Total candidates used = ", response['final_score'])
                exit(0)



    def your_algorithm(self, candidate_history):
        """
        PLACE YOUR ALGORITHM HERE
        As the player, you have access to the number of attributes (self.n),
        the history of candidates (self.candidate_history) and clock time left.
        You must return an array of weights.
        The weights may be positive or negative ranging from -1 to 1 and
        specified as decimal values having at most two digits to the right of the decimal point, e.g. 0.13 but not 0.134
        """
        return randint(-1, 1)