(function () {

    angular.module('graph')
        .directive('timelineGraph', ['GraphManager', 'SettingService', TimelineGraph]);

    function TimelineGraph(gm, ss) {

        var lanes = [];
        var items = [];
        var groups = [];
        var domain;
        var lanesMapping = {};
        var lanesTreeStruct = {};
        var displayNode;
        var filter = [];

        var margin = {top: 0, right: 0, bottom: 10, left: 0};

        var x, y, xAxis, svg, svgg, itemRects;
        var listener = {rect: {}, loaded: null};

        var yMap = function (index) {
            return y(lanesMapping[index]);
        };

        var genLanesMapping = function () {
            var map = [];

            function listUuidSupported(root) {
                if (root.child != undefined) {
                    var list = [];
                    for (var i in root.child) {
                        list = list.concat(listUuidSupported(root.child[i]));
                    }
                    return list;
                }
                return [root.uuid];
            }

            function r(nodes, path) {
                for (var i in nodes) {
                    var node = nodes[i];
                    if (node.visible) {
                        if (node.child == undefined) {
                            map.push({
                                id: path + "." + node.name,
                                node: node,
                                uuidSupported: [node.uuid]
                            });
                        } else {
                            var n = null;
                            for (var j in node.child) n = node.child[j];
                            if (n && n.visible) {
                                r(node.child, path + "." + node.name)
                            } else {
                                map.push({
                                    id: path + "." + node.name,
                                    node: node,
                                    uuidSupported: listUuidSupported(node)
                                });
                            }
                        }
                    }
                }
            }

            //TODO can't have multiple link between same nodes !

            // Serialize the tree with visible node
            r(lanesTreeStruct, '');
            // Sort lanes
            map = map.sort(function (a, b) {
                if (a.id < b.id) return -1;
                if (a.id > b.id) return 1;
                return 0;
            });
            displayNode = map;
            // Define a mapping between uuid and lane position
            lanesMapping = {};
            for (var i in map) {
                for (var j in map[i].uuidSupported) {
                    lanesMapping[map[i].uuidSupported[j]] = parseInt(i);
                }
            }
        };


        var refreshLanes = function (lanesList) {

            // Set struct by default
            lanes = lanesList;
            lanesTreeStruct = {
                nodes: {name: 'Nodes', visible: true, child: {}},
                links: {name: 'Links', visible: true, child: {}}
            };

            // Save data
            gm.timeline.graph.lanes = lanes;

            // Define nodes an links
            var nodes = lanesList.nodes;
            var links = lanesList.links;

            // Process a structure of lanes for each nodes
            for (var i in nodes) {
                var node = nodes[i];
                lanesTreeStruct.nodes.child[node.uuid] = {
                    name: node.name,
                    uuid: node.uuid,
                    visible: false,
                    parent: lanesTreeStruct.nodes
                };
            }

            // Process a structure of lanes for each links
            for (var i in links) {
                var link = links[i];
                var fromNode = link.source;
                var toNode = link.target;

                if (lanesTreeStruct.links.child[fromNode.uuid + toNode.uuid] != undefined) {
                    // Already in the tree (send)
                    lanesTreeStruct.links.child[fromNode.uuid + toNode.uuid].child.send = {
                        name: fromNode.name + " → " + toNode.name,
                        uuid: link.uuid,
                        visible: false,
                        parent: lanesTreeStruct.links.child[fromNode.uuid + toNode.uuid]
                    };
                } else if (lanesTreeStruct.links.child[toNode.uuid + fromNode.uuid] != undefined) {
                    // already in the tree (recv)
                    lanesTreeStruct.links.child[toNode.uuid + fromNode.uuid].child.recv = {
                        name: toNode.name + " ← " + fromNode.name,
                        uuid: link.uuid,
                        visible: false,
                        parent: lanesTreeStruct.links.child[toNode.uuid + fromNode.uuid]
                    };
                } else {
                    // New in node in the tree
                    lanesTreeStruct.links.child[fromNode.uuid + toNode.uuid] = {
                        name: fromNode.name + " ⟷ " + toNode.name,
                        visible: false,
                        child: {
                            send: {
                                name: fromNode.name + " → " + toNode.name,
                                uuid: link.uuid,
                                visible: false
                            },
                            recv: {}
                        },
                        parent: lanesTreeStruct.links
                    };
                    var n = lanesTreeStruct.links.child[fromNode.uuid + toNode.uuid];
                    n.child.send.parent = n;
                }
            }

            // Generate svg from the lanes definition
            genLanesMapping();
        };

        var addPackets = function (list) {
            for (var i in list) {
                var packet = list[i];
                // Timestamp [ms]
                var timestamp = {
                    end: Math.floor(packet.end),
                    start: Math.ceil(packet.start)
                };
                packet.start = new Date(timestamp.start);
                if (!packet.end) {
                    packet.end = new Date(timestamp.start);
                    packet.end.setMilliseconds(packet.end.getMilliseconds() + 1);
                    packet.status = "lost";
                } else {
                    packet.end = new Date(timestamp.end);
                    packet.status = "arrived";
                    if (timestamp.end == timestamp.start) {
                        packet.end.setMilliseconds(packet.end.getMilliseconds() + 1);
                    } else if (timestamp.end < timestamp.start) {
                        packet.status = "speedy (arrived " + (timestamp.start - timestamp.end) + " ms earlier)";
                        console.warn("SIP packet arrived before started ! (" + (timestamp.start - timestamp.end) + " ms)");
                        packet.end = new Date(timestamp.start);
                        packet.end.setMilliseconds(packet.end.getMilliseconds() + 1);
                    }
                }
            }
            items = list;
        };

        /**
         * Add packet group to the item (packet) structure and store all groups.
         * Replace UUID by a reference to packet object
         * @param list array of all groups
         */
        var addGroups = function (list) {
            var packetsByUuid = {};
            items.forEach(function (p) {
                packetsByUuid[p.uuid] = p;
            });
            list.forEach(function (group) {
                for (var i in group.packets) {
                    var packetUuid = group.packets[i];
                    group.packets[i] = packetsByUuid[packetUuid];
                    packetsByUuid[packetUuid].group = group;
                }
                groups.push(group);
            });
        };

        var init = function (scope, elem) {

            var lanesLength = displayNode.length;

            scope.height = lanesLength * scope.heightLane + margin.top + margin.bottom;
            gm.timeline.height = scope.height;

            var width = scope.width - margin.left - margin.right,
                height = scope.height - margin.top - margin.bottom,
                titleWidth = 150;

            if (!domain) {
                //TODO add a default domain (range scheduled)
                var interval = ss.search.filter.time.interval();
                domain = [interval.from, interval.to];
            }

            if(!x)
                x = d3.time.scale()
                    .domain(domain)
                    .range([0, width]);
            else
                x.range([0, width]);

            y = d3.scale.linear()
                .domain([0, lanesLength])
                .range([0, height]);

            xAxis = d3.svg.axis()
                .scale(x)
                .orient("bottom")
                .tickSize(-height);


            var zoom = d3.behavior.zoom()
                .x(x)
                .scaleExtent([0, (domain[1] - domain[0]) / 100])
                .on("zoom", updatePackets);

            svg = d3.select(elem).append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .attr("class", "timeline");

            svgg = svg.append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
                .call(zoom);

            // background lines
            svgg.append("g")
                .attr("class", "backgroundLines")
                .selectAll(".laneLines")
                .data(displayNode)
                .enter().append("rect")
                .attr("x", 0)
                .attr("y", function (d, i) {
                    return y(i);
                })
                .attr("width", width)
                .attr("height", y(1))
                .attr("fill", function (d, i) {
                    return i % 2 == 0 ? "rgb(230,230,230)" : "rgb(255,255,255)";
                });

            // Graph items
            var graph = svgg.append("g")
                .attr("class", "graphGroup");

            graph.append("defs").append("clipPath")
                .attr("id", "clip")
                .append("rect")
                .attr("width", width)
                .attr("height", height);

            graph.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + height + ")")
                .call(xAxis);

            itemRects = graph.append("g")
                .attr("clip-path", "url(#clip)");

            // Title side bar
            var title = svgg.append("g")
                .attr("width", width)
                .attr("height", height)
                .attr("class", "titleBar");

            title.append("defs").append("clipPath")
                .attr("id", "cliptitle")
                .append("rect")
                .attr("width", titleWidth)
                .attr("height", height);

            title.append("rect")
                .attr("x", 0)
                .attr("y", 0)
                .attr("width", titleWidth)
                .attr("height", height + 10)
                .attr("style", "fill:rgb(250,250,250); fill-opacity:.8;");

            title.append("g")
                .attr("class", "backgroundLines")
                .selectAll(".laneLines")
                .data(displayNode)
                .enter().append("rect")
                .attr("x", 0)
                .attr("y", function (d, i) {
                    return y(i);
                })
                .attr("width", titleWidth)
                .attr("height", y(1))
                .attr("fill", function (d, i) {
                    return i % 2 == 0 ? "rgb(230,230,230)" : "rgb(255,255,255)";
                });

            title.append("line")
                .attr("x1", titleWidth)
                .attr("x2", titleWidth)
                .attr("y1", 0)
                .attr("y2", height + 20)
                .attr("stroke", "rgba(0,0,0,.1)");

            title.append("g")
                .attr("clip-path", "url(#cliptitle)")
                .selectAll(".laneText")
                .data(displayNode).enter()
                .append("text")
                .text(function (d) {
                    return d.node.name;
                })
                .attr("x", function (d) {
                    var depth = 0;

                    function gd(n) {
                        if (n.parent == undefined) return;
                        depth++;
                        gd(n.parent);
                    }

                    gd(d.node);
                    if (d.node.child != undefined) depth++;
                    return depth * 13;
                })
                .attr("y", function (d, i) {
                    return y(i) + y(1) / 2;
                })
                .attr("dy", ".5ex")
                .attr("text-anchor", "start")
                .attr("class", "laneText");

            var treeTitle = title.append("g");

            function depthSearch(root, depth) {
                function getCurLanesNode(node) {
                    for (var i in displayNode) {
                        if (displayNode[i].node.name == node.name)
                            return [displayNode[i], i];
                    }
                    return null;
                }

                function getChildrenSorted(h) {
                    var hlist = [];
                    for (var i in h) {
                        hlist.push(h[i]);
                    }
                    hlist = hlist.sort(function (a, b) {
                        if (a.name < b.name) return -1;
                        if (a.name > b.name) return 1;
                        return 0;
                    });
                    return hlist;
                }

                function findFirstLanesNode(h) {
                    var hlist = getChildrenSorted(h);
                    var cur = getCurLanesNode(hlist[0]);
                    if (!cur) return findFirstLanesNode(hlist[0].child);
                    return cur;
                }

                var cur = getCurLanesNode(root);
                if (cur) {
                    if (root.child == undefined) return;
                    //In displayNode list
                    var g = treeTitle.append('g')
                        .attr('transform', 'translate(' + depth * 13 + ',' + (y(cur[1]) + y(1) / 2 - 6) + ')')
                        .on('click', function () {
                            // Change lanes list
                            var d = cur[0];
                            for (var i in d.node.child) d.node.child[i].visible = true;
                            // Regenerate lanes
                            updateLanes(scope, elem);
                        });
                    g.append('rect')
                        .attr("x", 0)
                        .attr("y", 0)
                        .attr("width", 10)
                        .attr("height", 10)
                        .attr("fill", "rgba(255,0,0,0)");
                    g.append('polygon')
                        .attr('points', '3,1 10,5 3,9')
                        .attr('fill', 'rgba(150,150,150,.7)');
                    return;
                }
                cur = findFirstLanesNode(root.child);
                var g = treeTitle.append('g')
                    .attr('transform', 'translate(' + depth * 13 + ',' + (y(cur[1]) + y(1) / 2 - 6) + ')')
                    .on('click', function () {
                        var d = root;
                        for (var i in d.child) d.child[i].visible = false;
                        // Regenerate lanes
                        updateLanes(scope, elem);
                    });
                g.append('rect')
                    .attr("x", 0)
                    .attr("y", 0)
                    .attr("width", 10)
                    .attr("height", 10)
                    .attr("fill", "rgba(0,255,0,0)");
                g.append('polygon')
                    .attr('points', '1,3 9,3 5,10')
                    .attr('fill', 'rgba(150,150,150,.7)');
                if (root.child != undefined) {
                    for (var i in root.child) {
                        depthSearch(root.child[i], depth + 1);
                    }
                }
            }

            depthSearch(lanesTreeStruct.nodes, 0);
            depthSearch(lanesTreeStruct.links, 0);

            updatePackets();

            if (listener.loaded) listener.loaded();
        };

        var updateLanes = function (scope, elem) {
            genLanesMapping();
            d3.select(elem).selectAll('svg').remove();
            init(scope, elem);
            scope.$apply();
        };

        var updatePackets = function () {

            if (items.length == 0)
                return;

            // Zoom
            svgg.select(".x.axis").call(xAxis);

            // Filter data
            var itemsFiltered = items.filter(function (d) {
                var p = ss.protocols[d.protocol];
                if (!p) return true;
                for (var i in p.filter) {
                    var cat = p.filter[i];
                    if(d.category.match(cat)) return true;
                }
                return !p.filter;
            });

            // Update time line graph
            var rects = itemRects.selectAll("rect")
                .data(itemsFiltered, function (d) {
                    return d.uuid;
                })
                .attr("x", function (d) {
                    return x(d.start);
                })
                .attr("width", function (d) {
                    return Math.abs(x(d.end) - x(d.start));
                });
            rects.enter().append("rect")
                .attr("x", function (d) {
                    return x(d.start);
                })
                .attr("y", function (d) {
                    return yMap(d.lane) + 2;
                })
                .attr("width", function (d) {
                    return Math.abs(x(d.end) - x(d.start));
                })
                .attr("height", function (d) {
                    return y(1) - 4;
                })
                .style("fill", color_packet)
                .style("stroke", color_packet);

            for (var l in listener.rect) {
                rects.on(l, (function (l) {
                    return function (d) {
                        listener.rect[l](d);
                    }
                })(l));
            }

            function color_packet(d) {
                var color = "#888888"; //Default color
                if (!ss.protocols) return color;
                if (ss.protocols[d.protocol]) {
                    var p = ss.protocols[d.protocol];
                    if(p.color) color = p.color;
                    if (!p.category) return color;
                    if(p.category[d.category]) {
                        var c = p.category[d.category];
                        if (c.color) return c.color;
                    }
                }
                return color;
            }

            rects.exit().remove();

        };

        var onrect = function (l, event) {
            listener.rect[l] = event;
        };

        var onLoaded = function (event) {
            listener.loaded = event;
        };

        var remove = function (elem) {
            lanes = [];
            items = [];
            elem.innerHTML = "";
        };

        return {
            restrict: 'EA',

            scope: {
                display: '=',
                data: '=',
                groups: '=',
                width: '=',
                height: '=',
                heightLane: '=',
                filter: '=',
                selectedData: '&'
            },

            link: function ($scope, elem, attrs) {

                $scope.$watch('display', function (value) {
                    if (value) {
                        console.debug("Build lanes");
                        refreshLanes(gm.network.graph);
                        init($scope, elem[0]);
                    } else {
                        console.debug("Remove all timeline graph no graph found");
                        remove(elem[0]);
                    }
                });

                $scope.$watch('data', function (value) {
                    if (!$scope.display) return;
                    addPackets(value);
                    updatePackets();
                    onrect('mouseover', function (d) {
                        // Display panel
                        $scope.$apply(function () {
                            $scope.selectedData({data: d});
                        });
                        // Show only packet in the group
                        itemRects.selectAll("rect").style("opacity", function(p){
                            return p.group == d.group ? 1 : .2;
                        });
                    });
                    onrect('mouseout', function (d) {
                        // Hidden panel
                        $scope.$apply(function () {
                            $scope.selectedData({data: null});
                        });
                        // Show all packet
                        itemRects.selectAll("rect").style("opacity", function(p){
                            return 1;
                        });
                    });
                    onrect('click', function (d) {
                        $scope.$apply(function () {
                            gm.panel.fixed = true;
                            $scope.selectedData({data: d});
                        });
                    });
                });

                $scope.$watch('groups', function (value) {
                   if (!$scope.display) return;
                   addGroups(value);
                });

                $scope.$watch('filter', function () {
                    console.debug("Update filter");
                    if (lanes)
                        updatePackets();
                }, true);

                $scope.$watch('width', function(value) {
                    if(svg) {
                        svg.attr('width', value);
                        d3.select(elem[0]).selectAll('svg').remove();
                        init($scope, elem[0]);
                    }
                });
            }


        };
    }
})();