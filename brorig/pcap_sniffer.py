import pyshark
import os

import sniffer


class PcapFileSniffer(sniffer.Sniffer):
    def __init__(self, server, protocol, category, conn_layer='ip'):
        sniffer.Sniffer.__init__(self, server)
        self.connectivity_layer = conn_layer
        self.protocol = protocol
        self.prot_cat = category

    def __process_cap(self, cap):
        for packet in cap:
            p = CapPacket(packet[self.protocol], self.protocol, self.prot_cat)
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
        cap = pyshark.FileCapture(os.path.join(tmp_dir, self.server.key + '.pcap'))
        self.__process_cap(cap)


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
