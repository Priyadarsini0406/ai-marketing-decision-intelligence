<script lang="ts">
    import '$lib/module-theme.css';
    import AccountMenu from '$lib/AccountMenu.svelte';
    import { afterNavigate } from '$app/navigation';
    import { page } from '$app/state';
    import { api, type User } from '$lib/api';
    import { adminPages } from '$lib/admin-navigation';
    import './admin.css';
    let { children } = $props();
    let user = $state<User | null>(null), error = $state('');
    let accessCheck = 0;
    afterNavigate(async () => {
        const check = ++accessCheck;
        try {
            const account: User = await api('/auth/me');
            if (check !== accessCheck) return;
            if (account.role !== 'admin') { user = null; error = 'Administrator access required.'; }
            else { user = account; error = ''; }
        }
        catch (e) { if (check === accessCheck) { user = null; error = (e as Error).message; } }
    });
</script>
{#if user}
    <div class="admin-shell module-shell">
        <aside><a class="brand" href="/admin">DecisionIntel <small>ADMIN</small></a>
            <nav aria-label="Administration">{#each adminPages as item}<a href={item.href} aria-current={page.url.pathname === item.href ? 'page' : undefined}>{item.label}</a>{/each}</nav>
            <a href="/dashboard">Marketing dashboard ↗</a>
            
        </aside>
        <main><header class="account-header"><span>Admin dashboard</span><AccountMenu {user} /></header>{#if error}<p role="alert">{error}</p>{/if}{@render children()}</main>
    </div>
{:else}
    <div class="login-card"><p role="status">{error || 'Checking administrator access…'}</p>{#if error}<a href="/login">Go to sign in</a>{/if}</div>
{/if}

<style>
.account-header{position:relative;z-index:40;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0 0 22px;margin-bottom:28px;color:var(--color-text-secondary);}
</style>
