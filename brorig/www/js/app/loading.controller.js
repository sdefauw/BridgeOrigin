(function () {

    angular.module('app')
        .controller('LoadingController', ['PageService', LoadingController]);

    function LoadingController(page) {

        var id = 'loading';
        var size = 50;
        var durAnim = 2500;

        var progress = 0;
        var arc = d3.svg.arc()
            .startAngle(0)
            .innerRadius(size / 2 - 5)
            .outerRadius(size / 2 - 4);
        var svg = d3.select("#" + id).append("svg")
            .attr("width", size)
            .attr("height", size)
            .append("g")
            .attr("transform", "translate(" + size / 2 + "," + size / 2 + ")");

        svg.append("path")
            .attr("class", "background")
            .attr("d", arc.endAngle(2 * Math.PI))
            .attr("fill", "rgb(240,240,240)");

        var foreground = svg.append("path")
            .attr("class", "foreground")
            .attr("fill", "rgba(0,204,255, .75)");

        var animate = function () {
            var i = d3.interpolate(0, 1);
            d3.transition().duration(durAnim).tween("progress", function () {
                return function (t) {
                    progress = i(t);
                    var ea = 2.75 * progress > 2 ? 2 * Math.PI : 2.75 * Math.PI * progress;
                    foreground.attr("d", arc.startAngle(2 * Math.PI * progress).endAngle(ea));
                };
            });
        };
        var interval;

        var status_show;

        this.show = function () {
            var show = page.load.show;
            if (status_show != show) {
                status_show = show;
                if (status_show) {
                    // Display
                    if (interval) clearInterval(interval);
                    animate();
                    interval = setInterval(animate, durAnim);
                } else {
                    //Hidden
                    clearInterval(interval);
                    interval = null;
                }
            }
            return show;
        };
    }
})();