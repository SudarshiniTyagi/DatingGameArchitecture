from collections import Counter

import numpy as np

class SAT():
    """
        Class to determine teams and centers for dancing-without-stars
        Inputs:
            dancers - Dictionary of dancer locations and colors
            colors - Int number of colors
            gen_size - Int size of ga generation
            max_iter - Int number of iterations to run
            cross_pct - Float pct of gen to get from crossover
            mut_pct - Float pct of gen to mutate
            penalty - Int penalty for overlapping centers
    """
    def __init__(self, weights, gen_size, max_iter, cross_pct, mut_pct):
        self.weights = weights
        self.num_att = self.weights.shape[0]
        self.params = {"max_iter":max_iter, "gen_size":gen_size, 
                       "save_k":gen_size - int(cross_pct*gen_size) if int(cross_pct*gen_size) % 2 == 0 else gen_size - int(cross_pct*gen_size)-1, 
                       "cross_k":int(cross_pct*gen_size) if int(cross_pct*gen_size) % 2 == 0 else int(cross_pct*gen_size) + 1, 
                       "mut_k":int(mut_pct*gen_size)}
        
    def evolve(self):
        self.gen = [np.random.choice((0,1), self.num_att) for _ in range(self.params['gen_size'])]
        self.best_chrm, self.best_score = None, 0
        countdown = 5
        
        for i in range(self.params['max_iter']):
            gen_score = self.__genScore__()
            if abs(gen_score.max() - self.best_score) <= 0.0001:
                if countdown == 0:
                    break
                else:
                    countdown -= 1
            else:
                countdown = 5
            
            if gen_score.max() >= self.best_score:
                self.best_chrm = self.gen[gen_score.argmax()]
                self.best_score = gen_score.max()
            new_gen  = self.__selection__(gen_score)
            new_gen += [self.gen[i] for i in gen_score.argsort()[:self.params['save_k']]]
            self.gen = new_gen
            self.__mutate__()

    def __genScore__(self):
        """
            Score generation
            Output:
                chrm_scores - array of scores
        """
        chrm_scores = np.zeros(self.params['gen_size'])
        for c, chrm in enumerate(self.gen):
            score = chrm.dot(self.weights) 
            chrm_scores[c] = 0 if score < 0 else score
            

        return chrm_scores
    
    def __selection__(self, gen_score):
        """
            Do Crossover
            Inputs:
                gen_score - array of scores per generation
            Output:
                new_gen - array of new chromosomes with size gen_size x cross_pct
        """
        new_gen = [[] for i in range(self.params['cross_k'])]
        probs  = gen_score/gen_score.sum()
        
        for i in range(0, len(new_gen), 2):
            p1, p2 = np.random.choice(np.arange(0,self.params['gen_size']), 2, p=probs)
            chrm1, chrm2 = self.__crossover__(self.gen[p1], self.gen[p2])
            new_gen[i] = chrm1
            new_gen[i+1] = chrm2
        
        return new_gen
      
    def __crossover__(self, chrm1, chrm2):
        """
            Crossover then repair new chromosomes
            Input:
                chrm1 - chromosome
                chrm2 - chromosome
            Output:
                cc1 - chromosome
                cc2 - chromosome
        """
        new_chrm1 = np.zeros(self.num_att)
        new_chrm2 = np.zeros(self.num_att)
        for i in range(new_chrm1.shape[0]):
            choice = np.random.randint(2)
            new_chrm1[i] = chrm1[i] if choice == 0 else chrm2[i]
            new_chrm2[i] = chrm1[i] if choice == 1 else chrm2[i]

        return new_chrm1, new_chrm2
    
    def __mutate__(self):
        """
            Mutate chromosomes
        """
        mutated = np.random.choice(np.arange(self.params['gen_size'], dtype=int), self.params['mut_k'], replace=False)
        for i in mutated:    
            col = np.random.choice(self.num_att, 1)
            self.gen[i][col] = 0 if self.gen[i][col] == 1 else 1
            
