import json

from clients.client import Player

class MatchMaker(Player):
    def __init__(self, name):
        super(MatchMaker, self).__init__(name=name, is_player=False)
        game_info = json.loads(self.client.receive_data())
        print('Matchmaker', game_info)
        self.random_candidates_and_scores = game_info['random_candidates_and_scores']
        self.n = game_info['n']
        self.candidate_score = {'candidate': [], 'score': 0}

    def play_game(self):
        first_candidate = self.my_candidate()
        self.client.send_data(json.dumps({"first_candidate": first_candidate}))
        while True:
            candidate = self.my_candidate()
            self.client.send_data(json.dumps({"candidate": candidate}))
            response = json.loads(self.client.receive_data())
            self.candidate_score = response['candidate_score']
            print("Candidate Score: ", self.candidate_score)

            if 'game_over' in response:
                if 'match_found' in response:
                    print("Perfect Candidate Found")
                    print("Total candidates used = ", response['final_score'])
                else:
                    print("Perfect candidate not found")
                    print("Total candidates used = ", response['final_score'])
                exit(0)

    def my_candidate(self):
        """
        PLACE YOUR CANDIDATE GENERATION ALGORITHM HERE
        As the matchmaker, you have access to the number of attributes (self.n),
        initial random candidates and their scores (self.random_candidates_and_scores),
        score of each candidate (self.candidate_score) and clock time left.
        For this function, you must return an array of values that lie between 0 and 1 inclusive and must have four or
        fewer digits of precision. The length of the array should be equal to the number of attributes (self.n)
        """
        return []
