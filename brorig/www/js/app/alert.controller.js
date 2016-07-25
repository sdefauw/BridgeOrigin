(function () {

    angular.module('app')
        .controller('AlertController', ['AlertService', AlertController]);

    function AlertController(al) {
        this.show = function () {
            return al.data != null;
        };

        this.txt = function () {
            return this.show() ? al.data.txt : '';
        };

        this.class = function () {
            return this.show() ? al.data.type : '';
        };

        this.close = function () {
            al.data = null;
        }
    }
})();