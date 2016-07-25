(function () {

    angular.module('graph')
        .controller('DisplayInfoController', ['GraphManager', DisplayInfoController]);

    function DisplayInfoController(gm) {

        this.close = function () {
            gm.panel.close();
        };

        this.show = function () {
            return gm.panel.fixed || gm.selected.node != null || gm.selected.packet != null;
        };

    }
})();