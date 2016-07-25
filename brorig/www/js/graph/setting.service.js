(function () {

    angular.module('graph')
        .factory('SettingService', ['$http', 'ChannelService', SettingService]);

    function SettingService($http, cs) {

        var ss = {
            protocols: {},
            display: false,
            search: {
                filter: {
                    historyTime: 5*60
                }
            }
        };

        cs.network.callbacks.push(function () {
            $http.get("protocol", {
                params: {
                    clientID: cs.client.data.uuid
                }
            }).success(function (data) {
                ss.protocols = data;
                // Set default filters
                for (var protocol in ss.protocols) {
                    var protocolObj = ss.protocols[protocol];
                    if (!protocolObj.filter) continue;
                    ss.protocols[protocol].selected = protocolObj.filter;
                }
            });
        });

        return ss;
    }
})();