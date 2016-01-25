(function () {

    angular.module('app')
        .service('ServerConfigService', ['$http', 'PageService', 'ServerSelectorService', ServerConfigService]);

    function ServerConfigService($http, page, sss) {

        var cl = {
            display: false,

            exe: function (cmd, successfct) {
                var serverkeys = sss.serverkeySelected();
                if (!serverkeys.length) {
                    page.alert.warning("You need to select device !");
                    return;
                }
                // Send XHR request to clean up asterisk log
                $http.get("configure?cmd=" + cmd + "&serverskey=" + serverkeys.join(','))
                    .success(function (data) {
                        successfct(data);
                    })
                    .error(function (data, status) {
                        page.alert.error("Impossible to execute this command log: " + status);
                    });
            }
        };

        return cl;

    }
})();