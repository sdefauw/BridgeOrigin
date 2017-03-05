(function () {

    angular.module('graph')
        .controller('SettingController', ['SettingService', SettingController]);

    function SettingController(ss) {

        var setting = {
            adder: {},
            timeFilterOptions: [
                {label: '30 s', value: 30},
                {label: '1 min', value: 60},
                {label: '5 min', value: 5 * 60},
                {label: '15 min', value: 15 * 60},
                {label: '30 min', value: 30 * 60},
                {label: '1 h', value: 60 * 60}
            ],
            timeSelection: "until_now",
            pickers: {
                from: {
                    date: new Date(),
                    open: false
                },
                to:{
                    date: new Date(),
                    open: false
                },
                search: {
                    criterion: function (crit) {
                        if (!crit) {
                            return ss.search.filter.criterion
                        }
                        return ss.search.filter.criterion[crit]
                    },
                    match: []
                }
            },

            openCalendar : function(e, picker) {
                setting.timeSelection = 'from_to';
                setting.pickers[picker].open = true;
            },

            show: function () {
                return ss.display;
            },

            isActiveMenu: function (type) {
                return ss.menu.selected === type ? 'selected' : '';
            },

            selectMenu: function (type) {
                ss.menu.selected = type;
            },

            tfilterSelect: function () {
                setting.timeSelection = 'until_now';
                ss.search.filter.time.from = -setting.tfilter.value;
                ss.search.filter.time.to = null;
            },

            pickerSelect: function () {
                setting.timeSelection = 'from_to';
                ss.search.filter.time.from = setting.pickers.from.date;
                ss.search.filter.time.to = setting.pickers.to.date;
            },

            addSearchCritiron: function () {
                setting.pickers.search.match.push({
                    criterion: "",
                    value: ""
                });
            },

            updateSearchMatch: function () {
                var f = {};
                for(var i in setting.pickers.search.match) {
                    var line = setting.pickers.search.match[i];
                    if (!line.value) continue;
                    f[line.criterion] = line.value;
                }
                ss.search.filter.match = f;
            },

            filtersAvailable: function () {
                var filters = {};
                for (var protocol in ss.protocols) {
                    var protocolObj = ss.protocols[protocol];
                    if (!protocolObj.filter) continue;
                    filters[protocol] = protocolObj;
                }
                return filters;
            },

            addProtocol: function (protocol) {
                if (!setting.adder[protocol]) return;
                var new_category = setting.adder[protocol];
                if (!new_category || new_category == '') return;
                var category_list = ss.protocols[protocol].category;
                var found = false;
                for (var i in category_list) {
                    var category = category_list[i];
                    if (category.name == new_category && ss.protocols[protocol].filter.indexOf(i) < 0) {
                        // Category found in the list
                        ss.protocols[protocol].selected.push(i);
                        found = true;
                        break;
                    }
                }
                if(!found) {
                    // Custom category
                    ss.protocols[protocol].selected.push(new_category);
                }
                setting.adder[protocol] = "";
            },

            rmProtocol: function (protocol, category) {
                if (!category || category == '') return;
                ss.protocols[protocol].selected.splice(ss.protocols[protocol].selected.indexOf(category), 1);
            }
        };

        setting['tfilter'] = setting.timeFilterOptions[1];
        setting.tfilterSelect();

        // Date time picker configuration
        setting.pickers.from.buttonBar = {
            show: true,
                now: {
                show: true,
                    text: 'Now'
            },
            today: {
                show: true,
                    text: 'Today'
            },
            clear: {
                show: false,
                    text: 'Clear'
            },
            date: {
                show: true,
                    text: 'Date'
            },
            time: {
                show: true,
                    text: 'Time'
            },
            close: {
                show: false,
                    text: 'Close'
            }
        };
        setting.pickers.to.buttonBar = setting.pickers.from.buttonBar;
        setting.pickers.from.date.setSeconds(setting.pickers.from.date.getSeconds() - setting.tfilter.value);

        return setting;
    }
})();