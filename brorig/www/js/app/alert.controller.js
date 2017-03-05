(function () {

    angular.module('app')
        .controller('AlertController', ['AlertService', AlertController]);

    function AlertController(al) {

        var ac = {
            show: function () {
                return al.data != null;
            },

            txt: function () {
                return ac.show() ? al.data.txt : '';
            },

            class: function () {
                return ac.show() ? al.data.type : '';
            },

            close: function () {
                al.data = null;
            }
        };

        return ac;
    }
})();