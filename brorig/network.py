#!/usr/bin/env python
# coding: utf-8

import base64
import uuid


class Vertex:
    def __init__(self, server):
        self.server = server
        self.uuid = base64.b32encode(uuid.uuid4().bytes)[:26]
        self.conn = []
        self.remote_vertex = []
        self.__packets = []

    def set_packets(self, packet):
        self.__packets.append(packet)

    def packet_list(self):
        return self.__packets

    def clean_packets(self):
        self.__packets = []


class Edge:
    def __init__(self, name, src=None, dst=None):
        self.name = name
        self.uuid = base64.b32encode(uuid.uuid4().bytes)[:26]
        self.src = src
        self.dst = dst
        self.__packets = []

    def set_packets(self, packet):
        self.__packets.append(packet)

    def packet_list(self):
        return self.__packets

    def clean_packets(self):
        self.__packets = []


class Network:
    def __init__(self):
        self.nodes = []
        self.links = []

    def add_node(self, list_server):
        # Nodes data
        for server in list_server:
            v = Vertex(server)
            v.conn = server.connectivity()
            self.nodes.append(v)
        # Link data
        # TODO remove duplicated links
        for node in self.nodes:
            self.set_connectivity(node)

    def set_connectivity(self, node):
        remote_connection_list = node.server.remote_connectivity()
        remote_vertex_known = {v[0]: v[1] for v in node.remote_vertex}
        node.remote_vertex = []
        for remote_connection in remote_connection_list:
            remote_node = self.get_node(remote_connection["conn"])
            if not remote_node:
                continue
            if remote_node in remote_vertex_known:
                e = remote_vertex_known[remote_node]
            else:
                e = Edge(remote_connection["name"], node, remote_node)
                self.links.append(e)
            node.remote_vertex.append((remote_node, e))

    def get_node(self, connectivity_id):
        for node in self.nodes:
            if connectivity_id in node.conn:
                return node
        return None

    def clean(self):
        # Remove packets on edges and vertexes
        for i in self.nodes + self.links:
            i.clean_packets()
