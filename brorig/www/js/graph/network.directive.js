(function () {

    angular.module('graph')
        .directive('networkGraph', ['$window', 'GraphManager', NetworkGraph]);

    function NetworkGraph($window, gm) {

        var color = d3.scale.category10();
        var listener = {node: {}};
        var svg;

        function build(graph, scope, elem) {

            if (graph.nodes.length == 0) return;

            console.debug("Rebuild network graph: %d nodes and %d links", graph.nodes.length, graph.links.length);

            var width = scope.width;
            var height = scope.height;

            var force = d3.layout.force()
                .charge(-2000)
                .linkDistance(75)
                .size([width, height]);


            svg = d3.select(elem).append("svg")
                .attr("width", width)
                .attr("height", height)
                .attr("class", "network");


            graph.links.forEach(function (item) {
                item.source = parseInt(item.source);
                item.target = parseInt(item.target);
            });

            gm.network.graph = graph;

            force
                .nodes(graph.nodes)
                .links(graph.links)
                .linkDistance(200)
                .alpha(0.1)
                .start();

            var path = svg.append("g").selectAll("path")
                .data(graph.links)
                .enter().append("path");

            svg.append("defs").selectAll("marker")
                .data(["suit"])
                .enter().append("marker")
                .attr("id", function (d) {
                    return d;
                })
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 30)
                .attr("refY", 0)
                .attr("markerWidth", 10)
                .attr("markerHeight", 10)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5");

            var drag = force.drag()
                .on("dragstart", function (d) {
                    d3.select(this).classed("fixed", d.fixed = true);
                });

            var node = svg.selectAll(".node")
                .data(graph.nodes)
                .enter().append("g")
                .attr("class", "node")
                .on("contextmenu", function (d) {
                    d3.select(this).classed("fixed", d.fixed = false);
                })
                .call(drag);

            node.append("rect")
                .attr("x", -50)
                .attr("y", -10)
                .attr("width", 100)
                .attr("height", 20)
                .attr("rx", 10)
                .style("fill", function (d) {
                    return color(d.cluster);
                })
                .style("stroke", function (d) {
                    return color(d.cluster);
                });

            node.append("text")
                .attr("dy", ".35em")
                .text(function (d) {
                    return d.name;
                });

            for (var l in listener.node) {
                node.on(l, (function (l) {
                    return function (d) {
                        listener.node[l](d);
                    }
                })(l));
            }

            force.on("tick", function () {

                path.attr("d", function (d) {
                    return "M" + d.source.x + "," + d.source.y + "L" + d.target.x + "," + d.target.y;
                });

                node.attr("transform", function (d) {
                    return "translate(" + d.x + "," + d.y + ")";
                });
            });


        }

        function remove(elem) {
            elem.innerHTML = "";
        }

        function nodeList(event, fct) {
            listener['node'][event] = fct;
        }

        return {
            restrict: 'EA',
            scope: {
                data: '=',
                width: '=',
                height: '=',
                selectedNode: "&"
            },
            link: function (scope, elem, attrs) {
                scope.$watch('data', function (value) {
                    if (value && Object.keys(value).length > 0) {
                        nodeList('mouseover', function (d) {
                            scope.$apply(function () {
                                scope.selectedNode({node: d});
                            });
                        });
                        nodeList('mouseout', function (d) {
                            scope.$apply(function () {
                                scope.selectedNode({node: null});
                            });
                        });
                        nodeList('dblclick', function (d) {
                            scope.$apply(function () {
                                gm.panel.fixed = true;
                                scope.selectedNode({node: d});
                            });
                        });
                        if (value.nodes && value.nodes.length > 0) {
                            build(value, scope, elem[0]);
                        }
                    } else {
                        remove(elem[0]);
                    }
                });

                scope.$watch('width', function (value) {
                    if (svg)
                        svg.attr('width', value);
                });

                scope.$watch('height', function (value) {
                    if (svg)
                        svg.attr('height', value);
                });

                angular.element($window).bind('resize', function () {
                    scope.$apply();
                });
            }
        };
    }
})();