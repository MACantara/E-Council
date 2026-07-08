(function () {
    const STORAGE_KEY = 'theme';
    const html = document.documentElement;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const icons = { light: 'sun', dark: 'moon', system: 'monitor' };
    const labels = { light: 'Light', dark: 'Dark', system: 'System' };

    function resolveStored(stored) {
        if (stored === 'dark') return 'dark';
        if (stored === 'light') return 'light';
        return mq.matches ? 'dark' : 'light';
    }

    function applyTheme(stored) {
        const resolved = resolveStored(stored);
        if (resolved === 'dark') html.classList.add('dark');
        else html.classList.remove('dark');
        document.dispatchEvent(new CustomEvent('themeChanged', { detail: resolved }));
    }

    function storedTheme() {
        return localStorage.getItem(STORAGE_KEY) || 'system';
    }

    function applyStored() {
        applyTheme(storedTheme());
    }

    function cycle() {
        const current = storedTheme();
        const next = current === 'light' ? 'dark' : current === 'dark' ? 'system' : 'light';
        localStorage.setItem(STORAGE_KEY, next);
        applyStored();
        return next;
    }

    function renderToggles() {
        const stored = storedTheme();
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.innerHTML = '<i data-lucide="' + icons[stored] + '" width="18" height="18" class="w-4 h-4"></i><span class="hidden sm:inline theme-label">' + labels[stored] + '</span>';
        });
        if (window.lucide) lucide.createIcons();
    }

    applyStored();

    mq.addEventListener('change', function () {
        if (storedTheme() === 'system') applyStored();
    });

    document.addEventListener('DOMContentLoaded', function () {
        renderToggles();
        document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                cycle();
                renderToggles();
            });
        });
    });

    document.addEventListener('themeChanged', renderToggles);
})();
