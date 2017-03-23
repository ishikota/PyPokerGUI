from pypokerengine.engine.card import Card
from pypokerengine.engine.deck import Deck
from tests.base_unittest import BaseUnitTest

import pypokergui.engine_wrapper as Engine

class EngineWrapperTest(BaseUnitTest):

    def test_start_game(self):
        uuid_list = ["hoge", "fuga", "boo"]
        name_list = ["HOGE", "FUGA", "BOO"]
        players_info = Engine.gen_players_info(uuid_list, name_list)
        game_config = Engine.gen_game_config(5, 100, 10, 1)

        engine = Engine.EngineWrapper()
        original_msgs = engine.start_game(players_info, game_config)
        hoge_msg, fuga_msg, boo_msg = [_simplify_messages(msgs) for msgs in _classify_messages_by_destination(original_msgs, uuid_list)]
        self.eq([MSG_RS, MSG_SS, MSG_AK], hoge_msg)
        self.eq([MSG_RS, MSG_SS], fuga_msg)
        self.eq([MSG_RS, MSG_SS], boo_msg)

    def test_update_game(self):
        uuid_list = ["hoge", "fuga", "boo"]
        name_list = ["HOGE", "FUGA", "BOO"]
        players_info = Engine.gen_players_info(uuid_list, name_list)
        game_config = Engine.gen_game_config(5, 100, 10, 1)

        engine = Engine.EngineWrapper()
        engine.start_game(players_info, game_config)
        original_msgs = engine.update_game("call", 10)
        hoge_msg, fuga_msg, boo_msg = [_simplify_messages(msgs) for msgs in _classify_messages_by_destination(original_msgs, uuid_list)]
        self.eq([MSG_GU], hoge_msg)
        self.eq([MSG_GU, MSG_AK], fuga_msg)
        self.eq([MSG_GU], boo_msg)

    def test_update_game_when_round_finished(self):
        uuid_list = ["hoge", "fuga", "boo"]
        name_list = ["HOGE", "FUGA", "BOO"]
        players_info = Engine.gen_players_info(uuid_list, name_list)
        game_config = Engine.gen_game_config(5, 100, 10, 1)

        engine = Engine.EngineWrapper()
        engine.start_game(players_info, game_config)
        engine.update_game("fold", 0)
        original_msgs = engine.update_game("fold", 0)
        hoge_msg, fuga_msg, boo_msg = [_simplify_messages(msgs) for msgs in _classify_messages_by_destination(original_msgs, uuid_list)]
        self.eq([MSG_GU, MSG_RF, MSG_RS, MSG_SS], hoge_msg)
        self.eq([MSG_GU, MSG_RF, MSG_RS, MSG_SS, MSG_AK], fuga_msg)
        self.eq([MSG_GU, MSG_RF, MSG_RS, MSG_SS], boo_msg)

    def test_update_game_when_game_finished(self):
        uuid_list = ["hoge", "fuga", "boo"]
        name_list = ["HOGE", "FUGA", "BOO"]
        players_info = Engine.gen_players_info(uuid_list, name_list)
        game_config = Engine.gen_game_config(5, 100, 10, 1)

        engine = Engine.EngineWrapper()
        engine.start_game(players_info, game_config)

        # Fix cards used in the game to make game result deterministic
        engine.current_state['table'].deck = Deck(cheat=True, cheat_card_ids=range(6, 11))
        for idx, player in enumerate(engine.current_state['table'].seats.players):
            player.hole_card = [Card.from_id(idx*2), Card.from_id(idx*2+1)]

        engine.update_game("raise", 99)
        engine.update_game("call", 99)
        original_msgs = engine.update_game("call", 99)
        hoge_msg, fuga_msg, boo_msg = [_simplify_messages(msgs) for msgs in _classify_messages_by_destination(original_msgs, uuid_list)]
        self.eq([MSG_GU, MSG_SS, MSG_SS, MSG_SS, MSG_RF, MSG_GF], hoge_msg)
        self.eq([MSG_GU, MSG_SS, MSG_SS, MSG_SS, MSG_RF, MSG_GF], fuga_msg)
        self.eq([MSG_GU, MSG_SS, MSG_SS, MSG_SS, MSG_RF, MSG_GF], boo_msg)

    def test_gen_players_info(self):
        uuid_list = ["hoge", "fuga", "boo"]
        name_list = ["HOGE", "FUGA", "BOO"]
        players_info = Engine.gen_players_info(uuid_list, name_list)
        for idx, (uuid, name) in enumerate(players_info.items()):
            self.eq(uuid_list[idx], uuid)
            self.eq(name_list[idx], name)

    def test_gen_game_config(self):
        config = Engine.gen_game_config(5, 100, 10, 1)
        self.eq(5, config['max_round'])
        self.eq(100, config['initial_stack'])
        self.eq(10, config['small_blind'])
        self.eq(1, config['ante'])
        self.eq(1, config['blind_structure'][1]['ante'])

    def test_gen_game_config_with_blind_structure(self):
        config = Engine.gen_game_config(5, 100, 10, 1, blind_structure)
        self.eq(1, config['blind_structure'][1]['ante'])
        self.eq(5, config['blind_structure'][2]['ante'])

    def test_get_forced_bet_amount(self):
        self.eq((10, 1), Engine._get_forced_bet_amount(1, blind_structure))
        self.eq((20, 5), Engine._get_forced_bet_amount(2, blind_structure))
        self.eq((30, 10), Engine._get_forced_bet_amount(3, blind_structure))
        self.eq((30, 10), Engine._get_forced_bet_amount(4, blind_structure))
        self.eq((50, 20), Engine._get_forced_bet_amount(5, blind_structure))

blind_structure = {
        2 : { 'small_blind': 20, 'ante': 5 },
        3 : { 'small_blind': 30, 'ante': 10 },
        5 : { 'small_blind': 50, 'ante': 20 }
        }

MSG_RS = 'round_start_message'
MSG_SS = 'street_start_message'
MSG_AK = 'ask_message'
MSG_GU = 'game_update_message'
MSG_RF = 'round_result_message'
MSG_GF = 'game_result_message'

def _classify_messages_by_destination(messages, uuid_list):
    dests = [[] for i in range(len(uuid_list))]
    for msg in messages:
        if -1 == msg[0]:
            #self.fail("message destination should be uuid: message => %s" % str(msg))
            for dest in dests:
                dest.append(msg)
        else:
            dests[uuid_list.index(msg[0])].append(msg)
    return dests

def _simplify_messages(msgs):
    return [msg[1]['message']['message_type'] for msg in msgs]

