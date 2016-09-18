(function () {

    angular.module('graph')
        .factory('ChannelService', [
            "$websocket",
            "AlertService",
            ChannelService
        ]);

        function ChannelService($websocket, al) {
        var cs = {

            packet: {
                callbacks: [],
                config: {
                    filter: function (filter) {
                        // TODO
                        console.error("TODO filter");
                    },
                    realTime: function (enable) {
                        ws.send(JSON.stringify({
                            timeline: {
                                play: enable,
                                clean: false
                            }
                        }));
                    }
                },
                request: function (from, to, clean) {
                    ws.send(JSON.stringify({
                        timeline: {
                            clean: !!clean,
                            packet: {
                                from: from,
                                to: to ? to : "now"
                            }
                        }
                    }));
                }
            },
            network: {
                callbacks: [],
                config: {
                    connectivity: function (request_list) {
                        ws.send(JSON.stringify({
                            network: [
                                {connect_mgt: request_list}
                            ]
                        }));
                    }
                },
                request: function (server_list) {
                    ws.send(JSON.stringify({
                        network: [
                            {clean: true},
                            {add_nodes: server_list}
                        ]
                    }));
                }
            },
            client: {
                data: {},
                callbacks: [function (data) {
                    cs.client.data.uuid = data.uuid;
                }]
            }
        };

        var callbackHandler = {
            detail: cs.client.callbacks,
            network: cs.network.callbacks,
            packets: cs.packet.callbacks
        };

        var ws = $websocket("ws://" + window.location.host + "/ws/network");

        ws.onOpen(function () {
            console.debug("WebSocket open");
        });

        ws.onClose(function () {
            al.error("Connection lost.");
        });

        ws.onMessage(function (evt) {
            var data = JSON.parse(evt.data);
            for (var cmd in data) {
                if (callbackHandler[cmd]) {
                    var handlers = callbackHandler[cmd];
                    var args = data[cmd];
                    for (var i in handlers) {
                        handlers[i](args);
                    }
                }
            }
        });

        return cs;
    }

})();