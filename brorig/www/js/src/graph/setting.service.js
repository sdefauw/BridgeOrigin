(function () {

    angular.module('graph')
        .factory('SettingService', ['$http', SettingService]);

    function SettingService($http) {

        var ss = {
            protocols: {},
            display: false
        };

        $http.get("protocol").success(function (data) {
            ss.protocols = data;
            // Set default filters
            for (var protocol in ss.protocols) {
                var protocolObj = ss.protocols[protocol];
                if (!protocolObj.filter) continue;
                ss.protocols[protocol].selected = protocolObj.filter;
            }
        });

        return ss;
    }
})();