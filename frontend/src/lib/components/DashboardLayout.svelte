<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { api, signOut, type User } from '$lib/api';
    import OutlineIcon from '$lib/components/OutlineIcon.svelte';
import ThemeToggle from '$lib/ThemeToggle.svelte';

    let { role, children }: { role: 'student' | 'manager' | 'admin'; children: import('svelte').Snippet } = $props();
    type NavItem = { label: string; href: string; icon: string; outline?: string };
    type NavGroup = { label?: string; items: NavItem[] };
    const navigation: Record<typeof role, NavGroup[]> = {
        student: [
            { items: [{ label: 'Dashboard', href: '/student/dashboard', icon: '◫', outline: 'dashboard' }] },
            { label: 'Admission', items: [
                { label: 'My Enquiries', href: '/student/enquiries', icon: '◌', outline: 'enquiries' }, { label: 'New Enquiry', href: '/student/enquiries/new', icon: '+', outline: 'new-enquiry' },
                { label: 'Enquiry Status', href: '/student/enquiries/status', icon: '◷', outline: 'enquiry-status' }, { label: 'Application Status', href: '/student/application', icon: '□', outline: 'application' }
            ] },
            { label: 'Account', items: [{ label: 'My Profile', href: '/student/profile', icon: '○', outline: 'profile' }, { label: 'Notifications', href: '/student/notifications', icon: '●', outline: 'notifications' }] }
        ],
        manager: [
            { items: [{ label: 'Dashboard', href: '/dashboard', icon: '◫', outline: 'dashboard' }] },
            { label: 'Lead Intelligence', items: [{ label: 'Student Leads', href: '/student-leads', icon: '◌', outline: 'enquiries' }, { label: 'Admission Prediction', href: '/admission-prediction', icon: '◇', outline: 'chart' }, { label: 'Explainable AI', href: '/explainable-ai', icon: '✦', outline: 'sparkle' }, { label: 'Student Segmentation', href: '/student-segmentation', icon: '◈', outline: 'users' }] },
            { label: 'Admission Analytics', items: [{ label: 'Admission Funnel', href: '/admission-funnel', icon: '▽', outline: 'clipboard' }, { label: 'Channel Attribution', href: '/channel-attribution', icon: '↗', outline: 'chart' }, { label: 'Campaign Analytics', href: '/campaign-analytics', icon: '◧', outline: 'chart' }] },
            { label: 'Budget Intelligence', items: [{ label: 'Budget Optimization', href: '/budget-optimization', icon: '◒', outline: 'briefcase' }, { label: 'What-If Simulator', href: '/what-if', icon: '◐', outline: 'sparkle' }] },
            { label: 'AI Insights', items: [{ label: 'AI Recommendations', href: '/ai-recommendations', icon: '✦', outline: 'award' }] },
            { label: 'Reports', items: [{ label: 'Reports & Analytics', href: '/reports', icon: '▤', outline: 'chart' }] }
        ],
        admin: [
            { items: [{ label: 'Dashboard', href: '/admin/dashboard', icon: '◫', outline: 'dashboard' }] },
            { label: 'User Management', items: [{ label: 'Students', href: '/admin/students', icon: '○', outline: 'graduation' }, { label: 'Managers', href: '/admin/managers', icon: '◌', outline: 'users' }, { label: 'User Accounts', href: '/admin/users', icon: '◉', outline: 'shield' }] },
            { label: 'Education Management', items: [{ label: 'Courses / Programs', href: '/admin/courses', icon: '□', outline: 'book' }, { label: 'Institutions', href: '/admin/institutions', icon: '▣', outline: 'building' }] },
            { label: 'Data Management', items: [{ label: 'Datasets', href: '/admin/datasets', icon: '▤', outline: 'clipboard' }, { label: 'Data Import', href: '/admin/data-import', icon: '⇧', outline: 'arrow-right' }] },
            { label: 'System', items: [{ label: 'System Activity', href: '/admin/activity', icon: '◷', outline: 'enquiry-status' }, { label: 'Audit Logs', href: '/admin/audit-logs', icon: '≡', outline: 'clipboard' }] }
        ]
    };
    const destinations = { student: '/student/dashboard', manager: '/dashboard', admin: '/admin/dashboard' };
    const student = $derived(role === 'student');
    const accountLinks = $derived(student
        ? { notifications: '/student/notifications', profile: '/student/profile', settings: '/student/settings' }
        : role === 'admin'
            ? { notifications: '/admin/notifications', profile: '/admin/profile', settings: '/admin/settings' }
            : { notifications: '/notifications', profile: '/profile', settings: '/settings' });
    let user = $state<User | null>(null);
    let error = $state('');
    let mobileOpen = $state(false);
    let menuOpen = $state(false);
    const roleMatches = (value: string) => role === 'manager' ? value === 'admission_manager' || value === 'marketing_manager' : value === role;
    const isActiveLink = (href: string) => page.url.pathname === href || page.url.pathname.startsWith(`${href}/`);
    const stop = (event: Event) => event.stopPropagation();
    let currentItem = $derived(navigation[role].flatMap(group => group.items).find(item => isActiveLink(item.href)));
    let title = $derived(currentItem?.label ?? (role === 'manager' ? 'Admission & Marketing Intelligence' : role === 'admin' ? 'Administration' : 'Student Portal'));
    onMount(async () => {
        try {
            const account = await api('/auth/me');
            if (!roleMatches(account.role)) { window.location.assign(destinations[account.role === 'student' ? 'student' : account.role === 'admin' ? 'admin' : 'manager']); return; }
            user = account;
        } catch (e) { error = (e as Error).message; }
    });
    async function logout() { try { await signOut(); window.location.assign('/login'); } catch (e) { error = (e as Error).message; } }
</script>

<svelte:window onclick={() => (menuOpen = false)} onkeydown={(event) => { if (event.key === 'Escape') menuOpen = false; }} />

{#if user}
<div class="role-effects flex h-screen bg-primary font-sans text-text-primary overflow-hidden" class:student-shell={student}>
    {#if mobileOpen}<button class="fixed inset-0 z-30 bg-black/30 md:hidden" aria-label="Close navigation" onclick={() => mobileOpen = false}></button>{/if}
    <aside class:translate-x-0={mobileOpen} class="fixed md:static inset-y-0 left-0 z-40 w-72 md:w-64 -translate-x-full md:translate-x-0 flex flex-col transition-transform duration-200 shrink-0 {student ? 'st-sidebar' : 'sh-sidebar'}">
        <div class="flex items-center {student ? 'st-brand px-5' : 'sh-brand'}">
            <a href="/" class="flex items-center gap-2.5">
                {#if student}<span class="st-brand-mark"><OutlineIcon name="cap" size={19} /></span><span class="st-brand-name">Decision<em>Intel</em></span>
                {:else}<span class="di-brand-mark sh-mark"><OutlineIcon name="cap" size={20} strokeWidth={1.8} /></span><span class="sh-brand-name">Decision<em>Intel</em></span>{/if}
            </a>
        </div>
        <nav class="flex-1 overflow-y-auto custom-scrollbar {student ? 'st-nav' : 'sh-nav'}" aria-label="Role navigation">
            {#each navigation[role] as group}
                <section>{#if group.label}<p class="{student ? 'st-nav-label' : 'sh-nav-label'}">{group.label}</p>{/if}
                {#each group.items as item}<a href={item.href} onclick={() => mobileOpen = false} class:nav-active={!student && isActiveLink(item.href)} class:st-active={student && isActiveLink(item.href)} class="{student ? 'st-nav-link' : 'nav-link'}">{#if student}<OutlineIcon name={item.outline ?? 'dashboard'} size={19} />{:else}<span class="nav-icon"><OutlineIcon name={item.outline ?? 'dashboard'} size={19} /></span>{/if}{item.label}</a>{/each}</section>
            {/each}
        </nav>
        {#if !student}<div class="sh-foot">
            <a class="nav-link" href={accountLinks.notifications}><span class="nav-icon"><OutlineIcon name="notifications" size={19} /></span>Notifications</a>
            <a class="nav-link" href={accountLinks.profile}><span class="nav-icon"><OutlineIcon name="profile" size={19} /></span>Profile</a>
            <a class="nav-link" href={accountLinks.settings}><span class="nav-icon"><OutlineIcon name="settings" size={19} /></span>Settings</a>
            <button class="nav-link danger w-full text-left" onclick={logout}><span class="nav-icon"><OutlineIcon name="logout" size={19} /></span>Logout</button>
        </div>{/if}
    </aside>
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header class="shrink-0 flex items-center px-4 md:px-8 justify-between {student ? 'st-header' : 'sh-header'}">
            <div class="flex items-center gap-3">
                {#if student}<button class="md:hidden inline-flex" onclick={() => mobileOpen = true} aria-label="Open navigation"><span class="st-icon-btn"><OutlineIcon name="menu" size={20} /></span></button>{:else}<button class="md:hidden sh-icon-btn" onclick={() => mobileOpen = true} aria-label="Open navigation"><OutlineIcon name="menu" size={20} /></button>{/if}
                <div>
                    <h2 class="{student ? 'st-header-title' : 'sh-title'}">{title}</h2>
                    <p class="hidden sm:block {student ? 'st-header-crumb' : 'sh-crumb'}">Decision-Intel / {title}</p>
                </div>
            </div>
            <div class="flex items-center gap-3 {student ? 'st-header-actions' : ''}">
                <ThemeToggle />
                <a href={accountLinks.notifications} class="{student ? 'st-icon-btn' : 'sh-icon-btn'}" aria-label="Notifications"><OutlineIcon name="notifications" size={18} /></a>
                {#if student}
                    <button class="st-profile-btn" aria-haspopup="menu" aria-expanded={menuOpen} onclick={(event) => { event.stopPropagation(); menuOpen = !menuOpen; }}>
                        <span class="st-avatar">{user.name.charAt(0).toUpperCase()}</span>
                        <span class="st-profile-name">{user.name}</span>
                        <span class="st-profile-caret"><OutlineIcon name="chevron-down" size={14} /></span>
                    </button>
                    {#if menuOpen}
                        <div class="st-menu" role="menu" tabindex="-1" onclick={stop} onkeydown={stop}>
                            <p class="st-menu-head"><span class="st-menu-name">{user.name}</span><span class="st-menu-mail">{user.email}</span></p>
                            <a class="st-menu-item" role="menuitem" href={accountLinks.profile}><OutlineIcon name="profile" size={18} />Profile</a>
                            <a class="st-menu-item" role="menuitem" href={accountLinks.notifications}><OutlineIcon name="notifications" size={18} />Notifications</a>
                            <a class="st-menu-item" role="menuitem" href={accountLinks.settings}><OutlineIcon name="settings" size={18} />Settings</a>
                            <button class="st-menu-item st-danger" role="menuitem" onclick={logout}><OutlineIcon name="logout" size={18} />Logout</button>
                        </div>
                    {/if}
                {:else}
                    <div class="sh-profile">
                        <button class="sh-profile-btn" aria-haspopup="menu" aria-expanded={menuOpen} onclick={(event) => { event.stopPropagation(); menuOpen = !menuOpen; }}>
                            <span class="sh-avatar">{user.name.charAt(0).toUpperCase()}</span>
                            <span class="sh-profile-name">{user.name}</span>
                            <span class="sh-caret"><OutlineIcon name="chevron-down" size={14} /></span>
                        </button>
                        {#if menuOpen}
                            <div class="sh-menu" role="menu" tabindex="-1" onclick={stop} onkeydown={stop}>
                                <p class="sh-menu-head"><span class="sh-menu-role">{role === 'manager' ? 'Manager' : 'Administrator'}</span><span class="sh-menu-name">{user.name}</span><span class="sh-menu-mail">{user.email}</span></p>
                                <a class="sh-menu-item" role="menuitem" href={accountLinks.profile}><OutlineIcon name="profile" size={18} />Profile</a>
                                <a class="sh-menu-item" role="menuitem" href={accountLinks.notifications}><OutlineIcon name="notifications" size={18} />Notifications</a>
                                <a class="sh-menu-item" role="menuitem" href={accountLinks.settings}><OutlineIcon name="settings" size={18} />Settings</a>
                                <button class="sh-menu-item sh-danger" role="menuitem" onclick={logout}><OutlineIcon name="logout" size={18} />Logout</button>
                            </div>
                        {/if}
                    </div>
                {/if}
            </div>
        </header>
        <div class="flex-1 overflow-auto relative custom-scrollbar {student ? 'st-content p-4 md:p-7 lg:p-8' : 'sh-content p-4 md:p-8'}">
            {#if !student}<div class="absolute top-0 right-0 w-125 h-125 bg-secondary/25 rounded-full blur-[100px] pointer-events-none z-0"></div>{/if}
            <div class="relative z-10 {student ? 'st-canvas' : ''}">{@render children()}</div>
        </div>
    </main>
</div>
{:else}<p class="p-8 text-text-secondary" role="status">{error || 'Authenticating…'} {#if error}<a href="/login" class="text-accent ml-2 hover:underline">Sign in</a>{/if}</p>{/if}

<style>
    .nav-link { display:flex; align-items:center; gap:.7rem; padding:.6rem .75rem; border-radius:.55rem; color:var(--color-text-secondary, #6f6979); font-size:.85rem; font-weight:500; transition:.2s; }
    .nav-link:hover { color:var(--di-accent-ink, #4E1D93); background:var(--di-accent-soft, #F3EBFC); }
    .nav-link.danger:hover { color:#A32B44; background:#FBEAEE; }
    .nav-active { color:var(--di-accent-ink, #4E1D93); background:var(--di-accent-soft, #F3EBFC); border:1px solid var(--di-accent-line, #E7D6FA); }
    :global(.custom-scrollbar::-webkit-scrollbar) { width:6px; }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background:rgba(106,49,196,.18); border-radius:10px; }

    /* ---- Manager / admin shell chrome (light theme) --------------- */
    .sh-sidebar { background-color:var(--di-surface, #fff); border-right:1px solid var(--di-border, #E9E4DC); }
    .sh-brand { height:5rem; padding:0 1.5rem; border-bottom:1px solid var(--di-border, #E9E4DC); }
    .sh-mark { width:2.125rem; height:2.125rem; border-radius:11px; }
    .sh-brand-name { font-size:1.2rem; font-weight:700; letter-spacing:.01em; color:var(--di-text, #262230); }
    .sh-brand-name em { font-family:Georgia,'Times New Roman',serif; font-style:italic; color:var(--di-accent, #6A31C4); }
    .sh-nav { padding:1.25rem .875rem; display:flex; flex-direction:column; gap:1.35rem; }
    .sh-nav-label { padding:0 .75rem; margin-bottom:.375rem; font-size:10px; font-weight:700; letter-spacing:.15em; text-transform:uppercase; color:var(--di-muted, #6F6979); }
    .nav-icon { display:inline-flex; flex:none; color:currentColor; opacity:.85; }
    .sh-foot { padding:1rem .875rem; border-top:1px solid var(--di-border, #E9E4DC); display:grid; gap:.25rem; }

    .sh-header { height:5rem; border-bottom:1px solid var(--di-border, #E9E4DC); background-color:rgba(247,245,242,.85); backdrop-filter:blur(12px); }
    .sh-title { font-size:1.125rem; font-weight:700; color:var(--di-text, #262230); }
    .sh-crumb { font-size:.75rem; color:var(--di-muted, #6F6979); }
    .sh-icon-btn {
        display:grid; place-items:center; width:2.25rem; height:2.25rem; flex:none;
        border-radius:10px; background-color:var(--di-surface, #fff);
        border:1px solid var(--di-border, #E9E4DC); color:var(--di-muted, #6F6979);
    }
    .sh-icon-btn:hover { color:var(--di-accent-ink, #4E1D93); background-color:var(--di-accent-soft, #F3EBFC); }

    .sh-profile { position:relative; }
    .sh-profile-btn {
        display:flex; align-items:center; gap:.5rem; padding:.3125rem .625rem .3125rem .3125rem;
        border-radius:999px; border:1px solid var(--di-border, #E9E4DC);
        background-color:var(--di-surface, #fff); font:inherit; cursor:pointer;
    }
    .sh-profile-btn:hover { border-color:var(--di-accent-line, #E7D6FA); background-color:var(--di-accent-soft, #F3EBFC); }
    .sh-avatar {
        display:grid; place-items:center; width:1.75rem; height:1.75rem; flex:none;
        border-radius:999px; background-image:var(--di-accent-sheen);
        color:#fff; font-size:.75rem; font-weight:700;
    }
    .sh-profile-name { font-size:.8125rem; font-weight:600; color:var(--di-text, #262230); max-width:9rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .sh-caret { display:inline-flex; color:var(--di-muted, #6F6979); }

    .sh-menu {
        position:absolute; right:0; top:calc(100% + .5rem); z-index:50; min-width:15rem;
        padding:.375rem; background-color:var(--di-surface, #fff);
        border:1px solid var(--di-border, #E9E4DC); border-radius:var(--di-radius, 16px);
        box-shadow:var(--di-shadow-lift, 0 20px 38px -24px rgba(38,34,48,.45));
    }
    .sh-menu-head { display:grid; gap:.125rem; padding:.625rem .75rem .75rem; border-bottom:1px solid var(--di-border, #E9E4DC); margin-bottom:.25rem; }
    .sh-menu-role { font-size:.625rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--di-accent, #6A31C4); }
    .sh-menu-name { font-size:.875rem; font-weight:650; color:var(--di-text, #262230); }
    .sh-menu-mail { font-size:.75rem; color:var(--di-muted, #6F6979); overflow:hidden; text-overflow:ellipsis; }
    .sh-menu-item {
        display:flex; align-items:center; gap:.625rem; width:100%; padding:.5rem .75rem;
        border-radius:.5rem; font:inherit; font-size:.8125rem; font-weight:600;
        color:var(--di-text, #262230); background:none; border:0; cursor:pointer; text-align:left; text-decoration:none;
    }
    .sh-menu-item:hover { background-color:var(--di-accent-soft, #F3EBFC); color:var(--di-accent-ink, #4E1D93); }
    .sh-menu-item.sh-danger { color:#A32B44; }
    .sh-menu-item.sh-danger:hover { background-color:#FBEAEE; }

    @media (max-width: 640px) {
        .sh-profile-name, .sh-caret { display:none; }
        .sh-brand { padding:0 1.25rem; }
    }
</style>
