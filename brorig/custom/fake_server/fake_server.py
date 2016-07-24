#!/usr/bin/env python
# coding: utf-8

import datetime
import time
import random

import server
import sniffer
import log


class Server(server.Server):
    def __init__(self, key, name, cluster):
        server.Server.__init__(self, key, name, cluster)
        self.sniffers = [FakeSniffer(self)]

    def connectivity(self, full=False):
        self.own_connectivity = [{"name": "eth0", "conn": self.key}]
        return self.own_connectivity if full else [c["conn"] for c in self.own_connectivity]

    def remote_connectivity(self):
        return [{"name": "eth" + s.key, "conn": s.key} for s in farm.list() if s.key != self.key]


class Farm(server.Farm):
    def __init__(self):
        server.Farm.__init__(self)
        self.cluster = []
        self.server = []

    def list(self):
        if not self.server:
            self.server = [Server(str(i), "Server" + str(i), server.Cluster(str(i % 3))) for i in range(1, 20)]
        return self.server

    def cluster_list(self):
        return self.cluster


class FakeSniffer(sniffer.Sniffer):
    def __init__(self, server):
        sniffer.Sniffer.__init__(self, server)
        self.capture_enabled = True

    def capture_start(self):
        log.info("Capturing...")
        time.sleep(2)
        self.capture_enabled = True

    def capture_stop(self):
        log.info("Stopping capture...")
        self.capture_enabled = False

    def capture_status(self):
        return self.capture_enabled

    def clean(self):
        log.info("Sniffer washed :)")

    def get_packets(self, filter, tmp_dir):
        for i in range(0, 20):
            p = FakePacket("cat." + str(random.randint(0, 3)))
            now = datetime.datetime.utcnow()
            trand = random.randint(0, (filter['time']['stop'] - filter['time']['start']).seconds*1000*1000)
            d = now - datetime.timedelta(microseconds=trand)
            p.set_src(self.server, d)
            m = d.microsecond + random.randint(0, 99999)
            p.set_dst(self.server, d.replace(microsecond=(m if m < 1000000 else 999999)))
            self.packets.append(p)

    def protocol_used(self):
        return ['fakepacket']


class FakePacket(sniffer.Packet):
    def __init__(self, name):
        sniffer.Packet.__init__(self, 'fakepacket', name)
        self.internal = True

    def template(self):
        return ("template.html", {
            "packet": "Fake packet",
        })


farm = Farm()
