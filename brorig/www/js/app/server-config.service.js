(function () {

    angular.module('app')
        .service('ServerConfigService', ['$http', 'AlertService', 'ServerSelectorService', ServerConfigService]);

    function ServerConfigService($http, al, sss) {

        var cl = {
            display: false,

            configure: {
                exe: function (callback) {
                    var serverkeys = sss.serverKeySelected();
                    if (!serverkeys.length) {
                        al.warning("You need to select servers !");
                        return;
                    }
                    var req = {
                        method: 'PUT',
                        url: 'configure/sniffer',
                        data: {
                            serverskey: serverkeys,
                            enable: cl.configure.status != "ON"
                        }
                    };
                    cl.configure.status = "...";
                    $http(req)
                        .then(function (data) {
                            cl.configure.update_status();
                            callback(data);
                        }, function (data, status) {
                            al.error("Impossible to configure sniffers");
                        });
                },
                
                status: '...',
                update_status: function () {
                    var serverkeys = sss.serverKeySelected();
                    if (!serverkeys.length) {
                        return;
                    }
                    cl.configure.status = "...";
                    $http.get('configure/sniffer', {
                            params: {
                                serverskey: serverkeys.join()
                            }
                        })
                        .then(function (res) {
                            var data = res.data;
                            var sniff_off = data.filter(function(item) {
                                return !item.enable;
                            });
                            if (sniff_off.length == data.length) {
                                cl.configure.status = "OFF";
                            } else if(sniff_off.length == 0) {
                                cl.configure.status = "ON";
                            } else {
                                cl.configure.status = "MIX";
                            }
                        }, function (err) {
                            al.error("Impossible to get sniffer configuration status");
                        });
                }
            },

            cleanup: function (callback) {
                var serverkeys = sss.serverKeySelected();
                if (!serverkeys.length) {
                    al.warning("You need to select servers !");
                    return;
                }
                var req = {
                    method: 'DELETE',
                    url: 'configure/sniffer',
                    data: {serverskey: serverkeys}
                };
                $http(req)
                    .then(function (res) {
                        callback(res.data);
                    }, function (err) {
                        al.error("Fail to clean sniffers");
                    });
            }
        };

        return cl;

    }
})();