(function () {

    angular.module('app')
        .service('ServerSelectorService', [
            '$http',
            'PageService', 'AlertService', 'GraphManager', 'ChannelService',
            ServerServiceController]);

    function ServerServiceController($http, page, al, gm, cs) {

        var sss = {
            display: true,
            servers: [],

            select: function () {
            },

            serverKeySelected: function () {
                var list = [];
                for (var i in this.servers) {
                    if (this.servers[i].selected) {
                        list.push(this.servers[i].key);
                    }
                }
                return list;
            },

            process: function () {
                var server_list = sss.serverKeySelected();
                if (!server_list.length) {
                    al.warning("You need to select server !");
                    return false;
                }
                // Request packet when the network is loaded
                cs.network.callbacks["update_timeline"] = function () {
                    cs.network.callbacks["update_timeline"] = null;
                    gm.packet.request(true);
                    gm.timeline.state = "refreshing";
                };
                // Loading progress
                page.load.display();
                cs.network.callbacks['loading'] = function () {
                    cs.network.callbacks['loading'] = null;
                    page.load.hidden();
                };
                // Ask to load the network graph
                gm.network.update(server_list);
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
                al.error("Impossible the list of SERVER: " + status);
            });


        return sss;
    }
})();