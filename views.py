# -*- coding: utf-8  -*-

from uuid import uuid4
import json
from Cookie import Cookie
import random

from bson import ObjectId
import tornado.web
import tornado.websocket


def check_board(board, line_length=19, column_length=19):
    for i in range(column_length):
        for j in range(line_length):
            if not board[i][j]:
                continue
            if j+4 < line_length:
                if not [k for k in range(1, 5) if board[i][j] != board[i][j+k]]:
                    return {'colour': board[i][j], 'line': [(i, j+k) for k in range(0, 5)]}
            if i+4 < column_length:
                if not [k for k in range(1, 5) if board[i][j] != board[i+k][j]]:
                    return {'colour': board[i][j], 'line': [(i+k, j) for k in range(0, 5)]}
            if j+4 < line_length and i+4 < column_length:
                if not [k for k in range(1, 5) if board[i][j] != board[i+k][j+k]]:
                    return {'colour': board[i][j], 'line': [(i+k, j+k) for k in range(0, 5)]}
            if j-4 >= 0 and i+4 < column_length:
                if not [k for k in range(1, 5) if board[i][j] != board[i+k][j-k]]:
                    return {'colour': board[i][j], 'line': [(i+k, j-k) for k in range(0, 5)]}
    return False


def get_or_create_session(request):
    session_id = request.get_secure_cookie('session_id')
    if not session_id:
        session_id = uuid4().hex
        request.set_secure_cookie('session_id', session_id)
    return session_id


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        get_or_create_session(self)
        self.render("index.html")


class OrderWebSockertHandler(tornado.websocket.WebSocketHandler):
    clients = {}

    def get_board_status(self, game_id):
        game = self.settings['sync_db']['game'].find_one({'_id': ObjectId(game_id)})
        if game['host_session_id'] == self.session_id:
            role = 'host'
        elif game['opponent_session_id'] == self.session_id:
            role = 'opponent'
        elif self.session_id in game['visitor_session_ids']:
            role = 'visitor'
        board_info = game['board_info']
        return board_info, role

    def check_origin(self, origin):
        return True

    def open(self):
        pass

    def on_close(self):
        del OrderWebSockertHandler.clients[self.session_id]

    def game_broadcast(cls, game_id, message):
        print cls.clients
        game_id = ObjectId(game_id)
        game = cls.settings['sync_db']['game'].find_one({'_id': game_id})
        c = cls.clients.get(game.get('host_session_id', ''), '')
        if c:
            message.update({'role': 'host'})
            c.write_message(message)
        print game.get('opponent_session_id', '')
        print cls.clients.get(game.get('opponent_session_id', ''), '')

        c = cls.clients.get(game.get('opponent_session_id', ''), '')
        if c:
            message.update({'role': 'opponent'})
            c.write_message(message)
        cs = [cls.clients.get(_id) for _id in game.get('visitor_session_ids', [])]
        for c in cs:
            if c:
                message.update({'role': 'visitor'})
                c.write_message(message)

    def on_message(self, message):
        print message
        message = json.loads(message)
        game_id = message.get('game_id', '')
        if message.get('action') == 'select_box':
            game_id = message.get('game_id')
            i = message.get('i')
            j = message.get('j')
            role = message.get('role')
            game = game_id and self.settings['sync_db']['game'].find_one({'_id': ObjectId(game_id)}) or {}
            if ((role == 'host' and game['host_session_id'] == self.session_id)
                or (role == 'opponent' and game['opponent_session_id'] == self.session_id)) \
                and (game['board_info']['board'][i][j] == '') \
                and game['board_info']['actual_turn'] == role:
                game['board_info']['board'][i][j] = role
                game['board_info']['actual_turn'] = role == 'host' and 'opponent' or 'host'
                board_check_status = check_board(game['board_info']['board'], line_length=19, column_length=19)
                if board_check_status:
                    game['board_info']['actual_turn'] = 'Finished'
                self.settings['sync_db']['game'].save(game)
                board_info, role = self.get_board_status(game_id)
                self.game_broadcast(game_id, {'action': 'board_status_after_click',
                                              'board_info': board_info,
                                              'role': role,
                                              'board_check_status': board_check_status})

        if message.get('action') == 'bind_cookie':
            session = str(message.get('cookie', ''))
            session = Cookie(session)['session_id'].value
            session_id = self.get_secure_cookie('session_id', session)
            self.session_id = session_id
            OrderWebSockertHandler.clients[session_id] = self
            game = game_id and self.settings['sync_db']['game'].find_one({'_id': ObjectId(game_id)}) or {}

            if game and not ('board_info' in game) and game_id and game.get('opponent_session_id') == self.session_id:
                message = {}
                colour = ['black', 'white']
                random.shuffle(colour)
                message.update({'host_colour': colour[0], 'opponent_colour': colour[1]})
                start_turn, actual_turn = '', ''
                if message['host_colour'] == 'white':
                    start_turn = 'host'
                    actual_turn = 'host'
                else:
                    start_turn = 'opponent'
                    actual_turn = 'opponent'
                message.update({'start_turn': start_turn, 'actual_turn': actual_turn})
                board = [[''] * 19] * 19
                message.update({'board': board})
                message = {'action': 'start_game', 'board_info': message}
                game.update(message)
                self.settings['sync_db']['game'].save(game)
                self.game_broadcast(game_id, message)
            elif 'board_info' in game:
                board_info, role = self.get_board_status(game_id)
                board_check_status = check_board(game['board_info']['board'], line_length=19, column_length=19)
                self.write_message({'action': 'board_status',
                                    'board_info': board_info,
                                    'role': role,
                                    'board_check_status': board_check_status})

    def callback(self, count):
        pass


class NewGameHandler(tornado.web.RequestHandler):
    def get(self):
        session_id = get_or_create_session(self)
        game = self.settings['sync_db']['game'].insert({'host_session_id': session_id})
        self.write(json.dumps({'status': 0, 'game_id': str(game)}))
        self.finish()


class GameRoomHandler(tornado.web.RequestHandler):
    def get(self, game_id):
        session_id = get_or_create_session(self)
        game_id = ObjectId(game_id)
        game = self.settings['sync_db']['game'].find_one({'_id': game_id})
        ret = {}
        if not game:
            ret = {'status': 0}
        else:
            if game['host_session_id'] == session_id:
                # game host
                ret.update({'status': 1, 'role': 'host'})
            else:
                opponent_session_id = game.get('opponent_session_id', '')
                # print opponent_session_id, session_id
                if opponent_session_id and opponent_session_id != session_id:
                    # append visitors
                    if not game.get('visitor_session_ids'):
                        game['visitor_session_ids'] = []
                    if session_id not in game['visitor_session_ids']:
                        game['visitor_session_ids'].append(session_id)
                        self.settings['sync_db']['game'].save(game)
                    ret.update({'status': 1, 'role': 'visitor'})
                else:
                    # opponent
                    if not opponent_session_id:
                        game['opponent_session_id'] = session_id
                        self.settings['sync_db']['game'].save(game)
                    ret.update({'status': 1, 'role': 'opponent'})
        self.write(json.dumps(ret))
        self.finish()


class PrincipalBoardClickedHandler(tornado.web.RequestHandler):
    def get(self):
        principal_board = self.settings['sync_db']['principal_board'].find_one()
        self.write(json.dumps({'board': principal_board['board']}))
        self.finish()

    def post(self):
        data_json = tornado.escape.json_decode(self.request.body)
        box_id = data_json['box_id']
        # box_id = self.get_argument('box_id')
        box, i, j = box_id.split('-')
        i = int(i)
        j = int(j)
        principal_board = self.settings['sync_db']['principal_board'].find_one()
        principal_board['board'][i][j] = not principal_board['board'][i][j]
        self.settings['sync_db']['principal_board'].save(principal_board)
        self.write(json.dumps({'board': principal_board['board']}))
        self.finish()
