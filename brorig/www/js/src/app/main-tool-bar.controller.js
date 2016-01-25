(function () {

    angular.module('app')
        .controller('MainToolBarController', [
            '$scope',
            'ServerConfigService', 'ServerSelectorService', MainToolBarController]);

    function MainToolBarController($scope, ServerConfig, sss) {
        var tab;

        $scope.back_button = history.length > 1;

        $scope.seTab = function (newValue) {
            tab = newValue;
        };

        $scope.isSet = function (tabName) {
            return tab === tabName;
        };

        $scope.serverConfig = function () {
            tab = 'config';
            ServerConfig.display = !ServerConfig.display;
        };

        $scope.selectSERVER = function () {
            tab = 'serverselect';
            sss.display = !sss.display;
        };

        $scope.refresh = function () {
            tab = 'refresh';
            sss.process();
        }
    }
})();