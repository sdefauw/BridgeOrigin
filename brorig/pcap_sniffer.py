#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import base64
import pyshark
import os
import re
import datetime
import uuid

import brorig.custom as custom
import brorig.sniffer as sniffer
import brorig.connectivity as connectivity
import brorig.log as log


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
            p = packet_type(packet[protocol_name], cat_fun(eval("packet.%s" % protocol_link['pcap_link'])))
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
                p.set_src(src_server)
                p.set_dst(self.server, time)
            self.packets.append(p)

    def get_packets(self, filter, file_path):
        cap = pyshark.FileCapture(file_path)
        self.__process_cap(cap)

    def packets_supported(self):
        return [protocol_supported[p]['packet'] for p in self.protocols]


class PcapRemoteSniffer(PcapFileSniffer):
    def __init__(self, server, protocols, conn_layer='ip', ports=None, filter=None):
        PcapFileSniffer.__init__(self, server, protocols, conn_layer)
        self.ports = ports
        self.filter = filter
        self.remote_file_path = "/tmp/brorig_{0!s}.pcap".format(base64.b32encode(uuid.uuid4().bytes)[:26])
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
        transfer_path = "/tmp/brorig_transfer_{0!s}.pcap".format(base64.b32encode(uuid.uuid4().bytes)[:26])
        local_path = os.path.join(tmp_dir, "log/pcap/")
        # Shrink the pcap trace base on the filter
        log.debug("Shrink the pcap file based on filters")
        t_start = filter['time']['start'].strftime("%Y-%m-%d %X")
        t_stop = filter['time']['stop'].strftime("%Y-%m-%d %X")
        shrink_cmd = 'sudo editcap -v -A "{start}" -B "{stop}" {f_remote} {t_path} > /dev/null 2> /dev/null'.format(
            start=t_start,
            stop=t_stop,
            f_remote=self.remote_file_path,
            t_path=transfer_path)
        connectivity.Script.remote_exe(self.server.ssh_connection, shrink_cmd)
        # Download the trace to the server directory
        log.debug("Download pcap trace shrinked")
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        local_path = os.path.join(local_path,
                                  '{time}-{server}.pcap'.format(
                                      time=filter['time']['stop'].strftime("%Y-%m-%dT%X"),
                                      server=self.server.key))
        self.server.ssh_connection.open_ssh_connexion()
        trans = connectivity.Transfer(self.server.ssh_connection.transport)
        trans.get(transfer_path, local_path)
        # Remove transfer file
        rm_transfer_path_cmd = "sudo rm -rf {file}".format(file=transfer_path)
        connectivity.Script.remote_exe(self.server.ssh_connection, rm_transfer_path_cmd)
        # Close the connection
        self.server.ssh_connection.close_ssh_connexion()
        # Read the trace
        log.debug("Read pcap trace")
        PcapFileSniffer.get_packets(self, filter, local_path)


class CapPacket(sniffer.Packet):
    def __init__(self, packet, category):
        sniffer.Packet.__init__(self, category)
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
    def __init__(self, packet, category):
        CapPacket.__init__(self, packet, category)

    @staticmethod
    def protocol():
        return 'HTTP'

    def equals(self, other):
        if not isinstance(other, HttpPacket):
            return False
        if hasattr(self.packet, 'request_method') and hasattr(other.packet, 'request_method'):
            delta = None
            if self.dst['time'] and other.src['time']:
                delta = abs(other.src['time'] - self.dst['time'])
            if self.src['time'] and other.dst['time']:
                delta = abs(self.src['time'] - other.dst['time'])
            threshold = datetime.timedelta(microseconds=100000)
            if not delta or delta > threshold:
                return False
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