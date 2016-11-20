(function () {

    angular.module('graph')
        .factory('SettingService', ['$http', 'ChannelService', SettingService]);

    function SettingService($http, cs) {

        var ss = {
            protocols: {},
            display: false,
            search: {
                filter: {
                    time: {
                        from: null,
                        to: null,
                        interval: function () {
                            if (ss.search.filter.time.from < 0 && !ss.search.filter.time.to) {
                                return {
                                    'from': new Date((new Date()).getTime() + ss.search.filter.time.from * 1000),
                                    'to': new Date()
                                };
                            }
                            if (ss.search.filter.time.from >= ss.search.filter.time.to) {
                                return null;
                            }
                            return {
                                'from': ss.search.filter.time.from,
                                'to': ss.search.filter.time.to
                            };
                        }
                    },
                    match: null
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