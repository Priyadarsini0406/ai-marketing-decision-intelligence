import { browser } from '$app/environment';

export type Theme = 'dark' | 'light';

const STORAGE_KEY = 'di-theme';
const LIGHT_CLASS = 'di-light';

/**
 * Dark is the Decision-Intel design of record, so it is the default. The
 * selection is persisted in localStorage and the class is mirrored onto
 * <html> so the same tokens drive every page, including the auth screens.
 */
export const theme = $state<{ current: Theme }>({ current: 'dark' });

export const isLight = () => theme.current === 'light';

function readStored(): Theme {
    if (!browser) return 'dark';
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored === 'light' || stored === 'dark' ? stored : 'dark';
    } catch {
        return 'dark';
    }
}

export function applyTheme(next: Theme) {
    theme.current = next;
    if (!browser) return;
    document.documentElement.classList.toggle(LIGHT_CLASS, next === 'light');
    document.documentElement.style.colorScheme = next;
    try {
        localStorage.setItem(STORAGE_KEY, next);
    } catch {
        /* private mode: the choice simply will not persist */
    }
}

export function toggleTheme() {
    applyTheme(theme.current === 'light' ? 'dark' : 'light');
}

/** Called once from the root layout; app.html has already set the class. */
export function initTheme() {
    applyTheme(readStored());
}
