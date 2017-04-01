#!/usr/bin/env python

import os
import sys

# Resolve path configuration
root = os.path.join(os.path.dirname(__file__), "..")
src = os.path.join(root, "pypokergui")
sys.path.append(root)
sys.path.append(src)

import click
import webbrowser

from pypokergui.server.poker import start_server
from pypokergui.config_builder import build_config

@click.group()
def cli():
    pass

@cli.command(name="serve")
@click.argument("config")
@click.option("--port", default=8000, help="port to run server")
@click.option("--speed", default="moderate", type=click.Choice(["moderate", "fast"]), help="how fast game progress")
def serve_command(config, port, speed):
    host = "localhost"
    webbrowser.open("http://%s:%s" % (host, port))
    start_server(config, port, speed)

@cli.command(name="build_config")
@click.option("-r", "--maxround", default=10, help="final round of the game")
@click.option("-s", "--stack", default=100, help="start stack of player")
@click.option("-b", "--small_blind", default=5, help="amount of small blind")
@click.option("-a", "--ante", default=0, help="amount of ante")
def build_config_command(maxround, stack, small_blind, ante):
    build_config(maxround, stack, small_blind, ante, None)


if __name__ == '__main__':
    cli()
