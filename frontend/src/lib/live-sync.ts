/** Refresh shared records while a dashboard is open and when it regains focus. */
export function startLiveSync(refresh: () => void | Promise<void>, intervalMs = 10000) {
    let active = false;
    let inFlight = false;

    const sync = () => {
        if (active || inFlight || document.visibilityState === 'hidden') return;
        inFlight = true;
        void Promise.resolve(refresh())
            .catch(() => undefined)
            .finally(() => { inFlight = false; });
    };

    const timer = window.setInterval(sync, intervalMs);
    window.addEventListener('focus', sync);
    document.addEventListener('visibilitychange', sync);

    return () => {
        active = true;
        window.clearInterval(timer);
        window.removeEventListener('focus', sync);
        document.removeEventListener('visibilitychange', sync);
    };
}
