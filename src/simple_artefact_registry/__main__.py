'''
##########################################################################
:mod:`simple_artefact_registry.__main__` - Simple Artefact Registry Server
##########################################################################

To run the Simple Artefact Registry Server use

.. code-block:: commandline

   python -m simple_artefact_registry [OPTIONS]

The following options are available:

* ``-c`` ``--config``: The configuration file to load. Defaults to "sar.yaml"
* ``-p`` ``--port``: The port to listen on. Defaults to 8080
* ``--host``: The host to listen on. Defaults to 0.0.0.0
'''
from argparse import ArgumentParser
from yaml import load

from . import run_server

parser = ArgumentParser(description='Simple Artefact Registry Server')
parser.add_argument('-c', '--config', dest='config', default='sar.yaml', help='Configuration file to use [sar.yaml]')
parser.add_argument('-p', '--port', dest='port', default=None, type=int, help='Override the port set in the configuration')
parser.add_argument('--host', dest='host', default=None, type=int, help='Override the host set in the configuration')
args = parser.parse_args()

with open(args.config) as conf:
    config = load(conf)

if args.port is not None:
    if 'server' in config:
        config['server']['port'] = args.port
    else:
        config['server'] = {'port': args.port}
if args.host is not None:
    if 'server' in config:
        config['server']['host'] = args.host
    else:
        config['server'] = {'host': args.host}

run_server(config)
