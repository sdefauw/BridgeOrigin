(function () {

    angular.module('graph')
        .controller('GraphController', [
            '$scope', '$window', "$http", "$timeout",
            'hotkeys',
            'GraphManager', 'SettingService', 'ServerSelectorService', 'PageService',
            GraphController]);

    function GraphController($scope, $window, $http, $timeout, hotkeys, gm, ss, sss, page) {

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

            load: function () {
                if (sss.serverkeySelected().length == 0) {
                    $timeout(function () {
                        gc.load(1);
                    }, 1000);
                    return;
                }
                var cacheID = sss.storage.getId();
                if (cacheID) {
                    $http.get('parse?cache=' + cacheID + '&serverkeys=' + sss.serverkeySelected().join(','))
                        .success(function (data) {
                            // Check error
                            if (data.error) {
                                console.log(data.error);
                                return;
                            }
                            // Load data file
                            gm.network.path = data.network;
                            gm.timeline.path = data.timeline;
                            gm.data.path = data.datapath;
                            page.alert.info('Use cache information');
                        });
                }
            },

            new_packets: function (clean, play) {
                // Display loading process
                page.load.display();
                // Clean old packets
                if (clean) {
                    gm.timeline.graph.packets = [];
                    gm.data.path = null;
                }
                // Get new packets
                sss.packetsRequest(play);
                // Close the loading process
                page.load.hidden();
            },

            isRealTime: function () {
                return gm.timeline.realTime;
            },

            showSetting: function () {
                ss.display = !ss.display;
            },

            filter: function () {
                return ss.protocols;
            }
        };

        // Define some shortcut
        hotkeys.bindTo($scope)
            .add({
                combo: 'r',
                description: 'Refresh the timeline',
                callback: function() {
                    gc.new_packets(true);
                }
            })
            .add({
                combo: 'f',
                description: 'Open filter panel',
                callback: function() {
                    gc.showSetting();
                }
            });
        

        return gc;
    }
})();
