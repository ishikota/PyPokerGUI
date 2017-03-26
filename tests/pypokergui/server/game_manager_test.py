import os

from tests.base_unittest import BaseUnitTest
from tests.pypokergui.server.sample_ai_setup_script import FishPlayer

from pypokergui.server.game_manager import GameManager

class GameManagerTest(BaseUnitTest):

    def setUp(self):
        self.GM = GameManager()

    def test_define_rule(self):
        self.GM.define_rule(1, 2, 3, 4, None)
        self.eq(self.GM.rule["max_round"], 1)
        self.eq(self.GM.rule["initial_stack"], 2)
        self.eq(self.GM.rule["small_blind"], 3)
        self.eq(self.GM.rule["ante"], 4)
        self.eq(self.GM.rule["blind_structure"], {1: {"small_blind": 3, "ante":4}})

    def test_join_ai_player(self):
        self.GM.join_ai_player("hoge", "fuga")
        expected = [{ "type": "ai", "uuid":'0', "name": "hoge", "setup_script_path": "fuga" }]
        self.eq(expected, self.GM.members_info)

    def test_join_human_player(self):
        self.GM.join_human_player("hoge", "fuga")
        expected = [{ "type": "human", "name": "hoge", "uuid": "fuga" }]
        self.eq(expected, self.GM.members_info)

    def test_get_human_player_info(self):
        self.GM.join_ai_player("hoge", "fuga")
        self.assertIsNone(self.GM.get_human_player_info("fuga"))
        self.GM.join_human_player("boo", "bar")
        self.assertIsNotNone(self.GM.get_human_player_info("bar"))

    def test_remove_human_player_info(self):
        self.GM.join_human_player("boo", "bar")
        self.GM.remove_human_player_info("bar")
        self.assertIsNone(self.GM.get_human_player_info("bar"))

    def test_start_game_build_ai_players(self):
        self.GM.define_rule(10, 100, 10, 5, None)
        self.GM.join_ai_player("hoge", ai_setup_script_path)
        self.GM.join_human_player("boo", "bar")
        self.GM.start_game()
        self.eq(self.GM.ai_players['0'].__class__.__name__, FishPlayer.__name__)

    def test_start_game(self):
        self.GM.define_rule(10, 100, 10, 5, None)
        self.GM.join_ai_player("hoge", ai_setup_script_path)
        self.GM.join_ai_player("fuga", ai_setup_script_path)
        self.GM.start_game()
        self.assertGreaterEqual(self.GM.latest_messages, 1)
        self.true(self.GM.is_playing_poker)
        self.eq('1', self.GM.next_player_uuid)

    def test_update_game(self):
        self.GM.define_rule(10, 100, 10, 5, None)
        self.GM.join_ai_player("hoge", ai_setup_script_path)
        self.GM.join_ai_player("fuga", ai_setup_script_path)
        self.GM.join_ai_player("bar", ai_setup_script_path)
        self.GM.start_game()
        self.eq('0', self.GM.next_player_uuid)
        self.GM.update_game("fold", 0)
        self.eq('1', self.GM.next_player_uuid)
        self.GM.update_game("raise", 30)
        self.eq('2', self.GM.next_player_uuid)

    def test_ask_action_to_ai_player(self):
        self.GM.define_rule(10, 100, 10, 5, None)
        self.GM.join_ai_player("hoge", ai_setup_script_path)
        self.GM.join_ai_player("fuga", ai_setup_script_path)
        self.GM.join_ai_player("bar", ai_setup_script_path)
        self.GM.start_game()
        action, amount = self.GM.ask_action_to_ai_player(self.GM.next_player_uuid)
        self.eq("call", action)
        self.eq(20, amount)

ai_setup_script_path = os.path.join(os.path.dirname(__file__), "sample_ai_setup_script.py")
