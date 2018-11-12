import sys

from argparse import ArgumentParser
from multiprocessing import Process
from time import sleep

from dating_server import GameServer

from clients.wdk_matchmaker_client import MatchMaker as MatchMaker
from clients.git_lost_player import Player as Player


def init_matchmaker(name):
    sleep(1)
    player = MatchMaker()
    player.play_game()

def init_player(name):
    sleep(1)
    player = Player()
    player.play_game()

def main():

    n = sys.argv[1]
    randomFile = sys.argv[2]

    print("n: ", n, "Random File: ", randomFile)
    player_1 = Process(target=init_matchmaker, args=('Player Sam',))
    player_1.start()
    player_2 = Process(target=init_player, args=('Matchmaker Inav',))
    player_2.start()

    controller = GameServer(n, randomFile)

if __name__ == '__main__':
    main()
