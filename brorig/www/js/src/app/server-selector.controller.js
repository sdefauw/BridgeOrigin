(function () {

    angular.module('app')
        .controller('ServerSelectorController', [
            '$scope',
            'ServerSelectorService',
            ServerSelectorController]);

    function ServerSelectorController($scope, sss) {

        this.tFilterOptions = [
            {label: '1 min', value: 60},
            {label: '5 min', value: 5 * 60},
            {label: '15 min', value: 15 * 60},
            {label: '30 min', value: 30 * 60},
            {label: '1 h', value: 60 * 60},
            {label: '5 h', value: 5 * 60},
            {label: '10 h', value: 10 * 60},
            {label: 'All log', value: ''}
        ];
        $scope.tfilter = this.tFilterOptions[1];

        this.serversFiltered = null;

        this.servers = function () {
            if (this.serversFiltered == null)
                return sss.servers;
            return this.serversFiltered;
        };

        this.display = function () {
            return sss.display;
        };
        this.close = function () {
            sss.display = false;
        };
        this.open = function () {
            sss.display = true;
        };
        this.process = function () {
            this.close();
            sss.filter.historyTime = $scope.tfilter.value;
            if (!sss.process())
                this.open();
        };
        this.select = function (server) {
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
        };

        this.search = function () {
            var keyword = $scope.searchkeys;
            if (!keyword || keyword == '') {
                this.serversFiltered = sss.servers;
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
            this.serversFiltered = list;
        };
    }
})();