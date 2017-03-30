#!/usr/bin/env python

import os
import sys

import click

# Resolve path configuration
root = os.path.join(os.path.dirname(__file__), "..")
src = os.path.join(root, "pypokergui")
sys.path.append(root)
sys.path.append(src)

from pypokergui.server.poker import start_server

@click.group()
def cli():
    pass

@cli.command(name="serve")
@click.argument("config")
@click.option("--port", default=8888, help="port to run server")
def serve_command(config, port):
    start_server(config, port)

if __name__ == '__main__':
    cli()
