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
        self.stat = {}

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

    def remove_node(self, node):
        """
        Remove node form the network. I will remove edges and vertex associated
        :param node: node to remove
        """
        del self.nodes[self.nodes.index(node)]
        links_to_remove = [l for l in self.links if l.dst == node or l.src == node]
        for l in links_to_remove:
            self.remove_link(l)

    def remove_link(self, link):
        """
        Remove links from the network graph
        :param link: link to remove
        """
        # Remove from graph
        del self.links[self.links.index(link)]
        # Remove edge in vertex (remote_vertex)
        for index, v_remote in enumerate(link.src.remote_vertex):
            _, e = v_remote
            if e == link:
                del link.src.remote_vertex[index]

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

    def remove_connectivity(self, node, connectivity):
        """
        Remove connectivity from node to the all node with connectivity given
        :param node: node to remove vertex
        :param connectivity: remote connectivity of all node to remove
        """
        edges = []
        for index, t in enumerate(node.remote_vertex):
            v, e = t
            if connectivity in v.conn:
                edges.append(e)
                del node.remote_vertex[index]
        for edge in edges:
            del self.links[self.links.index(edge)]

    def get_node(self, connectivity_id):
        for node in self.nodes:
            if connectivity_id in node.conn:
                return node
        return None

    def clean(self):
        # Remove packets on edges and vertexes
        for i in self.nodes + self.links:
            i.clean_packets()
