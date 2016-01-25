(function () {

    angular.module('graph')
        .controller('DisplayInfoController', ['$scope', 'GraphManager', DisplayInfoController]);

    function DisplayInfoController($scope, gm) {

        this.close = function () {
            $scope.$parent.node = null;
            $scope.$parent.packet = null;
            gm.panel.fixed = false;
        };

        this.show = function () {
            return gm.panel.fixed || $scope.$parent.node != null || $scope.$parent.packet != null;
        };

    }
})();