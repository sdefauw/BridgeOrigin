#!/usr/bin/env python
# coding: utf-8

import datetime
import random

import server
import sniffer


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

    def list(self):
        return [Server(str(i), "Server" + str(i), server.Cluster(str(i % 3))) for i in range(1, 20)]

    def cluster_list(self):
        return self.cluster


class FakeSniffer(sniffer.Sniffer):
    def __init__(self, server):
        sniffer.Sniffer.__init__(self, server)

    def get_packets(self, filter, tmp_dir):
        for i in range(0, 20):
            p = FakePacket("cat." + str(random.randint(0, 3)))
            now = datetime.datetime.now()
            trand = random.randint(0, filter['time']['start'])
            d = now - datetime.timedelta(seconds=trand)
            p.set_src(self.server, d)
            m = d.microsecond + random.randint(0, 99999)
            p.set_dst(self.server, d.replace(microsecond=(m if m < 1000000 else 999999)))
            self.packets.append(p)


class FakePacket(sniffer.Packet):
    def __init__(self, name):
        sniffer.Packet.__init__(self, 'fakepacket', name)
        self.internal = True

    def template(self):
        return ("template.html", {
            "packet": "Fake packet",
        })


farm = Farm()
