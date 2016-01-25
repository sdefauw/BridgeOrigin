#!/usr/bin/env python
# coding: utf-8

import re

import connectivity


class Server:
    def __init__(self, key, name, cluster):
        self.key = key
        self.name = name
        self.cluster = cluster
        # TODO create group class
        self.group = None
        self.ssh_connection = None
        self.hostname = name
        self.sniffers = []
        self.own_connectivity = []
        self.link = None

    def connectivity(self, full=False):
        """
        List of connectivity available on the server. It's a unique identify (by server).

        :param full: Show all information about the connectivity (name,...)
        :return: Array of connectivity
            [connect1, ...]                                 full=False
            [{"name":"my_name", "conn": connect1}, ...]     full=True
        """
        raise Exception("Connectivity must be implemented")

    def has_connectivity(self):
        return self.own_connectivity != []

    def remote_connectivity(self):
        """
        Get connectivity with others server. The connectivity must match connectivity list on the remote server.

        :return: list of connections. A connection has a name and a value.
            [{"name": "my_name", "conn": c}, ... ]
        """
        raise Exception("Remote connectivity must be implemented")


class ServerIP(Server):
    def __init__(self, key, name, cluster):
        Server.__init__(self, key, name, cluster)
        self.ip = []

    def __get_ip(self):
        ip_cmd_stdout = connectivity.Script.remote_exe(self.ssh_connection, "ip addr show")
        # TODO use framework
        interface_list = re.compile("[0-9]+: ([a-zA-Z0-9]+):").findall(ip_cmd_stdout)
        ip_list = re.compile("inet ([0-9.]+)/").findall(ip_cmd_stdout)
        return dict(zip(interface_list, ip_list))

    def connectivity(self, full=False):
        if self.own_connectivity == []:
            self.ip = self.__get_ip()
            self.own_connectivity = [{"name": eth, "conn": ip} for eth, ip in self.ip.iteritems()]
        return self.own_connectivity if full else [c["conn"] for c in self.own_connectivity]


class Cluster:
    id_gen = 0

    def __init__(self, name):
        self.name = name
        self.servers = []
        self.id = Cluster.id_gen
        Cluster.id_gen += 1

    def add_server(self, server):
        self.servers.append(server)


class Farm:
    def __init__(self):
        pass

    def list(self):
        """
        List of all servers available in the farm.
        :return: list of Server object
        """
        raise Exception("List of all server must be implemented")

    def cluster_list(self):
        """
        List of clusters available in the farm. A Cluster is a group of servers shared some properties .
        :return: list of Cluster object
        """
        raise Exception("List of cluster must be implemented")

    def get_server_by_key(self, key):
        for s in self.list():
            if s.key == key:
                return s
        return None

    def get_server_by_connectivity(self, connection):
        for server in self.list():
            if server.has_connectivity() and connection in server.connectivity():
                return server
        return None


farm = Farm()
