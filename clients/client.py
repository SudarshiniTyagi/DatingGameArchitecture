import json
from abc import abstractclassmethod

from hps.clients import SocketClient

HOST = '127.0.0.1'
PORT = 5000

class Player(object):
    def __init__(self, name, is_player):
        self.name = name
        self.is_player = is_player
        self.client = SocketClient(HOST, PORT)
        self.client.send_data(json.dumps({'name': self.name, 'is_player': self.is_player}))

    @abstractclassmethod
    def play_game(self):
        pass