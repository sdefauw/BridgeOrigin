#!/usr/bin/env python
# coding: utf-8

import base64
import uuid
import calendar
from pytz.reference import UTC


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

    def capture_status(self):
        """
        Check to capture status
        :return: true if the capture is currently processed otherwise false
        """
        return True

    def clean(self):
        pass

    def get_packets(self, filter, tmp_dir):
        pass

    def protocol_used(self):
        """
        List of all protocol used by this sniffer
        :return: List of protocol key defined in protocol.json
        """
        return []


class Packet:
    ST_INIT, ST_NEW, ST_UPDATED, ST_TRANSFERRED = range(4)

    def __init__(self, protocol, category):
        self.category = category
        self.protocol = protocol
        self.src = None
        self.dst = None
        self.internal = False
        self.uuid = base64.b32encode(uuid.uuid4().bytes)[:26]
        self.correlate_key = None
        self.state = Packet.ST_INIT

    def set_src(self, server, time=None):
        self.src = {
            "server": server,
            "time": time
        }

    def set_dst(self, server, time=None):
        self.dst = {
            "server": server,
            "time": time
        }

    def equals(self, other):
        return False

    def template(self):
        return None, None

    def tags(self):
        """
        Give a list of tags to correlate packets. A tag is a unique ID shared between packets
        :return: list of tags
        """
        return []

    def search_criterion(self):
        """
        Get all data that will be inserted to the search engine.
        Default values: protocol, category, time.start, time.end, server.src (server key), server.dst (server key)
        :return: data collection searchable
        """
        return dict(
            protocol=self.protocol,
            category=self.category,
            time=dict(
                start=calendar.timegm(self.src['time'].timetuple()) if self.src['time'] else 0,
                end=calendar.timegm(self.dst['time'].timetuple()) if self.dst['time'] else 0
            ),
            server=dict(
                src=self.src['server'].key if self.src['server'] else None,
                dst=self.dst['server'].key if self.dst['server'] else None
            )
        )
