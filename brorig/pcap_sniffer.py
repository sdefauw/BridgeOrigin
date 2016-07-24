import pyshark
import os
import re
import datetime

import custom
import sniffer
import connectivity
import log


class PcapFileSniffer(sniffer.Sniffer):
    def __init__(self, server, protocols, conn_layer='ip'):
        sniffer.Sniffer.__init__(self, server)
        self.connectivity_layer = conn_layer
        self.protocols = protocols

    def __process_cap(self, cap):
        for packet in cap:
            matched_proto = [p for p in self.protocols if p in protocol_supported and protocol_supported[p]['pcap_link'] in packet]
            if len(matched_proto) != 1:
                continue
            protocol_name = matched_proto[0]
            protocol_link = protocol_supported[protocol_name]
            cat_fun = protocol_link['category']
            packet_type = protocol_link['packet']
            p = packet_type(packet[protocol_name], protocol_name, cat_fun(eval("packet.%s" % protocol_link['pcap_link'])))
            src = packet[self.connectivity_layer].src
            dst = packet[self.connectivity_layer].dst
            time = datetime.datetime.utcfromtimestamp(float(packet.sniff_timestamp))
            if src in self.server.connectivity():
                # Send packet
                p.set_src(self.server, time)
                dst_server = custom.server.farm.get_server_by_connectivity(dst)
                p.set_dst(dst_server)
            else:
                # Recv packet
                src_server = custom.server.farm.get_server_by_connectivity(src)
                p.set_dst(src_server, time)
                p.set_src(self.server)
            self.packets.append(p)

    def get_packets(self, filter, file_path):
        cap = pyshark.FileCapture(file_path)
        self.__process_cap(cap)

    def protocol_used(self):
        return self.protocols


class PcapRemoteSniffer(PcapFileSniffer):
    def __init__(self, server, protocols, conn_layer='ip', ports=None, filter=None):
        PcapFileSniffer.__init__(self, server, protocols, conn_layer)
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
        transfer_path = "/tmp/brorig_transfer.pcap"
        local_path = os.path.join(tmp_dir, "log/pcap/")
        # Shrink the pcap trace base on the filter
        log.debug("Shrink the pcap file based on filters")
        t_start = filter['time']['start'].strftime("%Y-%m-%d %X")
        t_stop = filter['time']['stop'].strftime("%Y-%m-%d %X")
        shrink_cmd = 'sudo editcap -v -A "%s" -B "%s" %s %s > /dev/null 2> /dev/null' % (
            t_start, t_stop, self.remote_file_path, transfer_path)
        connectivity.Script.remote_exe(self.server.ssh_connection, shrink_cmd)
        # Download the trace to the server directory
        log.debug("Download pcap trace shrinked")
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        local_path = os.path.join(local_path,
                                  '%s-%s.pcap' % (filter['time']['stop'].strftime("%Y-%m-%dT%X"), self.server.key))
        self.server.ssh_connection.open_ssh_connexion()
        trans = connectivity.Transfer(self.server.ssh_connection.transport)
        trans.get(transfer_path, local_path)
        self.server.ssh_connection.close_ssh_connexion()
        # Read the trace
        log.debug("Read pcap trace")
        PcapFileSniffer.get_packets(self, filter, local_path)


class CapPacket(sniffer.Packet):
    def __init__(self, packet, protocol, category):
        sniffer.Packet.__init__(self, protocol, category)
        self.packet = packet

    def equals(self, other):
        if not isinstance(other, CapPacket):
            return False
        # WARNING too CPU computation
        return str(self.packet) == str(other.packet)

    def template(self):
        return ("packet.html", {
            "packet": self.packet
        })


class HttpPacket(CapPacket):
    def __init__(self, packet, protocol, category):
        CapPacket.__init__(self, packet, protocol, category)

    def equals(self, other):
        if not isinstance(other, HttpPacket):
            return False
        if hasattr(self.packet, 'request_method') and hasattr(other.packet, 'request_method'):
            # TODO not reliable
            return self.packet.request_method == other.packet.request_method and self.packet.request_uri == other.packet.request_uri and self.packet.request_method == other.packet.request_method and self.packet.host == other.packet.host
        if hasattr(self.packet, 'response_code') and hasattr(other.packet, 'response_code'):
            return self.packet.response_code == other.packet.response_code and self.packet.date == other.packet.date
        return False


def cat_http_fun(p_http):
    if hasattr(p_http, 'request_method'):
        return p_http.request_method
    if hasattr(p_http, 'response_code'):
        return p_http.response_code
    return None

protocol_supported = {
    'HTTP': {
        'pcap_link': 'http',
        'packet': HttpPacket,
        'category': cat_http_fun
    }
}