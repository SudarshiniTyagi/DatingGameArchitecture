import pickle
import random

random_candidates = {}


for i in range(0, 40):
    rand_cand = []
    # rand_cand = self.load_obj('random_weights/random_weights1.pkl')
    for j in range(0, 25):
        r = random.randint(0, 1)
        rand_cand.append(r)

with open('random_candidates/random_candidates25.pkl', 'wb') as f:
    pickle.dump(rand_cand, f, pickle.HIGHEST_PROTOCOL)