import os
from mock import Mock
from mock import patch

from tests.base_unittest import BaseUnitTest

from pypokergui.server.game_manager import GameManager
import pypokergui.server.message_manager as MM

class MessageManagerTest(BaseUnitTest):

    def test_broadcast_config_update(self):
        uuids = ["hoge", "fuga"]
        sockets = [gen_mock_socket(uuid) for uuid in uuids]
        with patch(
                'pypokergui.server.message_manager._gen_config_update_message',
                side_effect=lambda x, uuid: "config_update:%s" % uuid):
            MM.broadcast_config_update(GameManager(), sockets)
        for soc, uuid in zip(sockets, uuids):
            expected = "config_update:%s" % uuid
            self.eq(expected, soc.write_message.call_args_list[0][0][0])

    def test_broadcast_start_game(self):
        uuids = ["hoge", "fuga"]
        sockets = [gen_mock_socket(uuid) for uuid in uuids]
        gm = setup_game_manager(uuids)
        with patch(
                'pypokergui.server.message_manager._gen_start_game_message',
                side_effect=lambda x, uuid: "start_game:%s" % uuid):
            MM.broadcast_start_game(gm, sockets)
        for soc, uuid in zip(sockets, uuids):
            expected = "start_game:%s" % uuid
            self.eq(expected, soc.write_message.call_args_list[0][0][0])
        for uuid, player in gm.ai_players.items():
            self.eq(uuid, player.uuid)

    def test_broadcast_update_game(self):
        uuids = ["hoge", "fuga"]
        sockets = [gen_mock_socket(uuid) for uuid in uuids]
        gm = setup_game_manager(uuids)
        gm.ai_players.values()[0].debug_message = None
        gm.update_game("fold", 0)
        with patch(
                'pypokergui.server.message_manager._gen_game_update_message',
                return_value="update_game"),\
            patch(
                'pypokergui.server.message_manager._broadcast_message_to_ai',
                side_effect=self._append_log_on_player):
            MM.broadcast_update_game(gm, sockets, update_interval=0)
        for soc, uuid in zip(sockets, uuids):
            expected = "update_game"
            self.eq(expected, soc.write_message.call_args_list[0][0][0])
        for player in gm.ai_players.values():
            self.assertIsNotNone(player.debug_message)

    def _append_log_on_player(self, player, message):
        player.debug_message = message

ai_setup_script_path = os.path.join(os.path.dirname(__file__), "sample_ai_setup_script.py")

def gen_mock_socket(uuid):
    soc = Mock()
    soc.uuid = uuid
    return soc

def setup_game_manager(uuids):
    gm = GameManager()
    gm.define_rule(10, 100, 10, 5, None)
    for uuid in uuids:
        gm.join_human_player("name", uuid)
    gm.join_ai_player("ai", ai_setup_script_path)
    gm.start_game()
    return gm

def find_socket_by_uuid(sockets, uuid):
    for soc in sockets:
        if soc.uuid == uuid:
            return soc
