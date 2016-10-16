(function () {

    angular.module('graph')
        .controller('DisplayInfoController', ['GraphManager', DisplayInfoController]);

    function DisplayInfoController(gm) {

        var dic = {
            close: function () {
                gm.panel.close();
            },
            show: function () {
                return gm.panel.fixed || gm.selected.node != null || gm.selected.packet != null;
            },
            fullScreen: function () {
                gm.panel.fullScreen = !gm.panel.fullScreen;
            },
            isFullScreen: function () {
                return gm.panel.fullScreen;
            }
        };

        return dic;
    }

})();