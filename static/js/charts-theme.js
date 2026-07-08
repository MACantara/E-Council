(function () {
    const root = document.documentElement;

    function cssVar(name) {
        return getComputedStyle(root).getPropertyValue(name).trim();
    }

    window.ThemeCharts = {
        color: function (name) { return cssVar('--color-' + name); },
        colors: ['accent', 'danger', 'success', 'warning', 'info'],
        defaultColors: function (count) {
            return this.colors.slice(0, count).map(function (c) { return this.color(c); }.bind(this));
        },
        withAlpha: function (color, alpha) {
            return color.startsWith('#') ? color + Math.round(alpha * 255).toString(16).padStart(2, '0') : color;
        }
    };

    function apply() {
        if (typeof Chart === 'undefined') return;
        Chart.defaults.color = window.ThemeCharts.color('ink-2');
        Chart.defaults.borderColor = window.ThemeCharts.color('edge');
        Chart.defaults.backgroundColor = 'transparent';
        Chart.defaults.font.family = getComputedStyle(root).fontFamily;
    }

    apply();
    document.addEventListener('themeChanged', apply);
})();
