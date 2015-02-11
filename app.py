# -*- coding: utf-8  -*-

import os

import pymongo
import motor
import tornado.ioloop
import tornado.web
from tornado.options import define, options, parse_command_line

from views import MainHandler, OrderWebSockertHandler, NewGameHandler, GameRoomHandler, PrincipalBoardClickedHandler

define("debug", default=False, help="run in debug mode")
define("host", default="localhost", help="app host", type=str)
define("port", default=80, help="app port", type=int)


if __name__ == "__main__":
    parse_command_line()
    application = tornado.web.Application([

                                           (r"/game/(?P<game_id>[^\/]+)", GameRoomHandler),
                                           (r"/new-game/", NewGameHandler),
                                           (r"/websocket", OrderWebSockertHandler),
                                           (r"/principal-board-clicked/", PrincipalBoardClickedHandler),
                                           (r"/", MainHandler),
                                      ],
                                        template_path=os.path.join(os.path.dirname(__file__), "template"),
                                        static_path=os.path.join(os.path.dirname(__file__), "static"),
                                        xsrf_cookies=False,
                                        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
                                        debug=options.debug,
					server_url=options.host,
				        server_port=options.port,
                                        sync_db=pymongo.Connection('mongodb://localhost:27017').game,
                                        async_db=motor.MotorClient('mongodb://localhost:27017').game,
                                     )
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
