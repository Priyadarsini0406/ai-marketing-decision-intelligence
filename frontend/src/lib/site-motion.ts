/** Progressive enhancement: content remains visible if animation is unavailable. */
export function siteMotion(root: HTMLElement) {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const seen = new WeakSet<Element>();
    const running = new Set<Animation>();
    const selector = '.panel, .workspace-panel, .stat, .stats > section, .stats > div, .summary-grid > div, .bg-card.border, article, .identity-card, .institution, h1';
    let frame = 0;
    let stopped = false;
    let pointerFrame = 0;
    let hovered: HTMLElement | null = null;
    let pointerX = 0, pointerY = 0;
    const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
    function spotlight(event: PointerEvent) {
        if (preference.matches || !finePointer.matches) return;
        hovered = event.target instanceof Element ? event.target.closest<HTMLElement>('.role-effects .motion-card') : null;
        if (!hovered) return;
        pointerX = event.clientX; pointerY = event.clientY;
        if (!pointerFrame) pointerFrame = requestAnimationFrame(() => {
            pointerFrame = 0;
            if (!hovered || !hovered.isConnected) return;
            const bounds = hovered.getBoundingClientRect();
            hovered.style.setProperty('--glow-x', `${pointerX - bounds.left}px`);
            hovered.style.setProperty('--glow-y', `${pointerY - bounds.top}px`);
        });
    }

    function reveal(element: HTMLElement, delay: number) {
        if (preference.matches || typeof element.animate !== 'function') return;
        const animation = element.animate([
            { opacity: 0.35, translate: '0 14px' },
            { opacity: 1, translate: '0 0' }
        ], { duration: 460, delay, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' });
        running.add(animation);
        const done = () => running.delete(animation);
        animation.onfinish = done;
        animation.oncancel = done;
    }
    const intersection = typeof IntersectionObserver !== 'undefined' ? new IntersectionObserver(entries => {
        let index = 0;
        for (const entry of entries) {
            if (!entry.isIntersecting) continue;
            intersection?.unobserve(entry.target);
            reveal(entry.target as HTMLElement, Math.min(index++ * 45, 180));
        }
    }, { threshold: 0.06 }) : null;

    function scan() {
        frame = 0;
        if (stopped) return;
        root.querySelectorAll<HTMLElement>(selector).forEach(element => {
            if (seen.has(element) || element.closest('aside, nav, [role="dialog"]')) return;
            seen.add(element);
            if (element.tagName !== 'H1') element.classList.add('motion-card');
            if (!preference.matches) intersection?.observe(element);
        });
    }
    function schedule() { if (!frame && !stopped) frame = requestAnimationFrame(scan); }
    function reduceMotion() {
        if (preference.matches) {
            for (const animation of running) animation.cancel();
            intersection?.disconnect();
        }
    }
    const mutations = new MutationObserver(schedule);
    mutations.observe(root, { childList: true, subtree: true });
    preference.addEventListener('change', reduceMotion);
    root.addEventListener('pointermove', spotlight, { passive: true });
    schedule();
    return {
        destroy() {
            stopped = true; cancelAnimationFrame(frame);
            cancelAnimationFrame(pointerFrame);
            root.removeEventListener('pointermove', spotlight);
            mutations.disconnect(); intersection?.disconnect();
            preference.removeEventListener('change', reduceMotion);
            for (const animation of running) animation.cancel();
        }
    };
}
