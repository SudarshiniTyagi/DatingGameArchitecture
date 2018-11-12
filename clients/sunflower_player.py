import json
import random
import numpy as np
from heapq import heappush, heappop

from clients.client import Player


class Player(Player):
    def __init__(self):
        super(Player, self).__init__(name="Sunflower", is_player=True)
        game_info = json.loads(self.client.receive_data(32368*2))
        print('Player', game_info)
        self.n = game_info['n']
        self.numAttr = self.n
        self.weight_history = []
        self.time_left = 120
        self.candidate_history = []
        self.initialWeights = []
        self.nextWeight = []
        self.current_weights = None

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

        # start = random.choice([[1,-1],[-1,1]])
        # v1 = [-.9,.9,-.1,.1] + [0 for i in range(self.n - 4)]
        # v2 = [-.89,.89,-.11,.11] + [0 for i in range(self.n - 2)]
        # return random.choice([v1,v2])


        if not candidate_history:
            weights = self.getValidWeights().tolist()
            self.nextWeight = self.initialWeights
            weights = [round(x, 2) for x in weights]
            # import pdb; pdb.set_trace()
            return weights
        else:
            weights = self.getNewWeights(candidate_history[-1])
            weights = [round(x, 2) for x in weights]
            # import pdb; pdb.set_trace()
            return weights


    def getNewWeights(self, guess):
        # import pdb; pdb.set_trace()
        noise = self.getNoise(self.nextWeight, guess)
        if self.checkSum(self.nextWeight + noise):
            self.nextWeight = self.nextWeight + noise
        return self.nextWeight

    def getValidWeights(self):
        while(True):
            self.initialWeights = self.get_valid_weights(self.numAttr)
            if(self.checkSum(self.initialWeights)):
                return self.initialWeights
        return self.initialWeights 

    def get_valid_weights(self, n):
        totalNumbersInWeights = n
        positiveNumbersInWeights = int(38 * totalNumbersInWeights / 100)
        amountOfNegativeNumbersInWeights = totalNumbersInWeights - positiveNumbersInWeights
        positiveWeights = np.random.random(positiveNumbersInWeights)
        totalSumOfPositiveWeights = 0
        negativeWeights = np.random.random(amountOfNegativeNumbersInWeights)
        totalSumOfNegativeWeights = 0
        combinedWeights = np.concatenate((positiveWeights, negativeWeights))
        for i in combinedWeights:
            if i > 0:
                totalSumOfPositiveWeights += i
        for i in negativeWeights:
            totalSumOfNegativeWeights += i
        newSum = 0
        maxValPositive = 0
        minValPositive = 1
        maxValPositiveIndex = 0
        minValPositiveIndex = 0
        for index, item in enumerate(combinedWeights):
            if index < positiveNumbersInWeights:
                positiveWeights[index]=round(item / totalSumOfPositiveWeights, 2)
                newSum += positiveWeights[index]
                if(positiveWeights[index] > maxValPositive):
                    maxValPositive = positiveWeights[index]
                    maxValPositiveIndex = index
                if(positiveWeights[index] < minValPositive):
                    minValPositive = positiveWeights[index]
                    minValPositiveIndex = index
        howOffFromOnePositive = 1 - newSum
        if(howOffFromOnePositive>0):
            positiveWeights[minValPositiveIndex] = positiveWeights[minValPositiveIndex] + howOffFromOnePositive
        if(howOffFromOnePositive<0):
            positiveWeights[maxValPositiveIndex] = positiveWeights[maxValPositiveIndex] + howOffFromOnePositive

        newSumNegative = 0
        maxVal = 0
        minVal = 1
        maxValIndex = 0
        minValIndex = 0
        for index, item in enumerate(negativeWeights):
            negativeWeights[index]=-round(item / totalSumOfNegativeWeights, 2)
            newSumNegative += -negativeWeights[index]
            if(-negativeWeights[index] > maxVal):
                maxVal = -negativeWeights[index]
                maxValIndex = index
            if(-negativeWeights[index] < minVal):
                minVal = -negativeWeights[index]
                minValIndex = index
        howOffFromOneNegative = 1 - newSumNegative
        if(howOffFromOneNegative > 0):
            negativeWeights[minValIndex] = negativeWeights[minValIndex] - howOffFromOneNegative
        if(howOffFromOneNegative < 0):
            negativeWeights[maxValIndex] = negativeWeights[maxValIndex] - howOffFromOneNegative

        combinedWeights = np.concatenate((positiveWeights, negativeWeights))
        np.random.shuffle(combinedWeights)
        return combinedWeights
    def checkSum(self, weights):
        sum_pos = 0.0
        sum_neg = 0.0
        for w in weights:
            if w >= 0:
                if w >= 1:
                    return False
                sum_pos += w
            else:
                if w <= -1:
                    return False
                sum_neg += w
        if np.round(sum_pos, 2) - 1 != 0 or np.round(sum_neg, 2) + 1 != 0:
            return False
        return True

    def getNoise(self, weights,response):
        noise = np.zeros(len(weights))
        pos_heap = []
        neg_heap = []
        for index in range(len(weights)):
            if(weights[index]>0):
                heappush(pos_heap, (weights[index],index))
            if(weights[index]<0):
                heappush(neg_heap, (-1 * weights[index],index))
        addList = []
        subsList = []
        while(len(pos_heap)):
            (val,i) = heappop(pos_heap)
            if(val>=.05 and response[i]>0):
                subsList.append((val,i));
            if(val>=.05 and response[i]==0):
                addList.append((val,i))
        minLength = min(len(addList),len(subsList))
        maxIterations = int(5*len(weights)/100)-1
        if(maxIterations<2):
            return noise
        maxIterations -= maxIterations % 2
        count = 0
        for index in range(minLength):
            (addVal,addIndex) = addList[index]
            (subsVal,subsIndex) = subsList[index]
            val = min(addVal,subsVal)
            val = val*float(random.randint(5, 10)/100)
            #val = val*float(10/100)
            val = round(val,2)
            noise[addIndex] = val
            noise[subsIndex]= -1*val
            count +=2
            if(count>=maxIterations):
                return noise
        addList = []
        subsList = []
        while(neg_heap):
            (val,i) = heappop(neg_heap)
            if(val>=.05 and response[i]>0):
                subsList.append((val,i));
            if(val>=.05 and response[i]==0):
                addList.append((val,i))
        minLength = min(len(addList),len(subsList))
        for index in range(minLength):
            (addVal,addIndex) = addList[index]
            (subsVal,subsIndex) = subsList[index]
            val = min(addVal,subsVal)
            val = val*float(random.randint(5, 10)/100)
            #val = val*float(10/100)
            val = round(val,2)
            noise[addIndex] = val
            noise[subsIndex]= -1*val
            count +=2
            if(count>=maxIterations):
                return noise
        return noise

#def main():

    # n = sys.argv[1]
    # randomFile = sys.argv[2]

    # player_1 = Process(target=init_matchmaker, args=('Player Sam',))
    # player_1.start()
    # # player_2 = Process(target=init_player, args=('Matchmaker Inav',))
    # # player_2.start()

    # controller = GameServer(n)
    #player = Player(name="Foo")
    #player.play_game()

#if __name__ == '__main__':
    #main()
