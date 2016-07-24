(function () {

    angular.module('graph')
        .factory('GraphManager', [
            "SettingService", "ChannelService",
            GraphManager]);

    function GraphManager(ss, cs) {

        var gm =  {
            data: {
                path: null
            },
            network: {
                path: null,
                graph: {
                    nodes: [],
                    links: []
                },
                update: function (server_list) {
                    // Clean graph
                    gm.network.graph = {};
                    gm.timeline.graph = {
                        lanes: [],
                        packets: []
                    };
                    // Hidden timeline graph, no relevant anymore
                    gm.timeline.display = false;
                    // Ask network graph
                    cs.network.request(server_list);
                }
            },
            packet: {
                request: function (clean) {
                    var now = new Date() - 0;
                    var from = now - ss.search.filter.historyTime * 1000;
                    cs.packet.request(from, now, clean);
                },
                realtime: function () {
                    gm.timeline.realTime = !gm.timeline.realTime;
                    cs.packet.config.realTime(gm.timeline.realTime);
                }
            },
            timeline: {
                path: null,
                height: 0,
                display: false,
                graph: {
                    lanes: [],
                    packets: []
                },
                realTime: false
            },
            panel: {
                fixed: false,
                close: function () {
                    gm.selected.node = null;
                    gm.selected.packet = null;
                    gm.panel.fixed = false;
                }
            },
            selected: {
                node: null,
                packet: null
            }
        };

        cs.network.callbacks.push(function (data) {
            // Update graph data
            gm.network.graph = data;
            // Display timeline graph
            gm.timeline.display = true;
        });

        cs.packet.callbacks.push(function (data) {
            // Only add new packets and update already in the timeline
            var num_packet = gm.timeline.graph.packets.length;
            var old_data = gm.timeline.graph.packets.filter(function (item) {
                for (var i in data) {
                    var packet = data[i];
                    if (packet.uuid == item.uuid) return false;
                }
                return true;
            });
            gm.timeline.graph.packets = old_data.concat(data);
            console.info('Add %d and update %d packets in the timeline graph (old:%d, recv:%d, tot:%d)',
                data.length-(num_packet-old_data.length), num_packet-old_data.length,
                old_data.length, data.length, gm.timeline.graph.packets.length);
        });

        return gm;
    }
})();