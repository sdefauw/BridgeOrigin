(function () {

    angular.module('app')
        .controller('PageController', ['$scope', 'PageService', 'hotkeys', PageController]);

    function PageController($scope, ps, hotkeys) {

        var pc = {
            
        };

        // Define some shortcut
        hotkeys.bindTo($scope)
            .add({
                combo: 'esc',
                description: 'Refresh the timeline',
                callback: function() {
                    ps.windowsManager.closeTop();
                }
            });

        return pc;
    }
})();