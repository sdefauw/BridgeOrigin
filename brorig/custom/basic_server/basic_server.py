#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import brorig.server as server
import brorig.config as config
import brorig.connectivity as connectivity
import brorig.pcap_sniffer as pcap_sniffer
import brorig.log as log


class Server(server.ServerIP):
    def __init__(self, key, name, cluster, group):
        server.ServerIP.__init__(self, key, name, cluster)
        self.group = group
        self.sniffers = [
            pcap_sniffer.PcapRemoteSniffer(server=self, protocols=['HTTP'], ports=[80])
        ]

    def set_ssh_info(self, hostname, user, passwd=None, pkey_path=None):
        self.hostname = hostname
        self.ssh_connection = connectivity.Connection(self.hostname,
                                                      username=user,
                                                      passwd=passwd,
                                                      pkey_path=pkey_path)

    def connectivity(self, full=False):
        # remove loopback connectivity
        return [ip for ip in server.ServerIP.connectivity(self, full) if ip != "127.0.0.1"]

    def remote_connectivity(self):
        """
        Return the ICMP (ping) connectivity with all servers of the farm
        """
        global farm
        connection_list = []
        i = 0
        for s in farm.list():
            if s == self:
                continue
            for ip in s.connectivity():
                # TODO do an optimization to use a single connection for all ping
                ping_stdout = connectivity.Script.remote_exe(self.ssh_connection, "ping -c 1 %s  > /dev/null; echo $?" % ip)
                if ping_stdout == "0\n":
                    i += 1
                    connection_list.append({
                        "name": "Conn %d" % i,
                        "conn": ip
                    })
        return connection_list


class VagrantServer(Server):
    def __init__(self, key, name, cluster, group):
        Server.__init__(self, key, name, cluster, group)

    def remote_connectivity(self):
        # Remove 10.0.2.15 connectivity
        return [i for i in Server.remote_connectivity(self) if i['conn'] != "10.0.2.15"]


class Farm(server.Farm):
    def __init__(self):
        server.Farm.__init__(self)
        self.clusters = []
        self.servers = []
        self.type_of_server_available = {
            "basic": Server,
            "vagrant": VagrantServer
        }

    def list(self):
        """
        Build farm of server based on configuration file according to following structure:

        "farm": {
            "servers": [
              {
                "key": <unique_key>,
                "name": <name _of_server>,
                "cluster": <name_of_cluster_defined>,
                "group": <group_id>,
                "hostname": <server_hostanme>,
                "type": basic|vagrant
                "ssh": {
                    "user": <login_user>,
                    "passwd": <user_password> (optional)
                    "pkey": <ssh_private_key> (optional)
                }
              },
              ...
            ],
            "clusters": [
              {"name": <id_of_cluster>},
              ...
            ]
          }
        """
        if self.servers:
            return self.servers
        self.clusters = [server.Cluster(c["name"]) for c in config.config["farm"]["clusters"]]
        for s in config.config["farm"]["servers"]:
            if 'type' not in s["type"] and s["type"] not in self.type_of_server_available:
                serverClass = self.type_of_server_available["basic"]
                log.warning("Type of server undefined: using basic sever by default")
            else:
                serverClass = self.type_of_server_available[s["type"]]
            s_obj = serverClass(str(s["key"]), s["name"], [c for c in self.clusters if c.name == s["cluster"]][0], s["group"])
            s_obj.set_ssh_info(s["hostname"], s["ssh"]["user"],
                               passwd=s["ssh"]["passwd"] if 'passwd' in s['ssh'] else None,
                               pkey_path=s['ssh']['pkey'] if 'pkey' in s['ssh'] else None)
            self.servers.append(s_obj)
        for s in self.servers:
            s.cluster.add_server(s)
        return self.servers

    def cluster_id(self):
        return self.clusters


farm = Farm()
