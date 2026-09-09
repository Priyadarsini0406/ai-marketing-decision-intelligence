<script lang="ts">
    import { onMount } from 'svelte';
    import { api, signOut, type User } from '$lib/api';
    let user = $state<User | null>(null), error = $state(''), busy = $state(false);
    onMount(async () => { try { user = await api('/auth/me'); } catch(e) { error = (e as Error).message; } });
    async function logout() {
        busy = true; error = '';
        try { await signOut(); window.location.assign('/login'); }
        catch(e) { error = (e as Error).message; busy = false; }
    }
</script>

<svelte:head><title>My account | DecisionIntel</title></svelte:head>
<div class="account-page">
    <h1>My account</h1>
    <p>Your profile details and account access.</p>
    {#if error}<p role="alert">{error}</p>{/if}
    {#if user}
        <section class="workspace-panel panel">
            <div class="identity"><span class="profile-circle" aria-hidden="true">{user.name.trim().split(/\s+/).slice(0,2).map(part => part[0]).join('').toUpperCase()}</span><h2>{user.name}</h2></div>
            <dl><dt>Full name</dt><dd>{user.name}</dd><dt>Email</dt><dd>{user.email}</dd><dt>Role</dt><dd class="role">{user.role.replaceAll('_',' ')}</dd><dt>Account status</dt><dd>{user.active ? 'Active' : 'Inactive'}</dd></dl>
            <div class="account-actions"><a href={user.role === 'admin' ? '/admin' : '/dashboard'}>{user.role === 'admin' ? 'Admin dashboard' : 'My dashboard'} &rarr;</a><button onclick={logout} disabled={busy}>{busy ? 'Signing out...' : 'Sign out'}</button></div>
        </section>
    {:else if !error}<p role="status">Loading account...</p>{/if}
</div>

<style>
    .account-page{max-width:720px;margin:0 auto}.account-page h1{font-size:30px;font-weight:700;margin-bottom:12px}.account-page p{color:var(--color-text-secondary);margin-bottom:24px}
    .panel{padding:28px;border:1px solid #a47be040;border-radius:20px;background:var(--color-secondary);margin-top:24px}
    .identity{display:flex;gap:18px;align-items:center;margin-bottom:28px}.identity h2{font-size:22px;font-weight:600;overflow-wrap:anywhere;min-width:0;margin:0}
    .profile-circle{display:grid;place-items:center;flex-shrink:0;width:64px;height:64px;background:var(--color-cta);color:var(--color-primary);font-weight:700;font-size:22px;border-radius:50%;box-shadow:0 0 25px #f2a62b20}
    dl{display:grid;grid-template-columns:130px minmax(0,1fr);gap:16px;margin-bottom:28px}dt{color:var(--color-text-secondary)}dd{overflow-wrap:anywhere;color:var(--color-text-primary)}.role{text-transform:capitalize}
    .account-actions{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;border-top:1px solid #ffffff15;padding-top:22px}.account-actions a{color:var(--color-accent)}.account-actions button{padding:10px 18px;border-radius:9px;background:var(--color-cta);color:var(--color-primary);font-weight:600;cursor:pointer}.account-actions button:disabled{opacity:.6}
    .account-page [role=alert]{color:#ffadb9}@media(max-width:600px){dl{grid-template-columns:minmax(0,1fr);gap:8px}dd{margin-bottom:12px}.panel{padding:18px}}
</style>
