import json
from random import randint
from time import time

from hps.servers import SocketServer
from websocket_server import WebsocketServer

HOST = '127.0.0.1'
PORT = 5000

WEB_HOST = '127.0.0.1'
WEB_PORT = 8000

class GameServer(object):
    def __init__(self, n=36):
        self.n = n
        self.iterations = 20
        self.weights = [None]*n
        self.candidate_history = []
        self.perfect_candidate_found = False
        self.maxScore = 0
        self.previousCandidate = []

        self.player_time_left = self.matchmaker_time_left = 120
        self.web_server = None
        print('Waiting on port %s for players...' % PORT)
        self.accept_player_connections()


    def accept_player_connections(self):
        self.server = SocketServer(HOST, PORT, 2)
        self.server.establish_client_connections()
        self.player_attributes = [json.loads(info) for info in self.server.receive_from_all()]
        self.player_idx = 0 if self.player_attributes[0]['is_player'] else 1
        self.matchmaker_idx = 0 if self.player_attributes[0]['is_player'] else 1
        self.play_game()


    def timed_request(self, request_data, client_idx):
        self.server.send_to(json.dumps(request_data), client_idx)
        start = time()
        vector = json.loads(self.server.receive_from(client_idx))
        stop = time()
        return vector, (stop - start)


    def decrement_time(self, submarine_time_spent, trench_time_spent):
        self.player_time_left -= submarine_time_spent
        self.matchmaker_time_left -= trench_time_spent


    def check_time_left(self):
        if self.player_time_left < 0:
            raise Exception('Player ran out of time')

        if self.matchmaker_time_left < 0:
            raise Exception('Matchmaker ran out of time')


    def compute_score(self, weights, candidate):
        # TODO: compute the dot product
        score = 0
        return score

    def check_precision(self, candidate):
        # TODO: check if candidate has four or fewer digits of precision
        return True or False

    def check_weights_validity(self, weights):
        # TODO: check if weights are valid wrt the first weights
        return True or False



    def play_game(self):
        self.weights, player_time_spent = self.timed_request(
            {'n': self.n},
            self.player_idx
        )

        # TODO: Generate 20 random candidates and scores
        self.first_candidate, matchmaker_time_spent = self.timed_request(
            {'n': self.n,
             'randomCandidateAndScores': """randomCandidates and scores(dict)"""},
            self.matchmaker_idx
        )

        self.candidate_history.append(self.first_candidate)
        self.decrement_time(player_time_spent, matchmaker_time_spent)

        iterations = self.iterations
        new_weights = self.weights
        new_candidate = self.first_candidate
        while iterations > 0:
            self.check_time_left()

            print("**********************************************")
            # TODO: Print scores
            print("**********************************************")

            if not self.perfect_candidate_found:
                score = self.compute_score(weights=new_weights, candidate=new_candidate)

                if score == 1:
                    self.perfect_candidate_found = True
                    """Do other things that need to be done when game ends like breaking out of this loop"""


                new_weights, player_time_spent = self.timed_request(
                    {'candidate_history': self.candidate_history},
                    self.player_idx
                )

                """check weights validity"""


                new_candidate, matchmaker_time_spent = self.timed_request(
                    {'candidate_score': {'candidate': new_candidate, 'score': score}},
                    self.trench_idx
                )

                """check candidate validity"""

                self.decrement_time(player_time_spent, matchmaker_time_spent)

            iterations -= 1


        self.server.send_to_all(
            json.dumps({
                'game_over': True,
                'final_score': self.maxScore,
                'match_found': self.perfect_candidate_found
            })
        )