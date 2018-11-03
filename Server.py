import random
import copy
from decimal import *

#class variables
  self.no_attributes
  self.candidate_history = []

def playgame(self):

  infinity=100000
  n=self.no_attributes
  orig_weights=[]
  for i in range(0,n):
    orig_weights.append(0)

  # send n to player
  #start player timer
  #recieve orig_weights from Player (size n list)
  #pause player timer
  #check player timer <120s
  
  if(not check_validity(orig_weights)):
    return (-1,infinity,"Invalid Weights from Player")
  
  random_candidates=[]
  for i in range(0,20):
    rand_cand=[]
    for j in range(0,n):
      r=randInt(0,1)
      rand_cand.append(r)
      
    score=dotpdt(rand_cand,orig_weights)
    random_candidates.append((score,rand_cand))
    
  
  #send list random_candidates to mm
  
  getcontext().prec = 5
  max_score=0
  for i in range(0,20):
    current_candidate=[]
    #start mm timer
    #recieve current_candidate from mm (list of length n with values between 0,1 and precion 4 after decimal point)
    #pause mm timer
    #check mm timer <!20s
    
    if(not check_cand_validity(current_candiddate)):
      return (i,max_score,"Candidate from Matchmaker does not satisfy constraints")
    
    candidate_history.append(current_candidate)
    
    #send candidate history to Player
    #start player timer
    #recieve new_weights from Player
    #pause player timer
    #check player timer <120s
    
    if(not check_new_weight_validity(new_weights,orig_weights)):
      return (i,infinity,"Invalid Change to Weights from Player")
    
    score_current_candidate=dotpdt(new_weights,current_candidate)
    
    if(score_current_candidate==1):
      return (i,1,"Matchmaker was sucessful")
    
    #send score_current_candidate to mm
    
  return (20,max_score,"Ideal candidate not found")
   





