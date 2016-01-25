(function () {

    angular.module('app')
        .controller('AlertController', ['PageService', AlertController]);

    function AlertController(page) {
        this.show = function () {
            return page.alert.data != null;
        };

        this.txt = function () {
            return this.show() ? page.alert.data.txt : '';
        };

        this.class = function () {
            return this.show() ? page.alert.data.type : '';
        };

        this.close = function () {
            page.alert.data = null;
        }
    }
})();