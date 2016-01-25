(function () {

    angular.module('graph')
        .directive('displayInfoDetail', ["$http", 'GraphManager', displayInfoDetail]);

    function displayInfoDetail($http, gm) {
        return {
            transclude: true,
            replace: true,
            scope: {
                uuid: "="
            },
            link: function ($scope, $elem) {
                $scope.$watch('uuid', function (uuid) {
                    $elem.html('');
                    if (!uuid) return;
                    $http({
                        method: 'GET',
                        url: "packet",
                        params: {
                            uuid: uuid,
                            network: gm.uuid
                        }
                    })
                        .then(function (result) {
                            $elem.html(result.data);
                        });
                });
            }
        }
    }
})();