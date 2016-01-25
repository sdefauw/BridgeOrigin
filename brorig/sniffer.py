#!/usr/bin/env python
# coding: utf-8

import base64
import uuid


class Sniffer:
    """
    Abstract class for all sniffer
    """

    def __init__(self, server):
        self.server = server
        self.packets = []

    def capture_start(self):
        pass

    def capture_stop(self):
        pass

    def clean(self):
        pass

    def get_packets(self, filter, tmp_dir):
        pass


class Packet:
    def __init__(self, protocol, category):
        self.category = category
        self.protocol = protocol
        self.src = None
        self.dst = None
        self.internal = False
        self.uuid = base64.b32encode(uuid.uuid4().bytes)[:26]
        self.correlate_key = None

    def set_src(self, server, time):
        self.src = {
            "server": server,
            "time": time
        }

    def set_dst(self, server, time):
        self.dst = {
            "server": server,
            "time": time
        }

    def equals(self, other):
        return False

    def template(self):
        return None, None
