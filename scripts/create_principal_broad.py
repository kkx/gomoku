# -*- coding: utf-8  -*-

import pymongo

board = [[0] * 19] * 19
print board

db = pymongo.Connection('mongodb://localhost:27017').game
db['principal_board'].insert({'board': board})
