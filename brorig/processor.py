#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import base64
import calendar
import datetime
import gc
import json
import multiprocessing
import threading
import time
import uuid

from brorig import config, sniffer, custom, network, server, log
from brorig.search import SearchManager
from brorig.sniffer import Packet


class TimelinePacketProcessHelper(threading.Thread):
    def __init__(self, ws, clean=False, filter={}):
        threading.Thread.__init__(self)
        self.ws = ws
        self.filter = filter
        self.clean_packet = clean
        self.real_time = False
        self.transfer_old = True
        self.refresh_interval = config.config["real-time"]["refresh_interval"]

    def __gen_packet_list(self, list):
        def time_format(t):
            return calendar.timegm(t.timetuple()) * 1e3 + t.microsecond / 1e3 if t else None

        p_list_to_transfer = [(item, p) for item in list for p in item.packet_list() if p.src and p.src["time"] ]
        # Remove packet already transferred
        if not self.transfer_old:
            p_list_to_transfer = [(item, p) for (item, p) in p_list_to_transfer if not p.state == sniffer.Packet.ST_TRANSFERRED]

        # Tag packet that transferred to the front-end
        for (_, p) in p_list_to_transfer:
            p.state = sniffer.Packet.ST_TRANSFERRED

        return [{
                    "uuid": p.uuid,
                    "category": p.category,
                    "protocol": p.protocol,
                    "start": time_format(p.src["time"]) if p.src else None,
                    "end": time_format(p.dst["time"]) if p.dst else None,
                    "lane": item.uuid
                } for (item, p) in p_list_to_transfer]

    def __gen_packet_group(self, groups):
        return [
            dict(tags=g['tags'],
                 packets=[p.uuid for p in g['set']],
                 uuid=g['uuid'])
            for _, g in groups.iteritems()
        ]

    def __gen_stat(self):
        PacketProcessor(self.ws.client.network, self.ws.client.directory, self.filter).group_packet()
        self.ws.write_message(json.dumps(dict(
            packets=dict(
                groups=self.__gen_packet_group(self.ws.client.network.stat['packet_group'])
            )
        )))

    def packet_trigger(self):
        if self.clean_packet:
            self.ws.client.network.clean()
        PacketProcessor(self.ws.client.network, self.ws.client.directory, self.filter).collect()
        self.transfer_old = not self.real_time
        self.ws.write_message(json.dumps(dict(
            packets=dict(
                set=self.__gen_packet_list(self.ws.client.network.nodes)
            )
        )))
        self.ws.write_message(json.dumps(dict(
            packets=dict(
                set=self.__gen_packet_list(self.ws.client.network.links)
            )
        )))
        p = multiprocessing.Process(target=self.__gen_stat)
        p.start()

    def run(self):
        if self.real_time:
            # refresh new packet
            log.info("Start real-time")
            time.sleep(self.refresh_interval)
            t = datetime.datetime.utcnow()
            self.filter['time'] = {
                'start': t - datetime.timedelta(seconds=self.refresh_interval),
                'stop': t
            }
            while self.real_time:
                t = datetime.datetime.utcnow()
                # Collect packets
                self.packet_trigger()
                # Compute next time
                now = datetime.datetime.utcnow()
                d = self.refresh_interval - (now - t).seconds
                if d < 0:
                    log.warning("Real time issue: time to process data takes more time to refresh")
                else:
                    time.sleep(d)
                # Adapt the filter for the next iteration
                self.filter['time'] = {
                    'start': t,
                    'stop': datetime.datetime.utcnow()
                }
            log.info("End of real-time")
        else:
            # Inform only new packet
            self.packet_trigger()
            # Check if we don't need to run again
            if self.real_time:
                self.run()


class NetworkProcess(threading.Thread):
    def __init__(self, request, ws):
        threading.Thread.__init__(self)
        self.request = request
        self.ws = ws
        self.cmd = {
            "add_nodes": self.add_nodes,
            "clean": self.clean_graph,
            "connect_mgt": self.connectivity
        }

    def gen_node(self, node, pos):
        node.index = pos
        return {
            "id": node.server.key,
            "uuid": node.uuid,
            "name": node.server.name,
            "connectivity": {
                "own": node.server.connectivity(full=True),
                "remote": node.server.remote_connectivity()
            },
            "group": node.server.group,
            "cluster": node.server.cluster.name,
            "serverkey": node.server.key,
            "link": node.server.link
        }

    def gen_link(self, link):
        l = {
            "uuid": link.uuid,
            "source": link.src.index,
            "target": link.dst.index if link.dst else None
        }
        if link.dst:
            l['name'] = "%s to %s" % (link.src.server.name, link.dst.server.name)
        return l

    def write_ws(self, data):
        self.ws.write_message(json.dumps(data))

    def send_graph(self, net):
        self.write_ws({
            "network": {
                "nodes": [self.gen_node(n, i) for i, n in enumerate(net.nodes)],
                "links": [self.gen_link(l) for l in net.links if l.src and l.dst]
            }})

    def add_nodes(self, data):
        server_list = [s for s in custom.server.farm.list() if str(s.key) in data]
        self.ws.client.network.add_node(server_list)

    def clean_graph(self, data):
        if data:
            self.ws.client.network = network.Network()

    def connectivity(self, data):
        net = self.ws.client.network
        for c in data:
            node_key = c['node']
            node = net.get_node(node_key)
            remote_conn = c['remote_conn']
            status = c['status']
            if not node:
                log.warning("Ask change connectivity of unknown node")
                continue
            if status == "enable":
                # Add new virtual node
                virtual_nodes = [n for n in net.nodes for c in n.server.connectivity() if remote_conn in c]
                if len(virtual_nodes) == 1:
                    virtual_node = virtual_nodes[0]
                    if not isinstance(virtual_node.server, server.VirtualServer):
                        continue
                    virtual_node.server.add_connectivity(node_key)
                    net.set_connectivity(node)
                    net.set_connectivity(virtual_node)
                else:
                    vs = server.VirtualServer(remote_conn)
                    vs.add_connectivity(node_key)
                    net.add_node([vs])
            elif status == "disable":
                # Remove connectivity to and from the node
                remote_nodes = [n for n in net.nodes for c in n.server.connectivity() if remote_conn in c]
                for n in remote_nodes:
                    if isinstance(n.server, server.VirtualServer):
                        net.remove_connectivity(node, remote_conn)
                    if not isinstance(node.server, server.VirtualServer):
                        for c in node.server.connectivity():
                            net.remove_connectivity(n, c)
                # Clean all virtual server
                v_node = [n for n in net.nodes if isinstance(n.server, server.VirtualServer) if n.remote_vertex == []]
                for n in v_node:
                    net.remove_node(n)
            else:
                log.error("Invalid connectivity status")

    def run(self):
        for r in self.request:
            action, args = r.iteritems().next()
            if action in self.cmd:
                log.debug("Executing network action: %s(%s)" % (action, args))
                self.cmd[action](args)
            else:
                log.error("Network action %s not found" % action)
        self.send_graph(self.ws.client.network)


class PacketProcessor:
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