(function () {

    angular.module('app')
        .factory('AlertService', [AlertService]);

    function AlertService() {

        var alert = {
            data: null,
            info: function (txt) {
                alert.data = {
                    type: 'info',
                    txt: txt
                };
                console.info(txt);
            },
            warning: function (txt) {
                alert.data = {
                    type: 'warning',
                    txt: txt
                };
                console.warn(txt);
            },
            error: function (txt) {
                alert.data = {
                    type: 'error',
                    txt: txt
                };
                console.error(txt);
            }
        };

        return alert;
    }

})();