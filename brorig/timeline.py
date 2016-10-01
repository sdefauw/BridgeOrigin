#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import base64
import gc
import threading
import uuid

import brorig.log as log
from brorig.sniffer import Packet


class Timeline:
    def __init__(self, network, tmp_dir, filter=None):
        self.net = network
        self.filter = filter
        self.tmp_dir = tmp_dir

    def __get_packets(self):
        """
        Collect all packets from servers with a filter
        :return:
        """
        log.info("Getting packets from remote devices")
        threads = []
        try:
            for node in self.net.nodes:
                for sniffer in node.server.sniffers:
                    th = threading.Thread(target=sniffer.get_packets,
                                          args=(self.filter, self.tmp_dir))
                    threads.append(th)
                    th.start()
            log.debug("Waiting all download...")
            for th in threads:
                th.join()
            log.debug("Packets received")
        except Exception as e:
            log.error("Server execution:" + str(e))
            return

    def __set_to_network_level(self):
        """
        Take all packet from the server level (in sniffer) and place it in the network level (edges and vertexes).
        Do packets correlation in the network level.
        :return:
        """
        log.info("Set packet to network level (correlation)")
        node_server = [n.server for n in self.net.nodes]
        for node in self.net.nodes:
            for sniffer in node.server.sniffers:
                for packet in sniffer.packets:
                    # Node packet
                    if packet.internal or (packet.src and packet.dst and packet.src["server"] == packet.dst["server"]):
                        node.set_packets(packet)
                        packet.state = Packet.ST_NEW
                        continue
                    # Link packet
                    if packet.src and packet.dst and packet.src['server'] == node.server and packet.dst[
                        'server'] in node_server:
                        # Find other packet
                        remote_packet = [p for sniffer in packet.dst['server'].sniffers for p in sniffer.packets if
                                         packet.equals(p)]
                        if len(remote_packet) == 1:
                            remote_packet = remote_packet[0]
                            # Update info
                            packet.dst = remote_packet.dst
                            packet.state = Packet.ST_UPDATED
                        elif len(remote_packet) > 2:
                            log.warning("Multiple remote packet is found !")
                            # TODO take the short time delta
                        # Add to links
                        links_matched = [l for n, l in node.remote_vertex if n.server == packet.dst['server']]
                        for l in links_matched:
                            l.set_packets(packet)
                            packet.state = Packet.ST_NEW
                log.debug("Packet correlation done for sniffer %s on %s" % (sniffer.__class__.__name__, node.server.name))

    def __group_packet(self):
        """
        Group packet with seeming tags
        :return:
        """
        packets = [p for node in self.net.nodes for sniffer in node.server.sniffers for p in sniffer.packets]
        tag_set = {}
        tag_group = []
        # Build tag set
        for p in packets:
            for tag in p.tags():
                if tag not in tag_set:
                    tag_set[tag] = dict(set=[], group=-1)
                tag_set[tag]['set'].append(p)
        # Group tag set
        for p in packets:
            group_id = -1
            for tag in p.tags():
                if tag_set[tag]['group'] < 0:
                    # Set tag group
                    if group_id < 0:
                        # Add to new group
                        group_id = len(tag_group)
                        tag_group.append([tag])
                    else:
                        tag_group[group_id].append(tag)
                    tag_set[tag]['group'] = group_id
        # Group tag set
        tag_final_set = []
        for g in tag_group:
            packet_set = []
            for tag in g:
                packet_set += tag_set[tag]['set']
            tag_final_set.append(dict(
                tags=g,
                set=list(set(packet_set)),
                uuid=base64.b32encode(uuid.uuid4().bytes)[:26]
            ))
        self.net.stat['packet_group'] = tag_final_set

    def __clean_sniffer(self):
        """
        Empty sniff of captured packets.
        :return:
        """
        log.debug("Clean sniffers")
        for node in self.net.nodes:
            for sniffer in node.server.sniffers:
                sniffer.packets = []

    def collect(self):
        """
        Collect all packets in the user network
        :return:
        """
        self.__get_packets()
        # TODO concurrent execution
        self.__set_to_network_level()
        self.__group_packet()
        self.__clean_sniffer()
        gc.collect()
