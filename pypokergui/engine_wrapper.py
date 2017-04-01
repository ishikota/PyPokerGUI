from collections import OrderedDict

from pypokerengine.engine.table import Table
from pypokerengine.engine.player import Player
from pypokerengine.engine.round_manager import RoundManager
from pypokerengine.engine.message_builder import MessageBuilder
from pypokerengine.engine.poker_constants import PokerConstants as Const

class EngineWrapper(object):

    def start_game(self, players_info, game_config):
        self.config = game_config
        # setup table
        table = Table()
        for uuid, name in players_info.items():
            player = Player(uuid, game_config['initial_stack'], name)
            table.seats.sitdown(player)
        # start the first round
        state, msgs = self._start_new_round(1, game_config['blind_structure'], table)
        self.current_state = state
        return _parse_broadcast_destination(msgs, self.current_state['table'])

    def update_game(self, action, bet_amount):
        state, msgs = RoundManager.apply_action(self.current_state, action, bet_amount)
        if state['street'] == Const.Street.FINISHED:
            state, new_msgs = self._start_next_round(
                    state['round_count']+1, self.config['blind_structure'], state['table'])
            msgs += new_msgs
        self.current_state = state
        return _parse_broadcast_destination(msgs, self.current_state['table'])

    def _start_new_round(self, round_count, blind_structure, table):
        # adjust btn position to put btn of player-0 after table.shift_dealer_btn()
        # which will be called in self._start_next_round(...)
        table.dealer_btn = len(table.seats.players)-1
        return self._start_next_round(round_count, blind_structure, table)

    def _start_next_round(self, round_count, blind_structure, table):
        table.shift_dealer_btn()
        small_blind, ante = _get_forced_bet_amount(round_count, blind_structure)
        table = _exclude_short_of_money_players(table, ante, small_blind)
        if self._has_game_finished(round_count, table, self.config['max_round']):
            finished_state = { 'table': table }
            game_result_msg = _gen_game_result_message(table, self.config)
            msgs = _parse_broadcast_destination([game_result_msg], table)
            return finished_state, msgs
        else:
            return RoundManager.start_new_round(round_count, small_blind, ante, table)

    def _has_game_finished(self, round_count, table, max_round):
        is_final_round = round_count == max_round
        is_winner_decided = len([1 for p in table.seats.players if p.stack!=0])==1
        return is_final_round or is_winner_decided


def gen_players_info(uuid_list, name_list):
    assert len(uuid_list) == len(name_list)
    return OrderedDict(zip(uuid_list, name_list))

def gen_game_config(max_round, initial_stack, small_blind, ante, blind_structure=None):
    assert max_round > 0
    assert initial_stack > 0
    assert small_blind > 0
    assert ante >= 0
    if not blind_structure:
        blind_structure = { 1 : { 'small_blind': small_blind, 'ante': ante } }
    if not 1 in blind_structure:
        blind_structure[1] = { 'small_blind': small_blind, 'ante': ante }
    return {
            'max_round': max_round,
            'initial_stack': initial_stack,
            'small_blind': small_blind,
            'ante': ante,
            'blind_structure': blind_structure
            }

def _get_forced_bet_amount(round_count, blind_structure):
    level_thresholds = sorted(blind_structure.keys())
    current_level_pos = [r <= round_count for r in level_thresholds].count(True)-1
    assert current_level_pos >= 0
    current_level_key = level_thresholds[current_level_pos]
    current_structure = blind_structure[current_level_key]
    return current_structure['small_blind'], current_structure['ante']

def _exclude_short_of_money_players(table, ante, sb_amount):
    sb_pos, bb_pos = _steal_money_from_poor_player(table, ante, sb_amount)
    _disable_no_money_player(table.seats.players)
    table.set_blind_pos(sb_pos, bb_pos)
    if table.seats.players[table.dealer_btn].stack == 0: table.shift_dealer_btn()
    return table

def _steal_money_from_poor_player(table, ante, sb_amount):
    players = table.seats.players
    # exclude player who cannot pay ante
    for player in [p for p in players if p.stack < ante]: player.stack = 0
    if players[table.dealer_btn].stack == 0: table.shift_dealer_btn()

    search_targets = players + players + players
    search_targets = search_targets[table.dealer_btn+1:table.dealer_btn+1+len(players)]
    # exclude player who cannot pay small blind
    sb_player = _find_first_elligible_player(search_targets, sb_amount + ante)
    sb_relative_pos = search_targets.index(sb_player)
    for player in search_targets[:sb_relative_pos]: player.stack = 0
    # exclude player who cannot pay big blind
    search_targets = search_targets[sb_relative_pos+1:sb_relative_pos+len(players)]
    bb_player = _find_first_elligible_player(search_targets, sb_amount*2 + ante, sb_player)
    if sb_player == bb_player:  # no one can pay big blind. So steal money from all players except small blind
        for player in [p for p in players if p!=bb_player]: player.stack = 0
    else:
        bb_relative_pos = search_targets.index(bb_player)
        for player in search_targets[:bb_relative_pos]: player.stack = 0
    return players.index(sb_player), players.index(bb_player)


def _find_first_elligible_player(players, need_amount, default=None):
    if default: return next((player for player in players if player.stack >= need_amount), default)
    return next((player for player in players if player.stack >= need_amount))

def _disable_no_money_player(players):
    no_money_players = [player for player in players if player.stack == 0]
    for player in no_money_players:
        player.pay_info.update_to_fold()

def _parse_broadcast_destination(messages, table):
    uuid_list = [player.uuid for player in table.seats.players]
    parsed_msgs = []
    for message in messages:
        parsed_msgs.append(message)
        #if -1 == message[0]:  # -1 destination indicates broadcast
        #    message = [(uuid, message[1]) for uuid in uuid_list]
        #    parsed_msgs += message
        #else:
        #    parsed_msgs.append(message)
    return parsed_msgs

def _gen_game_result_message(table, config):
    compat_config = {
            'initial_stack': config['initial_stack'],
            'max_round': config['max_round'],
            'small_blind_amount': config['small_blind'],  # fill an interface gap
            'ante': config['ante'],
            'blind_structure': config['blind_structure']
            }
    msg = MessageBuilder.build_game_result_message(compat_config, table.seats)
    destination = -1
    return (destination, msg)

