#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import base64
import gc
import json
import os
import shutil
import threading
import time
import calendar
import uuid
import datetime

import tornado.escape
import tornado.gen
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.options
import tornado.web
import tornado.websocket

import brorig.config as config
import brorig.custom as custom
import brorig.log as log
import brorig.network as network
import brorig.server as server
import brorig.timeline as timeline
import brorig.sniffer as sniffer

threadServer = None

clientsList = None


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        custom_head = {
            "css": [],
            "js": []
        }
        dir_path = os.path.join(custom.dir, "www")
        if os.path.exists(dir_path):
            dir_www = os.listdir(dir_path)
            custom_head={
                "css": ["custom/" + f for f in dir_www if f.endswith(".css")],
                "js": ["custom/" + f for f in dir_www if f.endswith(".js")]
            }
        self.render("index.html", custom_head=custom_head)


class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "0")
        self.set_header("Access-Control-Allow-Origin", "*")


class ServerListHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(
                json.dumps([{"name": s.name, "key": s.key, "group": s.group} for s in custom.server.farm.list()]))


class ConfigurationSnifferHandler(tornado.web.RequestHandler):
    def __get_server(self, server_list):
        l = [str(i) for i in server_list]
        return [s for s in custom.server.farm.list() if str(s.key) in l]

    def __apply_sniffer_action(self, server_list, action):
        servers = self.__get_server(server_list)
        for server in servers:
            for sniffer in server.sniffers:
                action(server, sniffer)

    def get(self):
        servers = self.__get_server(self.get_argument("serverskey").split(','))
        status = [{'server': server.key, 'enable': sniffer.capture_status()}
                  for server in servers for sniffer in server.sniffers]
        self.write(json.dumps(status))

    def delete(self):
        def action(server, sniffer):
            log.debug("Cleanup traces on sniffer %s on %s" % (sniffer.__class__.__name__, server.name))
            sniffer.clean()
        data = tornado.escape.json_decode(self.request.body)
        self.__apply_sniffer_action(data['serverskey'], action)

    def put(self, *args, **kwargs):
        def action(server, sniffer):
            log.debug("Configure sniffer %s on %s" % (sniffer.__class__.__name__, server.name))
            if data['enable']:
                sniffer.capture_start()
            else:
                sniffer.capture_stop()
        data = tornado.escape.json_decode(self.request.body)
        self.__apply_sniffer_action(data['serverskey'], action)



class ProtocolHandler(tornado.web.RequestHandler):
    def load_json(self, path):
        try:
            json_data = open(path, 'r')
            protocol = json.load(json_data)
            json_data.close()
            return protocol
        except IOError as e:
            return {}

    def get(self):
        # Find graph
        client = self.get_argument("clientID")
        network = clientsList.find(client).network
        # Protocol needed
        p_list = list(set([p for l in network.nodes for s in l.server.sniffers for p in s.protocol_used()]))
        # Load all protocol description available
        protocol = self.load_json('www/packet/protocol.json')
        protocol_custom = self.load_json(custom.dir + "protocol.json")
        protocol.update(protocol_custom)
        # Filter to have all detail of protocols needed
        p = {p: protocol[p] for p in p_list}
        self.write(json.dumps(p))


class PacketHandler(tornado.web.RequestHandler):
    def get(self):
        global clientsList
        uuid = self.get_argument("uuid")
        client = self.get_argument("network")
        # Find graph
        network = clientsList.find(client).network
        # Find packet
        packet = [p for l in network.links for p in l.packet_list() if p.uuid == uuid]
        if len(packet) == 0:
            packet = [p for n in network.nodes for p in n.packet_list() if p.uuid == uuid]
        if len(packet) == 0:
            log.error("Packet not found")
            self.set_status(204)
            return
        p = packet[0]
        # Render packet
        template_name, template_args = p.template()
        if not template_name:
            self.set_status(204)
            return
        path_template = "packet/" + template_name
        if not os.path.isfile(os.path.join("www", path_template)):
            path_template = "../" + custom.dir + path_template
        self.render(path_template, **template_args)


class UserList:
    def __init__(self):
        self.list = {}

    def find(self, uuid):
        return self.list[uuid]

    def add(self, user):
        assert isinstance(user, User)
        self.list[user.uuid] = user

    def remove(self, user):
        assert isinstance(user, User)
        user.destroy()
        del self.list[user.uuid]

    def destroy(self):
        for _, user in self.list.items():
            user.destroy()
        log.info("Destroy %d users" % (len(self.list)))


class User:
    def __init__(self):
        self.uuid = base64.b32encode(uuid.uuid4().bytes)[:26]
        self.directory = self.__allocate_directory()
        self.network = None
        self.timeline = None
        self.timeline_filter = {}

    def __allocate_directory(self):
        root_path = config.config['server']['data_path']
        if not os.path.isdir(root_path):
            log.debug("Root directory created: %s" % root_path)
            os.makedirs(root_path)
        dir = root_path + self.uuid + "/"
        os.makedirs(dir)
        log.debug("Allocate temporary directory %s" % dir)
        return dir

    def destroy(self):
        shutil.rmtree(self.directory)
        self.clean()
        log.debug("Destroy user %s" % self.uuid)

    def clean(self):
        self.network = None
        self.timeline = None
        gc.collect()

    def __str__(self):
        return str(self.uuid)


class WebSocketNetworkHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
        self.command = {
            "network": self.network_build,
            "timeline": self.timeline_build,
        }

    def open(self, *args):
        global clientsList
        self.client = User()
        clientsList.add(self.client)
        self.stream.set_nodelay(True)
        self.write_message(json.dumps({
            "detail": {
                "uuid": self.client.uuid
            }
        }))
        self.timeline_th = None
        log.debug("WebSocket opened client %s" % self.client)

    def on_message(self, message):
        data = json.loads(message)
        for command, args in data.iteritems():
            if command in self.command:
                log.debug("Command executed: %s(%s)" % (command, args))
                self.command[command](args)
            else:
                log.error("Command % s not found" % command)

    def on_close(self):
        global clientsList
        if not clientsList:
            log.warning("Clients list not found")
            return
        clientsList.remove(self.client)
        log.debug("WebSocket closed for client %s" % self.client)

    def network_build(self, request):
        n = NetworkProcess(request, self)
        n.start()

    def timeline_build(self, config):
        # Set configuration in the timeline
        if 'filter' in config:
            # TODO
            # use self.client.timeline_filter
            pass
        if 'packet' in config:
            self.client.timeline_filter['time'] = {
                'start': datetime.datetime.utcfromtimestamp(config['packet']['from']/1000),
                'stop': datetime.datetime.utcfromtimestamp(config['packet']['to']/1000)
            }
        # Execute request
        if 'play' in config or 'packet' in config:
            # Configure the helper thread
            if not self.timeline_th or not self.timeline_th.isAlive():
                self.timeline_th = TimelinePacketProcessHelper(self, config['clean'], self.client.timeline_filter)
            # Set real time environment
            if 'play' in config:
                self.timeline_th.real_time = config['play']
            # Start the process
            if not self.timeline_th.isAlive():
                self.timeline_th.start()
            else:
                log.info("Timeline thread is running, updating only some information")


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

    def packet_trigger(self):
        if self.clean_packet:
            self.ws.client.network.clean()
        timeline.Timeline(self.ws.client.network, self.ws.client.directory, self.filter).collect()
        self.transfer_old = not self.real_time
        self.ws.write_message(json.dumps({"packets": self.__gen_packet_list(self.ws.client.network.nodes)}))
        self.ws.write_message(json.dumps({"packets": self.__gen_packet_list(self.ws.client.network.links)}))

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
            l['name'] = link.src.server.name + " to " + link.dst.server.name
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

    def run(self):
        for r in self.request:
            action, args = r.iteritems().next()
            if action in self.cmd:
                log.debug("Executing network action: %s(%s)" % (action, args))
                self.cmd[action](args)
            else:
                log.error("Network action % s not found" % action)
        self.send_graph(self.ws.client.network)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/server/list", ServerListHandler),
            (r"/ws/network", WebSocketNetworkHandler),
            (r"/packet", PacketHandler),
            (r"/configure/sniffer", ConfigurationSnifferHandler),
            (r'/protocol', ProtocolHandler),
            (r"/custom/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(custom.dir, "www")}),
            (r"/include/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "www")}),
        ]
        settings = dict(
                template_path=os.path.join(os.path.dirname(__file__), "www"),
                static_path=os.path.join(os.path.dirname(__file__), "www"),
                static_url_prefix="include/",
                xsrf_cookies=False,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class Th(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.app = Application

    def run(self):
        tornado.options.define("port", default=self.port, help="run on the given port", type=int)
        self.__set_log_level_tornado()
        app = self.app()
        app.listen(tornado.options.options.port)
        log.info("Web server started on port %s" % self.port)
        tornado.ioloop.IOLoop.instance().start()

    def __set_log_level_tornado(self):
        tornado.log.access_log.setLevel(log.level[config.log_level])
        tornado.log.app_log.setLevel(log.level[config.log_level])
        tornado.log.gen_log.setLevel(log.level[config.log_level])

    def stop(self):
        tornado.ioloop.IOLoop.instance().stop()
        log.info("Web server stopped")


def start_server(port):
    global threadServer, clientsList
    # Initialization
    clientsList = UserList()
    # Start tornado server
    threadServer = Th(port)
    threadServer.run()


def stop():
    global threadServer, clientsList
    clientsList.destroy()
    threadServer.stop()
