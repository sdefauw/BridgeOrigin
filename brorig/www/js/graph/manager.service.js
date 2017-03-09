(function () {

    angular.module('graph')
        .factory('GraphManager', [
            "SettingService", "ChannelService", 'AlertService',
            GraphManager]);

    function GraphManager(ss, cs, al) {

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
                config: {
                    connectivity: function (node_key, remote_conn, status) {
                        // Clean graph
                        gm.network.graph = {};
                        // TODO timeline
                        // Ask to update the connectivity
                        cs.network.config.connectivity([
                            {
                                node: node_key,
                                remote_conn: remote_conn,
                                status: status
                            }
                        ]);
                    }
                },
                update: function (server_list) {
                    // Clean graph
                    gm.network.graph = {};
                    gm.timeline.graph.clean(true);
                    // Hidden timeline graph, no relevant anymore
                    gm.timeline.display = false;
                    // Ask network graph
                    cs.network.request(server_list);
                }
            },
            packet: {
                loading: false,
                request: function (clean) {
                    var interval = ss.search.filter.time.interval();
                    if (!interval) {
                        al.error("Invalid time interval selected");
                        return;
                    }
                    gm.packet.loading = true;
                    // TODO unify time and match
                    cs.packet.config.filter = ss.search.filter.match;
                    cs.packet.request(interval.from.getTime(), interval.to.getTime(), clean);
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
                state: null,
                graph: {
                    lanes: [],
                    packets: {
                        set: [],
                        groups: []
                    },
                    clean: function (all) {
                      gm.timeline.graph.packets = {
                          set: [],
                          groups: []
                      };
                      if (all)
                        gm.timeline.graph.lanes = [];
                    }
                },
                realTime: false
            },
            panel: {
                fixed: false,
                fullScreen: false,
                close: function () {
                    gm.selected.node = null;
                    gm.selected.packet = null;
                    gm.panel.fixed = false;
                    gm.panel.fullScreen = false;
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
            if (data.set) {
                // Only add new packets and update already in the timeline
                var num_packet = gm.timeline.graph.packets.set.length;
                var old_data = gm.timeline.graph.packets.set.filter(function (item) {
                    for (var i in data.set) {
                        var packet = data.set[i];
                        if (packet.uuid == item.uuid) return false;
                    }
                    return true;
                });
                gm.timeline.graph.packets.set = old_data.concat(data.set);
                console.info('Add %d and update %d packets in the timeline graph (old:%d, recv:%d, tot:%d)',
                    data.set.length-(num_packet-old_data.length), num_packet-old_data.length,
                    old_data.length, data.set.length, gm.timeline.graph.packets.set.length);
                gm.packet.loading = false;
                gm.timeline.state = "updated";
            }
            if (data.groups) {
                gm.timeline.graph.packets.groups = data.groups
            }
        });

        return gm;
    }
})();