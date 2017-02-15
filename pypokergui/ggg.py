import os
import sys

root = "/Users/kota/development/PyPokerAIEnv/PyPokerAI"
src_path = os.path.join(root, "pypokerai")
sys.path.append(root)
sys.path.append(src_path)

from pypokerengine.players import BasePokerPlayer
from pypokerai.player import PokerPlayer
from pypokerai.task import TexasHoldemTask, blind_structure
from pypokerai.value_function import MLPOneLayerScaledScalarFeaturesValueFunction
from kyoka.value_function import BaseApproxActionValueFunction


WEIGHT_PATH = "/Users/kota/development/PyPokerGUIEnv/PyPokerGUI/pypokergui/base_line_player"

class ValueFuncWrapper(BaseApproxActionValueFunction):

    def setup(self):
        self.delegate = MLPOneLayerScaledScalarFeaturesValueFunction(128, blind_structure)
        self.delegate.setup()
        self.delegate.load(WEIGHT_PATH)

    def construct_features(self, state, action):
        return self.delegate.construct_features(state, action)

    def approx_predict_value(self, features):
        return self.delegate.approx_predict_value(features)

class PlayerWrapper(BasePokerPlayer):

    def set_uuid(self, uuid):
        self.uuid = uuid
        self.delegate.uuid = uuid

    def declare_action(self, valid_actions, hole_card, round_state):
        name = [p['name'] for p in round_state['seats'] if p['uuid'] == self.uuid]
        print "player [ %s ] has hole_card [ %s ]" % (name, hole_card)
        return self.delegate.declare_action(valid_actions, hole_card, round_state)

    def receive_game_start_message(self, game_info):
        self.delegate.receive_game_start_message(game_info)

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.delegate.receive_round_start_message(round_count, hole_card, seats)

    def receive_street_start_message(self, street, round_state):
        self.delegate.receive_street_start_message(street, round_state)

    def receive_game_update_message(self, action, round_state):
        self.delegate.receive_game_update_message(action, round_state)

    def receive_round_result_message(self, winners, hand_info, round_state):
        self.delegate.receive_round_result_message(winners, hand_info, round_state)

def setup_ai():
    task = TexasHoldemTask(scale_reward=True, shuffle_position=True, action_record=True)
    value_func = ValueFuncWrapper()
    value_func.setup()
    delegate = PokerPlayer(task, value_func, debug=False)
    player = PlayerWrapper()
    player.delegate = delegate
    return player

