# PyPokerGUI

[![Build Status](https://travis-ci.org/ishikota/PyPokerGUI.svg?branch=master)](https://travis-ci.org/ishikota/PyPokerGUI)
[![PyPI](https://img.shields.io/pypi/v/PyPokerGUI.svg?maxAge=2592000)](https://badge.fury.io/py/PyPokerGUI)
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](https://github.com/ishikota/PyPokerGUI/blob/master/LICENSE.md)

GUI application for [PyPokerEngine](https://github.com/ishikota/PyPokerEngine).  
You can play poker with your AI bia browser.

![app_demo](https://github.com/ishikota/PyPokerGUI/blob/release/screenshot/poker_demo.gif)

This library assumes that your AI is implemented in [PyPokerEngine](https://github.com/ishikota/PyPokerEngine) format.  
If you have not checked our [PyPokerEngine](https://github.com/ishikota/PyPokerEngine), we recommend you to check it first.

- [README tutorial](https://github.com/ishikota/PyPokerEngine)
- [doc site for PyPokerEngine](https://ishikota.github.io/PyPokerEngine/)

# Tutorial
In this tutorial, we will play poker with simple AI "*FishPlayer*".  
("*FishPlayer*" is an AI always declares CALL action. )

The outline of this tutorial is following.

1. Create script to setup our AI
2. Setup config file which defines rule of the game
3. Start the server with config file and play the game

## Installation
Please install this library with pip.

```bash
pip install pypokergui
```

## Create script to setup our AI
First, we will create a script which defines how to setup our AI.  
What you need to do is implementing `setup_ai` method.    
PyPokerGUI uses this method to setup your AI.

```python
from pypokerengine.players import BasePokerPlayer

class FishPlayer(BasePokerPlayer):  # Do not forget to make parent class as "BasePokerPlayer"

    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        call_action_info = valid_actions[1]
        action, amount = call_action_info["action"], call_action_info["amount"]
        return action, amount   # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return FishPlayer()
```

We assume that you put this script on `/Users/ishikota/poker/fish_player_setup.py` in following section.

## Setup config file which defines rule of the game
Next we will define the rule of the game.  
We need to define following settings in yaml format.

- **max_round** : how many round we will play
- **initial stack** : start stack size of each player
- **small blind** : the amount of small blind
- **ante** : the amount of ante
- **ai_players** : path to your AI-setup script

You can generate template of config file like this.

```bash
pypokergui build_config --maxround 10 --stack 100 --small_blind 10 --ante 0 >> poker_conf.yaml
```

Then your `poker_conf.yaml` would be ...

```yaml
ante: 0
blind_structure: null
initial_stack: 100
max_round: 10
small_blind: 10
ai_players:
- name: FIXME:your-ai-name
  path: FIXME:your-setup-script-path
```

We replace `ai_players` items like this.

```yaml
ante: 0
blind_structure: null
initial_stack: 100
max_round: 10
small_blind: 10
ai_players:
- name: fish_player_1
  path: /Users/ishikota/poker/fish_player_setup.py
- name: fish_player_2
  path: /Users/ishikota/poker/fish_player_setup.py
```

We assume that you put this file on `/Users/ishikota/poker/poker_conf.yaml` in following section.

## Start the server with config file and play the game
Ok, everything is ready. We start the local server with our config file.

```bash
pypokergui serve /Users/ishikota/poker/poker_conf.yaml
```

Then browser will be opened and you would see registration page.  
Please register yourself in the page and start the game. Enjoy poker!!

### How to registrate yourself
<img src="https://github.com/ishikota/PyPokerGUI/blob/release/screenshot/poker_registration.png" width=600px/>

### How to declare action in the game
<img src="https://github.com/ishikota/PyPokerGUI/blob/release/screenshot/poker_game.png" width=600px/>

