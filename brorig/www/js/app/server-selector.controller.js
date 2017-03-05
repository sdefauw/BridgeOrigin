(function () {

    angular.module('app')
        .controller('ServerSelectorController', [
            'ServerSelectorService', 'PageService',
            ServerSelectorController]);

    function ServerSelectorController(sss, ps) {

        var ssc = {
            serversFiltered: null,
            searchKeywords: null,
            filterApplied: [],

            servers: function () {
                if (ssc.serversFiltered == null)
                    return sss.servers;
                return ssc.serversFiltered;
            },

            display: function () {
                return sss.display;
            },

            close: function () {
                sss.display = false;
            },

            open: function () {
                sss.display = true;
            },

            process: function () {
                ssc.close();
                ps.windowsManager.closeAll();
                if (!sss.process())
                    ssc.open();
            },

            select: function (server) {
                for (var i in sss.servers) {
                    if (sss.servers[i].key == server.key) {
                        sss.servers[i].selected = !sss.servers[i].selected;
                        if (sss.servers[i].selected)
                            sss.storage.addServerkey(server.key);
                        else
                            sss.storage.rmServerkey(server.key);
                        return;
                    }
                }
            },

            applyFilters: function () {
                ssc.serversFiltered = sss.servers;
                // Re-compute all filters
                ssc.serversFiltered = sss.servers;
                for (var i in ssc.filterApplied) {
                    var filterName = ssc.filterApplied[i];
                    var ff = ssc.filters[filterName];
                    if (!ff) continue;
                    ssc.serversFiltered = ff(ssc.serversFiltered);
                }
                // Re-compute search filters
                ssc.searchFilter();
            },

            search: function () {
                ssc.applyFilters();
            },

            searchFilter: function () {
                if (!ssc.searchKeywords || ssc.searchKeywords == '') {
                    return;
                }
                var keywords = ssc.searchKeywords.split(" ");
                var list = [];
                ssc.serversFiltered.forEach(function (item) {
                    var s = item.key + " " + item.name + " " + item.group;
                    var d = false;
                    keywords.forEach(function (keyword) {
                        var re = new RegExp(keyword, "i");
                        if (!re.test(s))
                            d = true;
                    });
                    if (!d)
                        list.push(item);
                });
                ssc.serversFiltered = list;
            },

            setFilter: function (filter) {
                if (filter) {
                    // Check if filter exist
                    if (!ssc.filters[filter]) {
                        return;
                    }
                    // Enable/Disable the filter
                    if (ssc.filterApplied.indexOf(filter) < 0) {
                        ssc.filterApplied.push(filter);
                    } else {
                        ssc.filterApplied = ssc.filterApplied.filter(function (item) {
                            return item != filter;
                        });
                    }
                }
                // Apply filters
                ssc.applyFilters();
            },

            filters: {
                selected: function (list) {
                    return list.filter(function (item) {
                        return item.selected;
                    });
                }
            }

        };

        return ssc;
    }
})();