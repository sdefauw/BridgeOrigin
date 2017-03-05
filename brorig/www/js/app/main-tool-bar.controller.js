(function () {

    angular.module('app')
        .controller('MainToolBarController', [
            'ServerConfigService', 'ServerSelectorService', MainToolBarController]);

    function MainToolBarController(ServerConfig, sss) {
        var tab;

        var mtb = {

            serverConfig: function () {
                tab = 'config';
                ServerConfig.display = !ServerConfig.display;
                if (ServerConfig.display) {
                    ServerConfig.configure.update_status();
                }
            },

            selectServer: function () {
                tab = 'serverselect';
                sss.display = !sss.display;
            },

        };

        return mtb;
    }
})();