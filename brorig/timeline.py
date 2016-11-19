#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import base64
import gc
import threading
import uuid

import brorig.log as log
from brorig.sniffer import Packet
from brorig.search import SearchManager


class Timeline:
    def __init__(self, network, tmp_dir, filter=None):
        self.net = network
        self.filter = filter
        self.search = SearchManager(self.net)
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

    def group_packet(self):
        """
        Group packet with seeming tags
        Algorithm: 
         - Create a bipartite graph where one side is packets set and the other hand the tags set. Each link is the 
         relation between the packet and the tag. 
         - Compute Depth First Search to find all packets group. Indeed each connected component is a flow.
        :return:
        """
        log.debug("Computing packet group...")
        packets = [p for n in self.net.nodes for p in n.packet_list()] + \
                  [p for l in self.net.links for p in l.packet_list()]
        # Compute network graph
        n_packet = []
        n_packet_value = dict()
        n_tag = []
        n_tag_value = dict()
        l = []
        for p in packets:
            pn = dict(group=-1, value=p, links=[])
            for tag in p.tags():
                if tag not in n_tag_value:
                    n_tag_value[tag] = len(n_tag)
                    l.append((len(n_tag), len(n_packet)))
                    n_tag.append(dict(group=-1, value=tag, links=[len(l)-1]))
                else:
                    l.append((n_tag_value[tag], len(n_packet)))
                    n_tag[n_tag_value[tag]]['links'].append(len(l)-1)
                pn['links'].append(len(l)-1)
            n_packet_value[p] = len(n_packet)
            n_packet.append(pn)

        def dfs(node_index, is_packet, group_num):
            node = n_packet[node_index] if is_packet else n_tag[node_index]
            if node['group'] >= 0:
                # End of recursion: reach leaf
                return
            # Tag the node
            if is_packet:
                n_packet[node_index]['group'] = group_num
            else:
                n_tag[node_index]['group'] = group_num
            # Recursion
            for link in node['links']:
                dfs(l[link][int(not is_packet)], not is_packet, group_num)

        # Compute Depth First Search to get connected component
        log.debug("Doing depth first search on tag packet graph...")
        group_id = 0
        for idx, node in enumerate(n_packet):
            if node['group'] < 0:
                # node without group
                dfs(idx, True, group_id)
                n_packet[idx]['group'] = group_id
                group_id += 1

        # Convert graph to output structure
        log.debug("Convert tag packet graph into packet group")
        tag_group = dict()
        for n in n_packet:
            if n['group'] not in tag_group:
                tag_group[n['group']] = dict(tags=[], set=[], uuid=base64.b32encode(uuid.uuid4().bytes)[:26])
            tag_group[n['group']]['set'].append(n['value'])
        for n in n_tag:
            tag_group[n['group']]['tags'].append(n['value'])

        log.debug("Saving packet group computation")
        self.net.stat['packet_group'] = tag_group

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
        self.__set_to_network_level()
        self.__clean_sniffer()
        self.search.populate_search_engine()
        gc.collect()
