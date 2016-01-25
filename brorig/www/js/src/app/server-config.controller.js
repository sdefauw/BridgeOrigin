(function () {

    angular.module('app')
        .controller('ServerConfigController', ['ServerConfigService', ServerConfigController]);

    function ServerConfigController(serverconfig) {

        this.inProcess = '';

        this.display = function () {
            return serverconfig.display;
        };

        this.close = function () {
            serverconfig.display = false;
        };

        this.exe = function (cmd) {
            if (this.inProcess != '') {
                return;
            }
            this.inProcess = cmd;
            var self = this;
            serverconfig.exe(cmd, function (d) {
                self.inProcess = '';
            })
        }

    }
})();