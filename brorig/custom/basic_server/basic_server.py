import server
import config
import connectivity
import pcap_sniffer


class Server(server.ServerIP):
    def __init__(self, key, name, cluster, group):
        server.Server.__init__(self, key, name, cluster)
        self.group = group
        self.sniffers = [
            pcap_sniffer.PcapRemoteSniffer(server=self, protocols=['HTTP'], ports=[80])
        ]

    def set_ssh_info(self, hostname, user, passwd):
        self.hostname = hostname
        self.ssh_connection = connectivity.Connection(self.hostname, user, passwd)

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


class Farm(server.Farm):
    def __init__(self):
        server.Farm.__init__(self)
        self.clusters = []
        self.servers = []

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
                "ssh": {
                    "user": <login_user>,
                    "passwd": <user_password>
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
            s_obj = Server(s["key"], s["name"], [c for c in self.clusters if c.name == s["cluster"]][0], s["group"])
            s_obj.set_ssh_info(s["hostname"], s["ssh"]["user"], s["ssh"]["passwd"])
            self.servers.append(s_obj)
        for s in self.servers:
            s.cluster.add_server(s)
        return self.servers

    def cluster_id(self):
        return self.clusters


farm = Farm()
