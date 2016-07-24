(function () {

    angular.module('app')
        .factory('PageService', ['GraphManager', 'SettingService', PageService]);

    function PageService(gm, ss) {

        var page = {
            load: {
                show: false,
                display: function () {
                    page.load.show = true;
                },
                hidden: function () {
                    page.load.show = false;
                }
            },
            windowsManager: {
                closeAll: function () {
                    gm.panel.close();
                    ss.display = false;
                },
                closeTop: function () {
                    if (ss.display) {
                        ss.display = false;
                    } else  {
                        gm.panel.close();
                    }
                }
            }
        };

        return page;
    }

})();