(function () {

    angular.module('graph')
        .controller('GraphController', [
            '$scope', '$window',
            'hotkeys',
            'GraphManager', 'SettingService', 'PageService', 'ChannelService',
            GraphController]);

    function GraphController($scope, $window, hotkeys, gm, ss, page, cs) {

        var gc = {

            node: function() {
                return gm.selected.node;
            },

            packet: function() {
                return gm.selected.packet;
            },
            
            panel_fixed: function () {
                return gm.panel.fixed;
            },

            get_data: function (name) {
                return gm[name].graph;
            },

            display: function (name) {
                return gm[name].display;
            },

            setNode: function (node) {
                if (!gm.panel.fixed)
                    gm.selected.node = node;
            },

            displayDataPacket: function (data) {
                if (!gm.panel.fixed)
                    gm.selected.packet = data;
            },

            getHeight: function (name) {
                switch (name) {
                    case 'timeline':
                        return gm.timeline.height;
                    case 'network':
                        return $window.innerHeight - gm.timeline.height - 16;
                }
                return 0;
            },

            getWidth: function () {
                return $window.innerWidth;
            },

            newPacket: function (clean) {
                // Display loading process
                page.load.display();
                // Clean old packets
                if (clean) {
                    gm.timeline.graph.clean();
                    gm.data.path = null;
                }
                // Get new packets
                gm.packet.request(clean);
                // Close the loading process
                page.load.hidden();
            },

            setRealTime: function () {
                // Enable or disable real-time packet display
                gm.packet.realtime();
            },

            timelineLoading: function () {
                return gm.packet.loading;
            },

            timeline: {
                needRefresh: function () {
                    return gm.timeline.state == "need-refresh";
                },
                refresh: function () {
                    gc.refresh_action(false);
                    gm.timeline.state = "refreshing";
                }
            },

            refresh_action: function(dbclick) {
                if (dbclick) {
                    gc.setRealTime();
                    return;
                }
                if (gc.isRealTime()) {
                    gc.setRealTime();
                    return;
                }
                gc.newPacket(true);
            },

            isRealTime: function () {
                return gm.timeline.realTime;
            },

            showSetting: function (section) {
                ss.display = !ss.display;
                if (!section) {
                    return;
                }
                ss.menu.selected = section;
            },

            filter: function () {
                return ss.protocols;
            },

            connectMgt: function (node_key, remote_conn, status) {
                gm.timeline.display = false;
                gm.timeline.state = "need-refresh";
                // Loading progress
                page.load.display();
                cs.network.callbacks['loading'] = function () {
                    cs.network.callbacks['loading'] = null;
                    page.load.hidden();
                };
                // Hidden panel info
                gm.panel.close();
                // Update connectivity
                gm.network.config.connectivity(node_key, remote_conn, status);
            }

        };

        // Define some shortcut
        hotkeys.bindTo($scope)
            .add({
                combo: 'r',
                description: 'Refresh the timeline',
                callback: function() {
                    gc.newPacket(true);
                }
            })
            .add({
                combo: 'f',
                description: 'Open filter panel',
                callback: function() {
                    gc.showSetting('filter');
                }
            })
            .add({
                combo: 's',
                description: 'Open search panel',
                callback: function() {
                    gc.showSetting('search');
                }
            })
            .add({
                combo: 'space',
                description: 'Play the realtime check',
                callback: function() {
                    gc.setRealTime();
                }
            });
        

        return gc;
    }
})();
