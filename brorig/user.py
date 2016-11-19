#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import uuid
import shutil
import base64
import gc
import os

import brorig.log as log
import brorig.config as config
from brorig.search import SearchManager


class UserList:
    """
    UserList is a collection {User} using the application.
    """

    def __init__(self):
        self.list = {}

    def find(self, uuid):
        return self.list[uuid]

    def add(self, user):
        assert isinstance(user, User)
        self.list[user.uuid] = user

    def remove(self, user):
        assert isinstance(user, User)
        user.destroy()
        del self.list[user.uuid]

    def destroy(self):
        for _, user in self.list.items():
            user.destroy()
        log.info("Destroy %d reminding users" % (len(self.list)))


class User:
    """
    Representation of an user in the browser.
    The object contains information of the user request like network, packets, search, filetrs,...
    """

    def __init__(self):
        self.uuid = base64.b32encode(uuid.uuid4().bytes)[:26]
        self.directory = self.__allocate_directory()
        self.network = None
        self.timeline = None
        self.timeline_filter = {}
        self.search_engine = None
        self.clean()

    def __allocate_directory(self):
        root_path = config.config['server']['data_path']
        if not os.path.isdir(root_path):
            log.debug("Root directory created: %s" % root_path)
            os.makedirs(root_path)
        dir = root_path + self.uuid + "/"
        os.makedirs(dir)
        log.debug("Allocate temporary directory %s" % dir)
        return dir

    def destroy(self):
        shutil.rmtree(self.directory)
        self.clean()
        log.debug("Destroy user %s" % self.uuid)

    def clean(self):
        self.network = None
        self.timeline = None
        if self.search_engine:
            self.search_engine.clean()
        self.search_engine = SearchManager(self.uuid)
        gc.collect()

    def __str__(self):
        return str(self.uuid)
