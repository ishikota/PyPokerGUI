import os
import sys
root = os.path.join(os.path.dirname(__file__), "../"*2)
src_path = os.path.join(root, "pypokergui")
print src_path
sys.path.append(root)
sys.path.append(src_path)

import time
import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid

from tornado.options import define, options

import message_processor as MP
import ai_generator

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
        super(Application, self).__init__(handlers, debug=True, **settings)

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html", config=global_game_config, registered=False)

class PokerSocketHandler(tornado.websocket.WebSocketHandler):

    waiters = set()

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        self.uuid = str(uuid.uuid4())
        print "socket opend (uuid=%s)" % self.uuid
        PokerSocketHandler.waiters.add(self)

    def on_close(self):
        print "socket closed(uuid=%s)" % self.uuid
        PokerSocketHandler.waiters.remove(self)
        me = global_game_config.find_member_by_uuid(self.uuid)
        if me:
            global_game_config.remove_member(me)
            self._broadcast_config_update()

    def on_message(self, message):
        print "got message %r" % message  # TODO Remove me
        parsed = tornado.escape.json_decode(message)
        message_type = parsed['type']
        if 'action_new_member' == message_type:
            name = parsed['name']
            global_game_config.append_human_player(name, self.uuid)
            self._broadcast_config_update()
        elif 'action_start_game' == message_type:
            if global_game_config.state != GameConfig.PLAYING_GAME:
                global_game_config.state = GameConfig.PLAYING_GAME
                global_game_config.setup_engine()
                global_game_config.start_game()
                self._broadcast_start_game()
                self._broadcast_update_game()
                if self._is_ai_uuid(global_game_config.next_player_uuid):
                    self._progress_the_game_till_human()
        elif 'action_declare_action' == message_type:
            if self.uuid == global_game_config.next_player_uuid:
                action, amount = parsed['action'], int(parsed['amount'])
                global_game_config.update_game(action, amount)
                self._broadcast_update_game()
                if self._is_ai_uuid(global_game_config.next_player_uuid):
                    self._progress_the_game_till_human()
            else:  # TODO remove this condition because of debug purpose
                print "Received action from wrong player: self=%s, next=%s" % (self.uuid, global_game_config.next_player_uuid)
        else:
            raise Exception("Unexpected message %r received" % message)

    def _is_ai_uuid(self, uuid):
        return len(uuid) <= 2

    def _progress_the_game_till_human(self):
        while self._is_ai_uuid(global_game_config.next_player_uuid):  # TODO break if game has finished
            if global_game_config._has_game_finished(global_game_config.latest_messages): break
            action, amount = global_game_config.ask_action_to_ai(global_game_config.next_player_uuid)
            global_game_config.update_game(action, amount)
            self._broadcast_update_game()

    def _broadcast_config_update(self):
        for waiter in PokerSocketHandler.waiters:
            update = self._gen_config_update_message(waiter.uuid)
            try:
                waiter.write_message(update)
            except:
                logging.error("Error sending message", exc_info=True)

    def _gen_config_update_message(self, my_uuid):
        registered = global_game_config.find_member_by_uuid(my_uuid)
        html_str = self.render_string(
                "game_config.html", config=global_game_config, registered=registered)
        html = tornado.escape.to_basestring(html_str)
                
        return {
                'message_type': 'config_update',
                'html': html,
                'registered': registered
                }

    def _broadcast_start_game(self):
        for waiter in PokerSocketHandler.waiters:
            update = self._gen_start_game_message(waiter.uuid)
            try:
                waiter.write_message(update)
            except:
                logging.error("Error sending message", exc_info=True)

    def _broadcast_update_game(self):
        for dest_uuid, message in global_game_config.latest_messages:
            if dest_uuid == -1:
                for waiter in PokerSocketHandler.waiters:
                    update = self._gen_game_update_message(message)
                    try:
                        waiter.write_message(update)
                    except:
                        logging.error("Error sending message", exc_info=True)
                for _uuid, ai_player in global_game_config.ai_players.items():
                    self._broadcast_message_to_ai(message, ai_player)
            else:
                if len(dest_uuid) <= 2:
                    ai_player = global_game_config.ai_players[dest_uuid]
                    self._broadcast_message_to_ai(message, ai_player)
                else:
                    dest_socket = self._find_socket_by_uuid(dest_uuid)
                    try:
                        update = self._gen_game_update_message(message)
                        dest_socket.write_message(update)
                    except:
                        logging.error("Error sending message", exc_info=True)
            time.sleep(5)

    def _broadcast_message_to_ai(self, message, ai_player):
        message_type = message['message']['message_type']
        if 'round_start_message' == message_type:
            round_count = message['message']['round_count']
            hole_card = message['message']['hole_card']
            seats = message['message']['seats']
            ai_player.receive_round_start_message(round_count, hole_card, seats)
        elif 'street_start_message' == message_type:
            street = message['message']['street']
            round_state = message['message']['round_state']
            ai_player.receive_street_start_message(street, round_state)
        elif 'game_update_message' == message_type:
            action = message['message']['action']
            round_state = message['message']['round_state']
            ai_player.receive_game_update_message(action, round_state)
        elif 'round_result_message' == message_type:
            winners = message['message']['winners']
            round_state = message['message']['round_state']
            hand_info = message['message']['hand_info']
            ai_player.receive_round_result_message(winners, hand_info, round_state)
        elif 'game_result_message' == message_type:
            pass  # ai does not handle game result
        elif 'ask_message' == message_type:
            pass  # ask message handling is done in global_game_config.ask_action_to_ai
        else:
            raise Exception("Unexpected message received : %r" % message)

    def _find_socket_by_uuid(self, uuid):
        target = [sock for sock in self.waiters if sock.uuid == uuid]
        return target[0] if len(target)==1 else None

    def _gen_start_game_message(self, my_uuid):
        registered = global_game_config.find_member_by_uuid(my_uuid)
        html_str = self.render_string(
                "poker_game.html", config=global_game_config, registered=registered)
        html = tornado.escape.to_basestring(html_str)
                
        return {
                'message_type': 'start_game',
                'html': html
                }

    def _gen_game_update_message(self, message):
        message_type = message['message']['message_type']
        if 'round_start_message' == message_type:
            round_count = message['message']['round_count']
            hole_card = message['message']['hole_card']
            event_html_str = self.render_string("event_round_start.html",
                    round_count=round_count, hole_card=hole_card)
            content = {
                    'update_type': message_type,
                    'event_html': tornado.escape.to_basestring(event_html_str)
                    }
        elif 'street_start_message' == message_type:
            round_state = message['message']['round_state']
            street = message['message']['street']
            table_html_str = self.render_string("round_state.html", round_state=round_state)
            event_html_str = self.render_string("event_street_start.html", street=street)
            content = {
                    'update_type': message_type,
                    'table_html': tornado.escape.to_basestring(table_html_str),
                    'event_html': tornado.escape.to_basestring(event_html_str)
                    }
        elif 'game_update_message' == message_type:
            round_state = message['message']['round_state']
            action = message['message']['action']
            action_histories = message['message']['action_histories']
            table_html_str = self.render_string("round_state.html", round_state=round_state)
            event_html_str = self.render_string(
                    "event_update_game.html", action=action, round_state=round_state)
            content = {
                    'update_type': message_type,
                    'table_html': tornado.escape.to_basestring(table_html_str),
                    'event_html': tornado.escape.to_basestring(event_html_str)
                    }
        elif 'round_result_message' == message_type:
            round_state = message['message']['round_state']
            hand_info = message['message']['hand_info']
            winners = message['message']['winners']
            round_count = message['message']['round_count']
            table_html_str = self.render_string("round_state.html", round_state=round_state)
            event_html_str = self.render_string("event_round_result.html",
                    round_state=round_state, hand_info=hand_info, winners=winners, round_count=round_count)
            content = {
                    'update_type': message_type,
                    'table_html': tornado.escape.to_basestring(table_html_str),
                    'event_html': tornado.escape.to_basestring(event_html_str)
                    }
        elif 'game_result_message' == message_type:
            game_info = message['message']['game_information']
            event_html_str = self.render_string("event_game_result.html", game_information=game_info)
            content = {
                    'update_type': message_type,
                    'event_html' : tornado.escape.to_basestring(event_html_str)
                    }
        elif 'ask_message' == message_type:
            round_state = message['message']['round_state']
            hole_card = message['message']['hole_card']
            valid_actions = message['message']['valid_actions']
            action_histories = message['message']['action_histories']
            table_html_str = self.render_string("round_state.html", round_state=round_state)
            event_html_str = self.render_string("event_ask_action.html",
                    hole_card=hole_card, valid_actions=valid_actions,
                    action_histories=action_histories)
            content = {
                    'update_type': message_type,
                    'table_html': tornado.escape.to_basestring(table_html_str),
                    'event_html': tornado.escape.to_basestring(event_html_str)
                    }
        else:
            raise Exception("Unexpected message received : %r" % message)

        return {
                'message_type': 'update_game',
                'content': content
                }

class GameConfig(object):

    WAITING_ROOM = 0
    PLAYING_GAME = 1

    def __init__(self):
        self.members = []
        self.ai_players = {}
        self.rule = None
        self.state = self.WAITING_ROOM
        self.latest_messages = []

    def define_rule(self, max_round, initial_stack, small_blind, ante, blind_structure):
        self.rule = {
            'max_round': max_round,
            'initial_stack': initial_stack,
            'small_blind': small_blind,
            'ante': ante,
            'blind_structure': blind_structure
        }

    def append_ai_player(self, name, setup_script_path):
        member = self._gen_player_info("ai", name, setup_script_path)
        self.members.append(member)

    def append_human_player(self, name, uuid):
        member = self._gen_player_info("human", name, uuid=uuid)
        self.members.append(member)

    def find_member_by_uuid(self, uuid):
        target = [m for m in self.members if m['type'] == 'human' and m['uuid'] == uuid]
        return target[0] if len(target)==1 else None

    def remove_member(self, member):
        assert member in self.members
        self.members.remove(member)

    def setup_engine(self):
        self.engine = MP.MessageProcessor()
        uuid_list, name_list = [], []
        for idx, member in enumerate(self.members):
            uuid = str(idx) if member['type'] == "ai" else member['uuid']
            name = member['name']
            uuid_list.append(uuid)
            name_list.append(name)
            if member['type'] == "ai":
                self.ai_players[uuid] = self._setup_ai_player(member['setup_script_path'])
        self.players_info = MP.gen_players_info(uuid_list, name_list)
        self.engine_config = MP.gen_game_config(
                self.rule['max_round'],
                self.rule['initial_stack'],
                self.rule['small_blind'],
                self.rule['ante'],
                self.rule['blind_structure']
        )

    def _setup_ai_player(self, setup_script_path):
        if not ai_generator.healthcheck(setup_script_path, quiet=True):
            raise Exception("Failed to setup ai from [ %s ]" % setup_script_path)
        setup_method = ai_generator._import_setup_method(setup_script_path)
        return setup_method()

    def start_game(self):
        assert self.engine and self.engine_config and self.players_info
        self.latest_messages = self.engine.start_game(self.players_info, self.engine_config)
        if not self._has_game_finished(self.latest_messages):
            self.next_player_uuid = self._fetch_next_player_uuid(self.latest_messages)

    def update_game(self, action, amount):
        assert len(self.latest_messages) != 0  # check that start_game has already called
        self.latest_messages = self.engine.update_game(action, amount)
        if not self._has_game_finished(self.latest_messages):
            self.next_player_uuid = self._fetch_next_player_uuid(self.latest_messages)

    def ask_action_to_ai(self, uuid):
        ai_player = self.ai_players[uuid]
        ask_uuid, ask_message = self.latest_messages[-1]
        assert ask_message['type'] == 'ask' and uuid == ask_uuid
        return ai_player.declare_action(
                ask_message['message']['valid_actions'],
                ask_message['message']['hole_card'],
                ask_message['message']['round_state']
        )

    def _has_game_finished(self, new_messages):
        _uuid, last_message = new_messages[-1]
        return "game_result_message" == last_message['message']['message_type']

    def _fetch_next_player_uuid(self, new_messages):
        ask_uuid, ask_message = new_messages[-1]
        assert ask_message['type'] == 'ask'
        return ask_uuid

    def _gen_player_info(self, player_type, name, setup_script_path=None, uuid=None):
        info = { 'type': player_type, 'name': name }
        if 'ai' == player_type:
            assert setup_script_path
            info['setup_script_path'] = setup_script_path
        elif 'human' == player_type:
            assert uuid
            info['uuid'] = uuid
        else:
            raise Exception("Unexpected player type [ %s ] is passed" % player_type)
        return info

global_game_config = GameConfig()

path = "/Users/kota/development/PyPokerGUIEnv/PyPokerGUI/pypokergui/ttt.py"
sample_game_config = {
        'max_round': 10,
        'initial_stack': 100,
        'small_blind': 10,
        'ante': 5,
        'blind_structure': None,
        'ai_players': [
            { 'name': "ai1", "path": path },
            { 'name': "ai2", "path": path },
            { 'name': "ai3", "path": path },
        ]
}

def setup_config(config):
    global_game_config.define_rule(
            config['max_round'], config['initial_stack'], config['small_blind'],
            config['ante'], config['blind_structure']
    )
    for player in config['ai_players']:
        global_game_config.append_ai_player(player['name'], player['path'])

def main():
    tornado.options.parse_command_line()
    config = sample_game_config  # TODO parse config file into hash
    setup_config(config)
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()

