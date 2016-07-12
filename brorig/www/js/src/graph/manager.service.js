(function () {

    angular.module('graph')
        .factory('GraphManager', GraphManager);

    function GraphManager() {
        return {
            uuid: null,
            data: {
                path: null
            },
            network: {
                path: null,
                graph: {
                    nodes: [],
                    links: []
                }
            },
            timeline: {
                path: null,
                height: 0,
                display: false,
                graph: {
                    lanes: [],
                    packets: []
                }
            },
            panel: {
                fixed: false
            },
            selected: {
                node: null,
                packet: null,
            }
        }
    }
})();