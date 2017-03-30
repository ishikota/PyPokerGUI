import yaml

def build_config(max_round=None, initial_stack=None, small_blind=None, ante=None, blind_structure=None):
    config = {
            "max_round": max_round,
            "initial_stack": initial_stack,
            "small_blind": small_blind,
            "ante": ante,
            "blind_structure": blind_structure,
            "ai_players": [
                { "name": "FIXME:your-ai-name", "path": "FIXME:your-setup-script-path" },
            ]
            }
    print(yaml.dump(config, default_flow_style=False))

