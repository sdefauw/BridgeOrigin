#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function

import datetime
import json
import os
import threading

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
from brorig.processor import TimelinePacketProcessHelper, NetworkProcess
from brorig.user import User, UserList

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
