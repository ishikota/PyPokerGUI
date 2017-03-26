import time
import logging

import tornado.escape


def broadcast_config_update(handler, game_manager, sockets):
    for soc in sockets:
        try:
            soc.write_message(_gen_config_update_message(handler, game_manager, soc.uuid))
        except:
            logging.error("Error sending message", exc_info=True)

def _gen_config_update_message(handler, game_manager, uuid):
    registered = game_manager.get_human_player_info(uuid)
    html_str = handler.render_string(
            "game_config.html", config=game_manager, registered=registered)
    html = tornado.escape.to_basestring(html_str)

    return {
            'message_type': 'config_update',
            'html': html,
            'registered': registered
            }

def broadcast_start_game(handler, game_manager, sockets):
    # broadcast message to browser bia sockets
    for soc in sockets:
        try:
            soc.write_message(_gen_start_game_message(handler, game_manager, soc.uuid))
        except:
            logging.error("Error sending message", exc_info=True)
    # broadcast message to ai by invoking proper callback method
    # FIXME TMP SOLUTION to broadcast game_start_message to ai
    dummy_game_info = game_manager.latest_messages[0][1]['message']
    for uuid, player in game_manager.ai_players.items():
        player.receive_game_start_message(dummy_game_info)
        player.set_uuid(uuid)

def _gen_start_game_message(handler, game_manager, uuid):
    registered = game_manager.get_human_player_info(uuid)
    html_str = handler.render_string(
            "poker_game.html", config=game_manager, registered=registered)
    html = tornado.escape.to_basestring(html_str)

    return {
            'message_type': 'start_game',
            'html': html
            }

def broadcast_update_game(handler, game_manager, sockets, update_interval=0):
    for destination, update in game_manager.latest_messages:
        for uuid in _parse_destination(destination, game_manager, sockets):
            if len(str(uuid)) <= 2:
                ai_player = game_manager.ai_players[uuid]
                _broadcast_message_to_ai(ai_player, update)
            else:
                socket = _find_socket_by_uuid(sockets, uuid)
                message = _gen_game_update_message(handler, update)
                try:
                    socket.write_message(message)
                except:
                    logging.error("Error sending message", exc_info=True)
        time.sleep(update_interval)

def _parse_destination(destination, game_manager, sockets):
    if destination == -1:
        return [soc.uuid for soc in sockets] + game_manager.ai_players.keys()
    else:
        return [destination]

def _find_socket_by_uuid(sockets, uuid):
    target = [sock for sock in sockets if sock.uuid == uuid]
    assert len(target) == 1
    return target[0]

def _gen_game_update_message(handler, message):
    message_type = message['message']['message_type']
    if 'round_start_message' == message_type:
        round_count = message['message']['round_count']
        hole_card = message['message']['hole_card']
        event_html_str = handler.render_string("event_round_start.html",
                round_count=round_count, hole_card=hole_card)
        content = {
                'update_type': message_type,
                'event_html': tornado.escape.to_basestring(event_html_str)
                }
    elif 'street_start_message' == message_type:
        round_state = message['message']['round_state']
        street = message['message']['street']
        table_html_str = handler.render_string("round_state.html", round_state=round_state)
        event_html_str = handler.render_string("event_street_start.html", street=street)
        content = {
                'update_type': message_type,
                'table_html': tornado.escape.to_basestring(table_html_str),
                'event_html': tornado.escape.to_basestring(event_html_str)
                }
    elif 'game_update_message' == message_type:
        round_state = message['message']['round_state']
        action = message['message']['action']
        action_histories = message['message']['action_histories']
        table_html_str = handler.render_string("round_state.html", round_state=round_state)
        event_html_str = handler.render_string(
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
        table_html_str = handler.render_string("round_state.html", round_state=round_state)
        event_html_str = handler.render_string("event_round_result.html",
                round_state=round_state, hand_info=hand_info, winners=winners, round_count=round_count)
        content = {
                'update_type': message_type,
                'table_html': tornado.escape.to_basestring(table_html_str),
                'event_html': tornado.escape.to_basestring(event_html_str)
                }
    elif 'game_result_message' == message_type:
        game_info = message['message']['game_information']
        event_html_str = handler.render_string("event_game_result.html", game_information=game_info)
        content = {
                'update_type': message_type,
                'event_html' : tornado.escape.to_basestring(event_html_str)
                }
    elif 'ask_message' == message_type:
        round_state = message['message']['round_state']
        hole_card = message['message']['hole_card']
        valid_actions = message['message']['valid_actions']
        action_histories = message['message']['action_histories']
        table_html_str = handler.render_string("round_state.html", round_state=round_state)
        event_html_str = handler.render_string("event_ask_action.html",
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

def _broadcast_message_to_ai(ai_player, message):
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

