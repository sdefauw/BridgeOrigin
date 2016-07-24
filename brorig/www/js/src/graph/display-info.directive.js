(function () {

    angular.module('graph')
        .directive('displayInfoDetail', ["$http", 'ChannelService', displayInfoDetail]);

    function displayInfoDetail($http, cs) {
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
                            network: cs.client.data.uuid
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