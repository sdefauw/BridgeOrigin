(function () {

    angular.module('app')
        .service('ServerSelectorService', [
            '$http', '$websocket',
            'PageService', 'GraphManager', 'SettingService',
            ServerSelectorController]);

    function ServerSelectorController($http, $websocket, page, gm, ss) {

        var sss = {
            display: true,
            servers: [],
            lastNetwork: null,

            select: function () {
            },

            serverkeySelected: function () {
                var list = [];
                for (var i in this.servers) {
                    if (this.servers[i].selected) {
                        list.push(this.servers[i].key);
                    }
                }
                return list;
            },

            network: function () {
                sss.lastNetwork = sss.serverkeySelected();
                // Clean graph
                gm.network.graph = {};
                gm.timeline.graph = {
                    lanes: [],
                    packets: []
                };
                gm.timeline.display = false;
                // Ask network graph
                ws.send(JSON.stringify({
                    network: sss.lastNetwork
                }));
            },

            packetsRequest: function () {
                var startTime = ss.search.filter.historyTime;
                var stopTime = null;
                // Query packets with filers
                ws.send(JSON.stringify({
                    timeline: {
                        time: {
                            start: startTime,
                            stop: stopTime
                        },
                        clean: true
                    }
                }));
            },

            process: function () {
                var serverlist = sss.serverkeySelected();
                if (!serverlist.length) {
                    page.alert.warning("You need to select server !");
                    return false;
                }

                // Display loading process
                page.load.display();

                // Callback functions
                if (!sss.lastNetwork) {
                    // Ask packets
                    callbackHandler.network.push(function () {
                        sss.packetsRequest();
                        //TODO sss.storage.setId(id);
                    });

                    // Close all
                    callbackHandler.packets.push(function () {
                        page.load.hidden();
                    });
                }

                // Ask network
                sss.network();

                return true;
            },

            storage: {
                setId: function (id) {
                    sessionStorage.parcingid = id;
                },
                getId: function () {
                    return sessionStorage.parcingid;
                },
                getServerkeys: function () {
                    if (!sessionStorage.serverkeyselected) return [];
                    return sessionStorage.serverkeyselected.split(',');
                },
                addServerkey: function (serverkey) {
                    var list = sss.storage.getServerkeys();
                    if (list.indexOf('' + serverkey) != -1) return;
                    list.push(serverkey);
                    sessionStorage.serverkeyselected = list;
                },
                rmServerkey: function (serverkey) {
                    var list = sss.storage.getServerkeys();
                    if (list.indexOf('' + serverkey) == -1) return;
                    list.splice(list.indexOf('' + serverkey), 1);
                    sessionStorage.serverkeyselected = list;
                }
            }
        };

        $http.get('server/list')
            .success(function (data) {
                sss.servers = data;
                // Get info form session cache
                var list = sss.storage.getServerkeys();
                for (var i in sss.servers) {
                    var server = sss.servers[i];
                    server.selected = list.indexOf('' + server.key) != -1;
                }
            })
            .error(function (data, status) {
                page.alert.error("Impossible the list of SERVER: " + status);
            });

        var ws = $websocket("ws://" + window.location.host + "/ws/network");

        ws.onOpen(function () {
            console.debug("WebSocket open");
        });

        ws.onClose(function () {
            page.alert.error("Connection lost.");
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

        var networkDetailCallback = function (data) {
            gm.uuid = data.uuid;
        };

        var networkCallback = function (data) {
            gm.network.graph = data;
            gm.timeline.display = true;
        };

        var packetsCallback = function (data) {
            console.info('Add %d packets in the timeline graph', data.length);
            gm.timeline.graph.packets = gm.timeline.graph.packets.concat(data);
        };

        var callbackHandler = {
            "detail": [networkDetailCallback],
            "network": [networkCallback],
            "packets": [packetsCallback]
        };


        return sss;
    }
})();