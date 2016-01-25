(function () {

    angular.module('graph')
        .controller('SettingController', ['SettingService', SettingController]);

    function SettingController(ss) {

        var setting = {
            adder: {},

            show: function () {
                return ss.display;
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
        return setting;
    }
})();