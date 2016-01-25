#!/usr/bin/env python
# coding: utf-8

import config
import log

server = None

dir = ""


def load():
    global server, dir
    customer_import = None
    try:
        customer_import = __import__("custom." + config.config["custom"]["server"], fromlist=[''])
        log.info("Custom %s loaded" % config.config["custom"]["server"])
    except Exception as e:
        log.critical("Impossible to load the custom server")
        exit()
    server = customer_import.server
    dir = "custom/" + config.config["custom"]["server"] + "/"
