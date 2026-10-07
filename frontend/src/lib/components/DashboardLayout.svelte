<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { api, signOut, type User } from '$lib/api';
    import OutlineIcon from '$lib/components/OutlineIcon.svelte';
    import DashboardHeader from '$lib/components/DashboardHeader.svelte';
    import type { ShellRole } from '$lib/dashboard-header';

    let { role, children }: { role: ShellRole; children: import('svelte').Snippet } = $props();
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
    let user = $state<User | null>(null);
    let error = $state('');
    let mobileOpen = $state(false);
    const roleMatches = (value: string) => role === 'manager' ? value === 'admission_manager' || value === 'marketing_manager' : value === role;
    const isActiveLink = (href: string) => page.url.pathname === href || page.url.pathname.startsWith(`${href}/`);
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
    </aside>
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <DashboardHeader
            {role}
            {title}
            name={user.name}
            email={user.email}
            onlogout={logout}
            onopennav={() => (mobileOpen = true)}
        />
        <div class="flex-1 overflow-auto relative custom-scrollbar {student ? 'st-content p-4 md:p-7 lg:p-8' : 'sh-content p-4 md:p-8'}">
            {#if !student}<div class="absolute top-0 right-0 w-125 h-125 bg-secondary/25 rounded-full blur-[100px] pointer-events-none z-0"></div>{/if}
            <div class="relative z-10 {student ? 'st-canvas' : ''}">{@render children()}</div>
        </div>
    </main>
</div>
{:else}<p class="p-8 text-text-secondary" role="status">{error || 'Authenticating…'} {#if error}<a href="/login" class="text-accent ml-2 hover:underline">Sign in</a>{/if}</p>{/if}

<style>
    .nav-link { display:flex; align-items:center; gap:.7rem; padding:.6rem .75rem; border-radius:.55rem; color:var(--color-text-secondary, #6f6979); font-size:.85rem; font-weight:500; transition:.2s; }
    .nav-link:hover { color:var(--di-accent-ink, #5B21B6); background:var(--di-accent-soft, #F1EAFD); }
    .nav-active { color:var(--di-accent-ink, #5B21B6); background:var(--di-accent-soft, #F1EAFD); border:1px solid var(--di-accent-line, #DDD0F7); }
    :global(.custom-scrollbar::-webkit-scrollbar) { width:6px; }
    :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background:rgba(91,33,182,.18); border-radius:10px; }

    /* ---- Manager / admin shell chrome (light theme) --------------- */
    .sh-sidebar { background-color:var(--di-surface, #fff); border-right:1px solid var(--di-border, #E9E4DC); }
    .sh-brand { height:5rem; padding:0 1.5rem; border-bottom:1px solid var(--di-border, #E9E4DC); }
    .sh-mark { width:2.125rem; height:2.125rem; border-radius:11px; }
    .sh-brand-name { font-size:1.2rem; font-weight:700; letter-spacing:.01em; color:var(--di-text, #262230); }
    .sh-brand-name em { font-family:Georgia,'Times New Roman',serif; font-style:italic; color:var(--di-accent, #6D28D9); }
    .sh-nav { padding:1.25rem .875rem; display:flex; flex-direction:column; gap:1.35rem; }
    .sh-nav-label { padding:0 .75rem; margin-bottom:.375rem; font-size:10px; font-weight:700; letter-spacing:.15em; text-transform:uppercase; color:var(--di-muted, #6F6979); }
    .nav-icon { display:inline-flex; flex:none; color:currentColor; opacity:.85; }

    @media (max-width: 640px) {
        .sh-brand { padding:0 1.25rem; }
    }
</style>
