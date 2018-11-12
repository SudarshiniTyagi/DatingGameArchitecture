import json
import random
from sklearn import linear_model
from sklearn import svm
import numpy as np
from scipy.optimize import linprog
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import time

from clients.client import Player


class MatchMaker(Player):
    def __init__(self):
        super(MatchMaker, self).__init__(name="Redis matchmaker", is_player=False)
        game_info = json.loads(self.client.receive_data(size=32368*2))
        print('Matchmaker', game_info)
        self.random_candidates_and_scores = game_info['randomCandidateAndScores']
        self.n = game_info['n']
        self.prev_candidate = {'candidate': [], 'score': 0, 'iter': 0}
        self.time_left = 120
        self.candidate_history = {}
        self.cand_number = len(self.random_candidates_and_scores) + 1
        self.iter = 0
        self.initial_best = {}

    def play_game(self):

        best_cand = None
        best_score = -2

        self.all_candidates = []
        self.all_scores = []

        for cnum, val in self.random_candidates_and_scores.items():
            self.candidate_history[cnum] = {'score': val['Score'], 'attributes': val['Attributes']}
            self.all_candidates.append(val['Attributes'])
            self.all_scores.append(val['Score'])
            if val['Score'] > best_score:
                best_score = val['Score']
                best_cand = val['Attributes']

        self.best_score = best_score
        self.best_cand = best_cand

        self.initial_best['score'] = self.best_score
        self.initial_best['candidate'] = self.best_cand

        while True:
            candidate = self.my_candidate()
            self.client.send_data(json.dumps(candidate))
            response = json.loads(self.client.receive_data(32368*2))
            if 'game_over' in response:
                scores = [val['Score'] for i, val in self.random_candidates_and_scores.items()]
                print(max(scores))
                if response['match_found']:
                    print("Perfect Candidate Found")
                    print("Total candidates used = ", response['num_iterations'])
                else:
                    print("Perfect candidate not found - you have failed the player")
                    print("Total candidates used = ", response['total_candidates'])
                exit(0)
            else:
                self.prev_candidate = response['prev_candidate']
                self.time_left = response['time_left']
                self.iter = response['prev_candidate']['iter']
                if len(self.prev_candidate['candidate']) > 0:
                    self.candidate_history[self.cand_number] = {'score': self.prev_candidate['score'], 'attributes': self.prev_candidate['candidate']}
                    self.cand_number += 1
                    self.all_candidates.append(self.prev_candidate['candidate'])
                    self.all_scores.append(self.prev_candidate['score'])

    def my_candidate(self):

        """
        PLACE YOUR CANDIDATE GENERATION ALGORITHM HERE
        As the matchmaker, you have access to the number of attributes (self.n),
        initial random candidates and their scores (self.random_candidates_and_scores),
        your clock time left (self.time_left)
        and a dictionary of the previous candidate sent (self.prev_candidate) consisting of
            'candidate' = previous candidate attributes
            'score' = previous candidate score
            'iter' = iteration num of previous candidate
        For this function, you must return an array of values that lie between 0 and 1 inclusive and must have four or
        fewer digits of precision. The length of the array should be equal to the number of attributes (self.n)
        """

        # print(self.best_score)
        # print(self.best_cand)

        if self.initial_best['score'] == 1:
            return self.initial_best['candidate']

        if self.n < 85:
            X = np.array(self.all_candidates)
            y = np.array(self.all_scores)

            if self.iter % 2 == 0:
                lin_reg = LinearRegression()

                print("X:" + str(X))
                print("y:" + str(y))
                lin_reg.fit(X, y)
                w = lin_reg.coef_
                print("lr w:" + str(w))
                result = []
                for i in w:
                    if i > 0:
                        result.append(1)
                    else:
                        result.append(0)
                print("lr candidate:" + str(result))
                return result

            else:
                fourth = int(self.n / 4)
                if self.iter == 1:
                    return [0] * fourth + [1] * (self.n - fourth)

                elif self.iter == 3:
                    return [1] * fourth + [0] * fourth + [1] * (self.n - 2 * fourth)

                elif self.iter == 5:
                    return [1] * (2 * fourth) + [0] * fourth + [1] * (self.n - 3 * fourth)

                elif self.iter == 7:
                    return [1] * (3 * fourth) + [0] * (self.n - 3 * fourth)

                s = np.sum(X, axis=0)
                ratio = int(0.2 * self.n)
                idx = np.argpartition(s, ratio)[:ratio]
                print("lowest 20% of indices:" + str(idx))
                arr = []
                for i in range(self.n):
                    if i in idx:
                        arr.append(1)
                    else:
                        arr.append(0)
                print("column sum:" + str(s))
                print("column average and std:" + str(np.mean(s)) + ", " + str(np.std(s)))
                return arr

        if self.iter == 0 or self.iter == 2:
            X = np.array(self.all_candidates)
            y = np.array(self.all_scores)
            lin_reg = LinearRegression()

            print("X:" + str(X))
            print("y:" + str(y))
            lin_reg.fit(X, y)
            #   print("score:"+str(lin_reg.score(X, y)))
            w = lin_reg.coef_
            print("lr w:" + str(w))
            result = []
            for i in w:
                if i > 0:
                    result.append(1)
                else:
                    result.append(0)
            return result

        fourth = int(self.n / 4)
        if self.iter == 1:
            return [0] * fourth + [1] * (self.n - fourth)

        elif self.iter == 3:
            return [1] * fourth + [0] * fourth + [1] * (self.n - 2 * fourth)

        elif self.iter == 4:
            return [1] * (2 * fourth) + [0] * fourth + [1] * (self.n - 3 * fourth)

        elif self.iter == 5:
            return [1] * (3 * fourth) + [0] * (self.n - 3 * fourth)

        if self.iter == 19:
            if self.best_score < self.initial_best['score']:
                return self.initial_best['candidate']

        if self.iter % 3 == 1 and self.iter < 12:

            X = np.array(self.all_candidates)
            s = np.sum(X, axis=0)
            ratio = int(0.2 * self.n)
            idx = np.argpartition(s, ratio)[:ratio]
            print("lowest 20% of indices:" + str(idx))
            arr = []
            for i in range(self.n):
                if i in idx:
                    arr.append(1)
                else:
                    arr.append(0)
            print("column sum:" + str(s))
            print("column average and std:" + str(np.mean(s)) + ", " + str(np.std(s)))
            # [random.randint(0, 1) for i in range(self.n)]
            return arr

        elif self.iter % 3 == 2 and self.iter != 19:
            X = np.array(self.all_candidates)
            y = np.array(self.all_scores)
            lin_reg = LinearRegression()

            print("X:" + str(X))
            print("y:" + str(y))
            lin_reg.fit(X, y)
            #   print("score:"+str(lin_reg.score(X, y)))
            w = lin_reg.coef_
            print("lr w:" + str(w))
            result = []
            for i in w:
                if i > 0:
                    result.append(1)
                else:
                    result.append(0)
            return result

        starttime = time.time()

        if self.prev_candidate['score'] > self.best_score:
            self.best_score = self.prev_candidate['score']
            self.best_cand = self.prev_candidate['candidate']

        weight_vectors = []

        # Count of positive associations
        weights = {}
        for x in range(0, self.n):
            supersum = 0
            for cnum, val in self.candidate_history.items():
                # print(val)
                supersum += val['attributes'][x] * val['score']
            weights[x] = supersum

        output = []
        for x, val in weights.items():
            if val > 0:
                output.append(1)
            else:
                output.append(0)

        weight_vectors.append(output)

        weights = {}
        for x in range(0, self.n):
            supersum = 0
            for cnum, val in self.candidate_history.items():
                # print(val)
                if val['score'] > 0:
                    supersum += 1
            weights[x] = supersum

        output = []
        for x, val in weights.items():
            if val/len(self.candidate_history) > 0.5:
                output.append(1)
            else:
                output.append(0)

        weight_vectors.append(output)

        # Create Feature Vector and Target
        fv = [[1] * self.n]
        target = [0]
        for cnum, vals in self.candidate_history.items():
            fv.append(vals['attributes'])
            target.append((vals['score']))

        # Ridge
        for alp in np.logspace(-3, 2, 15):
            reg = linear_model.Ridge(alpha=alp)
            reg.fit(fv, target)
            # print(reg.coef_)
            # print(np.sum(reg.coef_))

            output = []
            for val in reg.coef_:
                if val > 0:
                    output.append(1)
                else:
                    output.append(0)

            weight_vectors.append(output)

        # Lasso
        for alp in np.logspace(-3, 2, 15):
            reg = linear_model.Lasso(alpha=alp)
            reg.fit(fv, target)
            # print(reg.coef_)
            # print(np.sum(reg.coef_))

            output = []
            for val in reg.coef_:
                if val > 0:
                    output.append(1)
                else:
                    output.append(0)

            weight_vectors.append(output)

        # SGD
        for alp in np.logspace(-3, 2, 15):
            for pen in ['l1', 'l2', 'elasticnet']:
                reg = linear_model.SGDRegressor(loss='squared_loss', penalty=pen, alpha=alp)
                reg.fit(fv, target)
                # print(reg.coef_)
                # print(np.sum(reg.coef_))

                output = []
                for val in reg.coef_:
                    if val > 0:
                        output.append(1)
                    else:
                        output.append(0)
                weight_vectors.append(output)

                reg = linear_model.SGDRegressor(loss='huber', penalty=pen, alpha=alp)
                reg.fit(fv, target)
                # print(reg.coef_)
                # print(np.sum(reg.coef_))

                output = []
                for val in reg.coef_:
                    if val > 0:
                        output.append(1)
                    else:
                        output.append(0)
                weight_vectors.append(output)

        # Bayseian
        for alp in np.logspace(-3, 2, 15):
            reg = linear_model.BayesianRidge(alpha_1=alp, alpha_2=alp, lambda_1=alp, lambda_2=alp)
            reg.fit(fv, target)
            # print(reg.coef_)
            # print(np.sum(reg.coef_))

            output = []
            for val in reg.coef_:
                if val > 0:
                    output.append(1)
                else:
                    output.append(0)

            weight_vectors.append(output)

        lin_reg = LinearRegression()
        X = np.array(self.all_candidates)
        y = np.array(self.all_scores)
        # print("X:" + str(X))
        # print("y:" + str(y))
        lin_reg.fit(X, y)
        #   print("score:"+str(lin_reg.score(X, y)))
        w = lin_reg.coef_
        print("lr w:" + str(w))
        result = []
        for i in w:
            if i > 0:
                result.append(1)
            else:
                result.append(0)

        # Compute likelihood of positive weight
        weight_prob = []
        total_num = len(weight_vectors)
        for x in range(0, self.n):
            num_pos = 0
            for weights in weight_vectors:
                num_pos += weights[x]

            lin = result[x]
            num_pos = num_pos + lin*total_num
            total_num = total_num*2
            weight_prob.append(round((num_pos/total_num),4))

        output_vector = None
        backup_vector = None
        max_score = -2
        backup_score = -2

        rf1_10 = RandomForestRegressor(n_estimators=10, criterion='mse')
        rf1_50 = RandomForestRegressor(n_estimators=50, criterion='mse')
        rf1_100 = RandomForestRegressor(n_estimators=100, criterion='mse')

        rf2_10 = RandomForestRegressor(n_estimators=10, criterion='mae')
        rf2_50 = RandomForestRegressor(n_estimators=50, criterion='mae')
        rf2_100 = RandomForestRegressor(n_estimators=100, criterion='mae')

        rf1_10.fit(fv, target)
        rf1_50.fit(fv, target)
        rf1_100.fit(fv, target)
        rf2_10.fit(fv, target)
        rf2_50.fit(fv, target)
        rf2_100.fit(fv, target)

        while True:
            if time.time() - starttime > 14:
                break

            final_vector = self.best_cand
            # for x in weight_prob:
            #     val = int(np.random.choice([0, 1], p=[1 - x, x]))
            #     final_vector.append(val)
            counter = -1
            for x in weight_prob:
                counter += 1
                if x > 0.5:
                    if final_vector[counter] == 1:
                        final_vector[counter] = int(np.random.choice([0, 1], p=[(1 - x)/2, x + ((1-x)/2)]))
                    else:
                        final_vector[counter] = int(np.random.choice([0, 1], p=[1 - x, x]))
                if x < 0.5:
                    if final_vector[counter] == 0:
                        final_vector[counter] = int(np.random.choice([0, 1], p=[1 - x + x/2, x/2]))
                    else:
                        final_vector[counter] = int(np.random.choice([0, 1], p=[1 - x, x]))

            vector = np.array(final_vector).reshape(1,-1)

            scores = []

            scores.append(rf1_10.predict(vector))
            scores.append(rf1_50.predict(vector))
            scores.append(rf1_100.predict(vector))
            scores.append(rf2_10.predict(vector))
            scores.append(rf2_50.predict(vector))
            scores.append(rf2_100.predict(vector))

            score = sum(scores)/len(scores)
            if score > max_score:
                if final_vector not in self.all_candidates:
                    output_vector = final_vector
                    max_score = score
            if score > backup_score:
                backup_vector = final_vector
                backup_score = score

        # print(weight_prob)
        # print(final_vector)

        # time.sleep(0.3)
        if output_vector is None:
            return backup_vector
        return output_vector