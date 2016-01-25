#!/usr/bin/env python
# coding: utf-8

import json
import os
import shutil

import util

config = {}
filename = None

log_level = 'DEBUG'


def load(path):
    global config, filename
    json_data = open(path)
    filename = path
    config = json.load(json_data)
    json_data.close()


def gen_template(path):
    if util.query_yes_no("Would you like to create a new empty configuration file ?"):
        root_path = os.path.abspath(os.path.dirname(__file__))
        shutil.copyfile(root_path + '/config.json.template', path)
        print("Configuration file created: %s" % path)
