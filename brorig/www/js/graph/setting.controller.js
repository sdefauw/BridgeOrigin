(function () {

    angular.module('graph')
        .controller('SettingController', ['SettingService', SettingController]);

    function SettingController(ss) {

        var setting = {
            adder: {},
            menu: {
                selected: "filter"
            },
            timeFilterOptions: [
                {label: '1 min', value: 60},
                {label: '5 min', value: 5 * 60},
                {label: '15 min', value: 15 * 60},
                {label: '30 min', value: 30 * 60},
                {label: '1 h', value: 60 * 60},
                {label: '5 h', value: 5 * 60},
                {label: '10 h', value: 10 * 60},
                {label: 'All log', value: ''}
            ],

            picker : {
                date: new Date(),
                open: true,
                buttonBar: {
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
                }
            },

            openCalendar : function(e, picker) {
                setting.picker.open = true;
            },

            show: function () {
                return ss.display;
            },

            isActiveMenu: function (type) {
                return setting.menu.selected === type ? 'selected' : '';
            },

            selectMenu: function (type) {
                setting.menu.selected = type;
            },

            tfilterSelect: function () {
                ss.search.filter.historyTime = setting.tfilter.value;
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

        return setting;
    }
})();