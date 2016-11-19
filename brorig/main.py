#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import signal
import sys

import pkg_resources

import brorig.config as config
import brorig.log as log
import brorig.web_server as webserver
import brorig.custom as custom


def signal_handler(signal, frame):
    log.info('Stopping...')
    webserver.stop()
    sys.exit(0)


def parse_options(argument_string=None):
    """Parse user-provided options"""
    import argparse

    try:
        version = "%(prog)s " + str(pkg_resources.get_distribution("main.py").version)
    except pkg_resources.DistributionNotFound:
        version = "dev"

    descr = "Asterisk Callflow Debugger (" + version + ")"

    parser = argparse.ArgumentParser(description=descr,
                                     epilog="To install a new configuration file, use the option -i.")

    parser.add_argument("--verbosity", "-v", default=0, action="count", help="Increase the debug verbosity")
    parser.add_argument('--version', action='version', version=version)

    parser.add_argument('--port', '-p', type=int, default=4242, help="Port where web server will listen (default 4242)")
    parser.add_argument('--config', '-c', type=str, required=True, help="Configuration file path")
    parser.add_argument('--install', '-i', help="Generate configuration file", action="store_true")

    if argument_string:
        arguments = parser.parse_args(argument_string.split())
    else:
        # from command line arguments
        arguments = parser.parse_args()
    return arguments


def setup():
    args = parse_options()
    if args.install:
        config.gen_template(args.config)
        exit()
    signal.signal(signal.SIGINT, signal_handler)
    config.load(args.config)
    log.init(args.verbosity)
    custom.load()
    webserver.start_server(args.port)


if __name__ == "__main__":
    setup()
