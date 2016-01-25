(function () {

    angular.module('graph')
        .controller('GraphController', [
            '$scope', '$window', "$http", "$timeout",
            'GraphManager', 'SettingService', 'ServerSelectorService', 'PageService',
            GraphController]);

    function GraphController($scope, $window, $http, $timeout, gm, ss, sss, page) {

        $scope.panel_fixed = function () {
            return gm.panel.fixed;
        };

        $scope.get_data = function (name) {
            $scope.data = gm[name].graph;
            return $scope.data;
        };

        $scope.display = function (name) {
            return gm[name].display;
        };

        $scope.setNode = function (node) {
            if (!gm.panel.fixed)
                $scope.node = node;
        };

        $scope.displayDataPacket = function (data) {
            if (!gm.panel.fixed)
                $scope.packet = data;
        };

        $scope.getHeight = function (name) {
            switch (name) {
                case 'timeline':
                    return gm.timeline.height;
                case 'network':
                    return $window.innerHeight - gm.timeline.height - 16;
            }
            return 0;
        };

        $scope.getWidth = function () {
            return $window.innerWidth;
        };

        $scope.load = function (t) {
            if (t > 1) return;
            if (sss.serverkeySelected().length == 0) {
                $timeout(function () {
                    $scope.load(1);
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
        };

        $scope.showSetting = function () {
            ss.display = !ss.display;
        };

        $scope.filter = function () {
            return ss.protocols;
        };
    }
})();