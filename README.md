# DatingGameArchitecture
This is the architecture for the [Dating Game](https://cs.nyu.edu/courses/fall18/CSCI-GA.2965-001/dating.html) for the Heuristics class.

## Running the game

This architecture uses `python3.6`

`cd` into this project and run `python run_game.py <n>` where n is the number of attributes no more than 200. For example:

`python run_game.py 100`

## Player Client

In the clients folder you will find player_client.py. In the function your_algorithm you can place your code for creating the weights for the n attributes. These weights must meet the following specifications:

* The weights must range between -1 and 1
* The sum of the positive weights must be 1
* The sum of the negative weights must be -1
* No more than 5% of the n weights can be modified on each turn
* No attribute weights can be changed by more than 20% with respect to it's original weight
* The weights may have no more than two digits to the right of the decimal point

The player client has access to the following information:

* `self.n` The number of attributes
* `self.time_left` The amount of time remaining out of 120 seconds
* `self.weight_history` A list of previous weights provided by player
* `candidate_history` A list containing all of the previous candidates provided by the matchmaker

## Matchmaker Client

In the clients folder you will also find matchmaker_client.py. In the function my_candidate you can place your code for creating new candidates for the player. These candidates must meet the following specifications

* Each value lies between 0 and 1
* Each value must have four or fewer digits of precision

The matchmaker_client has access to the following information

* `self.n` The number of attributes
* `self.time_left` The amount of time remaining out of 120 seconds
* `self.random_candidates_and_scores` A dictionary containing the 40 randomly generated candidates and their scores
* `self.prev_candidate` A dictionary of the previous candidate, containing their attributes, scores and iteration


## Scoring

Each contestant will take a turn as the matchmaker and as the player. The winner is the contestant that finds and ideal (score = 1) candidate in the fewest number of iterations. If no contestant finds an ideal candidate as the matchmaker then the winner is the contestant the achieves the highest score as the matchmaker.

