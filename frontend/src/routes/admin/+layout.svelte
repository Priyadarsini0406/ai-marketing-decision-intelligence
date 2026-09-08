<script lang="ts">
    import { afterNavigate } from '$app/navigation';
    import { page } from '$app/state';
    import { api, signOut, type User } from '$lib/api';
    import { adminPages } from '$lib/admin-navigation';
    import './admin.css';
    let { children } = $props();
    let user = $state<User | null>(null), error = $state('');
    let accessCheck = 0;
    afterNavigate(async () => {
        const check = ++accessCheck;
        if (page.url.pathname === '/admin/login') { user = null; error = ''; return; }
        try {
            const account: User = await api('/auth/me');
            if (check !== accessCheck) return;
            if (account.role !== 'admin') { user = null; error = 'Administrator access required.'; }
            else { user = account; error = ''; }
        }
        catch (e) { if (check === accessCheck) { user = null; error = (e as Error).message; } }
    });
    async function logout() {
        try { await signOut(); window.location.assign('/admin/login'); }
        catch (e) { error = (e as Error).message; }
    }
</script>
{#if page.url.pathname === '/admin/login'}
    {@render children()}
{:else if user}
    <div class="admin-shell">
        <aside><a class="brand" href="/admin">DecisionIntel <small>ADMIN</small></a>
            <nav aria-label="Administration">{#each adminPages as item}<a href={item.href} aria-current={page.url.pathname === item.href ? 'page' : undefined}>{item.label}</a>{/each}</nav>
            <a href="/dashboard">Marketing dashboard ↗</a>
            <p>{user.name}<br /><small>{user.email}</small></p><button class="secondary" onclick={logout}>Sign out</button>
        </aside>
        <main>{#if error}<p role="alert">{error}</p>{/if}{@render children()}</main>
    </div>
{:else}
    <div class="login-card"><p role="status">{error || 'Checking administrator access…'}</p>{#if error}<a href="/admin/login">Go to admin login</a>{/if}</div>
{/if}
