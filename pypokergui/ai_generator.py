import os
import sys
import importlib

from pypokerengine.players import BasePokerPlayer

"""Assert passed script satisfies requirements for PyPokerGUI
    ai-generator script must implement "setup_ai()" method which
    returns child instance of pypokerengine.players.BasePokerPlayer.
"""
def healthcheck(script_path, quiet=False):
    status = True

    # Assertion-1. check if setup_ai method is implemented
    try:
        setup_method = _import_setup_method(script_path)
    except Exception as e:
        if not quiet: print('"setup_ai" method was not found in [ %s ].(Exception=%s)' % (script_path, e.message))
        status = False

    # Assertion-2. check if "setup_ai" method works
    try:
        if status: player = setup_method()
    except Exception as e:
        if not quiet: print('Exception [ %s ] was raised when your "setup_ai" method invoked' % e.message)
        status = False

    # Assertion-3. check if generated player is instance of BasePokerPlayer
    if status and not isinstance(player, BasePokerPlayer):
        if not quiet: print("Generated player is not instance of [ BasePokerPlayer ] but of [ %s ]" % type(player).__name__)
        status = False

    if status and not quiet: print("health check succeeded for script of [ %s ]" % script_path)
    return status

def _import_setup_method(script_path):
    dirname = os.path.dirname(script_path)
    filename = os.path.basename(script_path)
    sys.path.append(dirname)
    m = importlib.import_module(os.path.splitext(filename)[0])
    return m.setup_ai

