import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("config", default=None, help="path to game config", type=int)

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
                (r"/", MainHandler),
                (r"/pokersocket", PokerSocketHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        super(Application, self).__init__(handlers, **settings)

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        config_path = options.config
        game_config = sample_game_config  # TODO read config from yaml
        for ai_player in game_config['ai_players']:
            ai_player['type'] = 'ai'
        self.render("index.html", config=game_config)

class PokerSocketHandler(tornado.websocket.WebSocketHandler):

    waiters = set()
    human_players_info = []

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        self.uuid = str(uuid.uuid4())
        PokerSocketHandler.waiters.add(self)

    def on_close(self):
        PokerSocketHandler.waiters.remove(self)

    def send_updates(self, player):
        for waiter in PokerSocketHandler.waiters:
            try:
                print waiter==self
                waiter.write_message(player)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        if messagetype == "action_new_member":  # invoked from js file
            memberlist.append_human_player(message)
            broadcast_member_udpate(memberlist)
        if messagetype == "update_member":
            update_memberlist()
        if messagetype == "action_start_game":  # invoked from js file
            switch_ui_for_game()
            engine = setup_engine(memberlist)
            msgs = engine.start_game()
            broadcast_game_update(msgs)
        if messagetype == "action_declare_action":  # invoked from js file
            msgs = engine.declare_action(message)
            broadcast_game_update(msgs)
        if messagetype == "update_game":
            for msg in msgs:
                for waiter in self.waiters:
                    waiter.write_message(msg)
        print "got message %r" % message
        parsed = tornado.escape.json_decode(message)
        player = {
                "id": str(uuid.uuid4()),
                "type": "human",
                "name": parsed["body"]
                }
        player["html"] = tornado.escape.to_basestring(
                self.render_string("player.html", player=player))
        PokerSocketHandler.human_players_info.append(player)
        self.send_updates(player)

sample_game_config = {
        'max_round': 10,
        'initial_stack': 100,
        'small_blind': 10,
        'ante': 5,
        'blind_structure': None,
        'ai_players': [
            { 'name': "ai1", "path": "path1" },
            { 'name': "ai2", "path": "path2" },
            { 'name': "ai3", "path": "path3" },
        ]
}

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()

