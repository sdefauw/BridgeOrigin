(function () {

    angular.module('graph')
        .controller('DisplayInfoController', ['GraphManager', DisplayInfoController]);

    function DisplayInfoController(gm) {

        this.close = function () {
            gm.selected.node = null;
            gm.selected.packet = null;
            gm.panel.fixed = false;
        };

        this.show = function () {
            return gm.panel.fixed || gm.selected.node != null || gm.selected.packet != null;
        };

    }
})();