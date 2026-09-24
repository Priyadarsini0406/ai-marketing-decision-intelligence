<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { api, signOut, type User } from '$lib/api';

    let { role, children }: { role: 'student' | 'manager' | 'admin'; children: import('svelte').Snippet } = $props();
    type NavItem = { label: string; href: string; icon: string };
    type NavGroup = { label?: string; items: NavItem[] };
    const navigation: Record<typeof role, NavGroup[]> = {
        student: [
            { items: [{ label: 'Dashboard', href: '/student/dashboard', icon: '◫' }] },
            { label: 'Admission', items: [
                { label: 'My Enquiries', href: '/student/enquiries', icon: '◌' }, { label: 'New Enquiry', href: '/student/enquiries/new', icon: '+' },
                { label: 'Enquiry Status', href: '/student/enquiries/status', icon: '◷' }, { label: 'Application Status', href: '/student/application', icon: '□' }
            ] },
            { label: 'Account', items: [{ label: 'My Profile', href: '/student/profile', icon: '○' }, { label: 'Notifications', href: '/student/notifications', icon: '●' }] }
        ],
        manager: [
            { items: [{ label: 'Dashboard', href: '/dashboard', icon: '◫' }] },
            { label: 'Lead Intelligence', items: [{ label: 'Student Leads', href: '/student-leads', icon: '◌' }, { label: 'Admission Prediction', href: '/admission-prediction', icon: '◇' }, { label: 'Explainable AI', href: '/explainable-ai', icon: '✦' }, { label: 'Student Segmentation', href: '/student-segmentation', icon: '◈' }] },
            { label: 'Admission Analytics', items: [{ label: 'Admission Funnel', href: '/admission-funnel', icon: '▽' }, { label: 'Channel Attribution', href: '/channel-attribution', icon: '↗' }, { label: 'Campaign Analytics', href: '/campaign-analytics', icon: '◧' }] },
            { label: 'Budget Intelligence', items: [{ label: 'Budget Optimization', href: '/budget-optimization', icon: '◒' }, { label: 'What-If Simulator', href: '/what-if', icon: '◐' }] },
            { label: 'AI Insights', items: [{ label: 'AI Recommendations', href: '/ai-recommendations', icon: '✦' }] },
            { label: 'Reports', items: [{ label: 'Reports & Analytics', href: '/reports', icon: '▤' }] }
        ],
        admin: [
            { items: [{ label: 'Dashboard', href: '/admin/dashboard', icon: '◫' }] },
            { label: 'ML Intelligence', items: [{ label: 'Model Performance', href: '/admin/model-performance', icon: '◧' }] },
            { label: 'User Management', items: [{ label: 'Students', href: '/admin/students', icon: '○' }, { label: 'Managers', href: '/admin/managers', icon: '◌' }, { label: 'User Accounts', href: '/admin/users', icon: '◉' }] },
            { label: 'Education Management', items: [{ label: 'Courses / Programs', href: '/admin/courses', icon: '□' }, { label: 'Institutions', href: '/admin/institutions', icon: '▣' }] },
            { label: 'Data Management', items: [{ label: 'Datasets', href: '/admin/datasets', icon: '▤' }, { label: 'Data Import', href: '/admin/data-import', icon: '⇧' }] },
            { label: 'System', items: [{ label: 'System Activity', href: '/admin/activity', icon: '◷' }, { label: 'Audit Logs', href: '/admin/audit-logs', icon: '≡' }] }
        ]
    };
    const destinations = { student: '/student/dashboard', manager: '/dashboard', admin: '/admin/dashboard' };
    let user = $state<User | null>(null);
    let error = $state('');
    let mobileOpen = $state(false);
    let sidebarCollapsed = $state(false);
    const roleMatches = (value: string) => role === 'manager' ? value === 'admission_manager' || value === 'marketing_manager' : value === role;
    const isActiveLink = (href: string) => page.url.pathname === href || page.url.pathname.startsWith(`${href}/`);
    let currentItem = $derived(navigation[role].flatMap(group => group.items).find(item => isActiveLink(item.href)));
    let title = $derived(currentItem?.label ?? (role === 'manager' ? 'Admission & Marketing Intelligence' : role === 'admin' ? 'Administration' : 'Student Portal'));
    const toggleSidebar = () => { sidebarCollapsed = !sidebarCollapsed; };
    onMount(async () => {
        try {
            const account = await api('/auth/me');
            if (!roleMatches(account.role)) { window.location.assign(destinations[account.role === 'student' ? 'student' : account.role === 'admin' ? 'admin' : 'manager']); return; }
            user = account;
        } catch (e) { error = (e as Error).message; }
    });
    async function logout() { try { await signOut(); window.location.assign('/login'); } catch (e) { error = (e as Error).message; } }
</script>

{#if user}
<div class="role-effects flex h-screen bg-primary font-sans text-text-primary overflow-hidden">
    {#if mobileOpen}<button class="fixed inset-0 z-30 bg-black/60 md:hidden" aria-label="Close navigation" onclick={() => mobileOpen = false}></button>{/if}
    <aside class:translate-x-0={mobileOpen} class:md:w-64={!sidebarCollapsed} class:md:w-20={sidebarCollapsed} class="fixed md:static inset-y-0 left-0 z-40 w-72 md:w-64 -translate-x-full md:translate-x-0 bg-card border-r border-white/5 flex flex-col transition-all duration-300 ease-in-out shrink-0 overflow-hidden">
        <div class="h-20 border-b border-white/5 flex items-center justify-between px-3 md:px-4">
            <a href="/" class="flex items-center gap-2 min-w-0 overflow-hidden" class:justify-center={sidebarCollapsed}>
                <div class="w-8 h-8 rounded-lg bg-linear-to-br from-accent to-secondary grid place-items-center shadow-[0_0_15px_rgba(164,123,224,.5)] shrink-0">🎓</div>
                {#if !sidebarCollapsed}
                    <span class="text-xl font-bold tracking-wider text-white whitespace-nowrap">Decision<span class="text-accent font-serif italic">Intel</span></span>
                {/if}
            </a>
            <button type="button" class="hidden md:grid h-8 w-8 place-items-center rounded-lg border border-white/10 bg-white/5 text-text-secondary hover:text-white transition-colors duration-200 shrink-0" aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'} title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'} onclick={toggleSidebar}>
                {#if sidebarCollapsed}
                    <svg viewBox="0 0 24 24" class="h-4 w-4 transition-transform duration-200" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18l6-6-6-6" /></svg>
                {:else}
                    <svg viewBox="0 0 24 24" class="h-4 w-4 transition-transform duration-200" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6" /></svg>
                {/if}
            </button>
        </div>
        <nav class="flex-1 p-3 md:p-4 space-y-4 overflow-y-auto custom-scrollbar" aria-label="Role navigation">
            {#each navigation[role] as group}
                <section>
                    {#if group.label && !sidebarCollapsed}
                        <p class="px-3 mb-1 text-[10px] uppercase tracking-[.15em] font-bold text-slate-500">{group.label}</p>
                    {/if}
                    {#each group.items as item}
                        <a href={item.href} onclick={() => mobileOpen = false} class:nav-active={isActiveLink(item.href)} class:justify-center={sidebarCollapsed} class="nav-link" title={sidebarCollapsed ? item.label : undefined}>
                            <span class="w-5 text-center opacity-80 shrink-0">{item.icon}</span>
                            {#if !sidebarCollapsed}<span class="nav-text whitespace-nowrap">{item.label}</span>{/if}
                        </a>
                    {/each}
                </section>
            {/each}
        </nav>
        <div class="p-3 md:p-4 border-t border-white/5 space-y-1">
            {#each [
                { label: 'Notifications', href: role === 'admin' ? '/admin/notifications' : role === 'student' ? '/student/notifications' : '/notifications', icon: '●' },
                { label: 'Profile', href: role === 'admin' ? '/admin/profile' : role === 'student' ? '/student/profile' : '/profile', icon: '○' },
                { label: 'Settings', href: role === 'admin' ? '/admin/settings' : role === 'student' ? '/student/settings' : '/settings', icon: '⚙' },
            ] as item}
                <a href={item.href} class:justify-center={sidebarCollapsed} class="nav-link" title={sidebarCollapsed ? item.label : undefined}>
                    <span class="w-5 text-center opacity-80 shrink-0">{item.icon}</span>
                    {#if !sidebarCollapsed}<span class="nav-text whitespace-nowrap">{item.label}</span>{/if}
                </a>
            {/each}
            <button class:justify-center={sidebarCollapsed} class="nav-link w-full text-left hover:text-red-300" title={sidebarCollapsed ? 'Logout' : undefined} onclick={logout}>
                <span class="w-5 text-center opacity-80 shrink-0">↪</span>
                {#if !sidebarCollapsed}<span class="nav-text whitespace-nowrap">Logout</span>{/if}
            </button>
        </div>
    </aside>
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header class="h-20 shrink-0 border-b border-white/5 flex items-center px-4 md:px-8 justify-between bg-primary/80 backdrop-blur-md">
            <div class="flex items-center gap-3"><button class="md:hidden p-2 text-white" onclick={() => mobileOpen = true} aria-label="Open navigation">☰</button><div><h2 class="text-lg md:text-xl font-bold text-white">{title}</h2><p class="hidden sm:block text-xs text-text-secondary">Decision-Intel / {title}</p></div></div>
            <div class="flex items-center gap-3"><a href={role === 'admin' ? '/admin/notifications' : role === 'student' ? '/student/notifications' : '/notifications'} class="w-9 h-9 rounded-lg bg-white/5 border border-white/10 grid place-items-center text-text-secondary hover:text-white" aria-label="Notifications">●</a><div class="hidden sm:block text-right"><p class="text-xs font-bold text-accent uppercase">{role === 'manager' ? 'Admission Manager' : role}</p><p class="text-sm text-white">{user.name}</p></div><div class="h-10 w-10 rounded-full bg-cta text-black grid place-items-center font-bold">{user.name.charAt(0).toUpperCase()}</div></div>
        </header>
        <div class="flex-1 overflow-auto p-4 md:p-8 relative custom-scrollbar"><div class="absolute top-0 right-0 w-125 h-125 bg-secondary/20 rounded-full blur-[100px] pointer-events-none z-0"></div><div class="relative z-10">{@render children()}</div></div>
    </main>
</div>
{:else}<p class="p-8 text-text-secondary" role="status">{error || 'Authenticating…'} {#if error}<a href="/login" class="text-accent ml-2 hover:underline">Sign in</a>{/if}</p>{/if}

<style>
    .nav-link { display:flex; align-items:center; gap:.7rem; padding:.6rem .75rem; border-radius:.55rem; color:var(--color-text-secondary, #a7a4b4); font-size:.85rem; font-weight:500; transition:all .2s ease; overflow:hidden; }
    .nav-link:hover { color:white; background:rgba(255,255,255,.05); }
    .nav-active { color:white; background:var(--color-secondary, #37305f); border:1px solid rgba(164,123,224,.25); box-shadow:0 0 15px rgba(164,123,224,.12); }
    :global(.custom-scrollbar::-webkit-scrollbar) { width:6px; }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background:rgba(255,255,255,.13); border-radius:10px; }
</style>
