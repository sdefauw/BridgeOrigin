(function () {

    angular.module('app')
        .factory('PageService', [PageService]);

    function PageService() {

        var page = {
            alert: {
                data: null,
                info: function (txt) {
                    page.alert.data = {
                        type: 'info',
                        txt: txt
                    };
                },
                warning: function (txt) {
                    page.alert.data = {
                        type: 'warning',
                        txt: txt
                    };
                },
                error: function (txt) {
                    page.alert.data = {
                        type: 'error',
                        txt: txt
                    };
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
            }
        };

        return page;
    }

})();