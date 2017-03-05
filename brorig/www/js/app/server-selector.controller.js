(function () {

    angular.module('app')
        .controller('ServerSelectorController', [
            '$scope',
            'ServerSelectorService', 'PageService',
            ServerSelectorController]);

    function ServerSelectorController($scope, sss, ps) {

        var ssc = {
            serversFiltered: null,

            servers: function () {
                if (ssc.serversFiltered == null)
                    return sss.servers;
                return ssc.serversFiltered;
            },

            display: function () {
                return sss.display;
            },

            close: function () {
                sss.display = false;
            },

            open: function () {
                sss.display = true;
            },

            process: function () {
                ssc.close();
                ps.windowsManager.closeAll();
                if (!sss.process())
                    ssc.open();
            },

            select: function (server) {
                for (var i in sss.servers) {
                    if (sss.servers[i].key == server.key) {
                        sss.servers[i].selected = !sss.servers[i].selected;
                        if (sss.servers[i].selected)
                            sss.storage.addServerkey(server.key);
                        else
                            sss.storage.rmServerkey(server.key);
                        return;
                    }
                }
            },

            search: function () {
                var keyword = $scope.searchkeys;
                if (!keyword || keyword == '') {
                    ssc.serversFiltered = sss.servers;
                    return;
                }
                var keywords = keyword.split(" ");
                var list = [];
                sss.servers.forEach(function (item) {
                    var s = item.key + " " + item.name + " " + item.group;
                    var d = false;
                    keywords.forEach(function (keyword) {
                        var re = new RegExp(keyword, "i");
                        if (!re.test(s))
                            d = true;
                    });
                    if (!d)
                        list.push(item);
                });
                ssc.serversFiltered = list;
            }

        };

        return ssc;
    }
})();