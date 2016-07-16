(function () {

    angular.module('app')
        .controller('ServerConfigController', ['ServerConfigService', ServerConfigController]);

    function ServerConfigController(serverconfig) {

        var scc = {
            config: {
                exe: function () {
                    exe(scc.config, serverconfig.configure.exe);
                },
                status: function () {
                    return serverconfig.configure.status;
                },
                inProgress: false
            },

            cleanup: {
                exe: function () {
                    exe(scc.cleanup, serverconfig.cleanup);
                },
                inProgress: false
            },

            display: function () {
                return serverconfig.display;
            },

            close: function () {
                serverconfig.display = false;
            }
        };

        function exe(obj, exe) {
            if (obj.inProgress) {
                return;
            }
            obj.inProgress = true;
            exe(function (d) {
                obj.inProgress = false;
            });
        }

        return scc;

    }
})();