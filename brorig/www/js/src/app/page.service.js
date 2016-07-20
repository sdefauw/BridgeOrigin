(function () {

    angular.module('app')
        .factory('PageService', ['GraphManager', 'SettingService', PageService]);

    function PageService(gm, ss) {

        var page = {
            alert: {
                data: null,
                info: function (txt) {
                    page.alert.data = {
                        type: 'info',
                        txt: txt
                    };
                    console.info(txt);
                },
                warning: function (txt) {
                    page.alert.data = {
                        type: 'warning',
                        txt: txt
                    };
                    console.warn(txt);
                },
                error: function (txt) {
                    page.alert.data = {
                        type: 'error',
                        txt: txt
                    };
                    console.error(txt);
                }
            },
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