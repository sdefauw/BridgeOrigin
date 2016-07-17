import pyshark
import os
import re

import sniffer
import connectivity


class PcapFileSniffer(sniffer.Sniffer):
    def __init__(self, server, protocol, category_fun, conn_layer='ip'):
        sniffer.Sniffer.__init__(self, server)
        self.connectivity_layer = conn_layer
        self.protocol = protocol
        self.prot_cat = category_fun

    def __process_cap(self, cap):
        for packet in cap:
            p = CapPacket(packet[self.protocol], self.protocol, self.prot_cat(eval("packet.%s" % self.protocol)))
            src = packet[self.connectivity_layer].src
            dst = packet[self.connectivity_layer].dst
            time = packet.sniff_timestamp
            if src in self.server.connectivity():
                # Send packet
                p.set_src(src, time)
                p.set_dst(dst)
            else:
                # Recv packet
                p.set_dst(src)
                p.set_src(dst, time)

    def get_packets(self, filter, tmp_dir):
        cap = pyshark.FileCapture(os.path.join(tmp_dir, '%d.pcap' % self.server.key))
        self.__process_cap(cap)


class PcapRemoteSniffer(PcapFileSniffer):
    def __init__(self, server, protocol, category_fun, conn_layer='ip', ports=None, filter=None):
        PcapFileSniffer.__init__(self, server, protocol, category_fun, conn_layer)
        self.ports = ports
        self.filter = filter
        self.remote_file_path = "/tmp/brorig.pcap"
        ports_arg = "" if not self.ports else " or ".join("port %d" % i for i in self.ports)
        filter_arg = "" if not self.filter else self.filter
        self.cmd = re.sub(' +', ' ',
                          "sudo tshark -n %s %s -i eth1 -w %s" % (ports_arg, filter_arg, self.remote_file_path))

    def capture_start(self):
        connectivity.Script.remote_exe(self.server.ssh_connection, "screen -dmS brorig bash -c '%s'" % self.cmd)

    def capture_stop(self):
        connectivity.Script.remote_exe(self.server.ssh_connection, "sudo kill -9 $(pgrep -f '%s')" % self.cmd)

    def clean(self):
        connectivity.Script.remote_exe(self.server.ssh_connection, "sudo rm -rf %s" % self.remote_file_path)

    def capture_status(self):
        stdout = connectivity.Script.remote_exe(self.server.ssh_connection,
                                                "pgrep -f '%s' > /dev/null; echo $?" % self.cmd)
        return stdout == "0\n"

    def get_packets(self, filter, tmp_dir):
        # TODO transfert the pcap trace to the main server
        # PcapFileSniffer.get_packets(self, filter, tmp_dir)
        return []


class CapPacket(sniffer.Packet):
    def __init__(self, packet, protocol, category):
        sniffer.Packet.__init__(self, protocol, category)
        self.packet = packet

    def equals(self, other):
        if not isinstance(other, CapPacket):
            return False
        # TODO too CPU computation
        return self.packet == other.packet

    def template(self):
        return ("packet.html", {
            "packet": self.packet
        })
