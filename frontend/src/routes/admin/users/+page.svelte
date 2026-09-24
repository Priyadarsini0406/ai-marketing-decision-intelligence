<script lang="ts">
    import { onMount, tick } from 'svelte';
    import { api, type User } from '$lib/api';
    let users = $state<User[]>([]), editing = $state(''), name = $state(''), email = $state(''), password = $state(''), role = $state('student'), active = $state(true), error = $state(''), message = $state(''), busy = $state(false), loading = $state(true);
    let editor: HTMLDivElement;
    let nameInput: HTMLInputElement;
    const roles = ['student', 'admission_manager', 'marketing_manager', 'admin'];
    let search = $state(''), roleFilter = $state('all'), statusFilter = $state('all');
    const filteredUsers = $derived(users.filter(user => (roleFilter === 'all' || user.role === roleFilter) && (statusFilter === 'all' || user.active === (statusFilter === 'active')) && `${user.name} ${user.email}`.toLowerCase().includes(search.toLowerCase())));
    async function refresh() { loading = true; error = ''; try { await load(); } catch(e) { error = (e as Error).message; } finally { loading = false; } }
    async function load() { users = await api('/admin/users'); }
    onMount(async () => { try { await load(); } catch(e) { error = (e as Error).message; } finally { loading = false; } });
    function reset() { editing = ''; name = ''; email = ''; password = ''; role = 'student'; active = true; }
    async function edit(user: User) {
        if (busy) return;
        editing = user.id; name = user.name; email = user.email; role = user.role; active = user.active;
        password = ''; message = ''; error = '';
        await tick();
        editor.scrollIntoView({ behavior: 'instant', block: 'start' });
        nameInput.focus({ preventScroll: true });
    }
    async function save(event: SubmitEvent) {
        event.preventDefault(); busy = true; error = ''; message = '';
        try {
            await api(editing ? `/admin/users/${editing}` : '/admin/users', { method: editing ? 'PUT' : 'POST', body: JSON.stringify({ name, email, role, active, ...(password ? { password } : {}) }) });
            message = editing ? 'User updated. Their previous sessions have been revoked.' : 'Account created. This user can now sign in.';
            reset(); await load();
        } catch(e) { error = (e as Error).message; } finally { busy = false; }
    }
</script>
<svelte:head><title>User Accounts | DecisionIntel</title></svelte:head>
<p class="eyebrow">USER MANAGEMENT</p><h1>User Accounts</h1><p>Create working accounts and control platform access. Deactivation prevents login immediately.</p>
<div class="stats"><section><span>Total accounts</span><strong>{users.length}</strong></section><section><span>Students</span><strong>{users.filter(user => user.role === 'student').length}</strong></section><section><span>Managers</span><strong>{users.filter(user => user.role === 'admission_manager' || user.role === 'marketing_manager').length}</strong></section><section><span>Active accounts</span><strong>{users.filter(user => user.active).length}</strong></section></div>
{#if error}<p role="alert">{error}</p>{/if}{#if message}<p role="status">{message}</p>{/if}
<div class="panel account-editor" id="account-editor" bind:this={editor}><h2>{editing ? 'Edit account' : 'Create account'}</h2>
<form onsubmit={save}><fieldset disabled={busy}><div class="grid">
    <label>Full name<input bind:this={nameInput} bind:value={name} required maxlength="100" /></label>
    <label>Email<input type="email" bind:value={email} required readonly={!!editing} />{#if editing}<small>The sign-in email cannot be changed here.</small>{/if}</label>
    <label>{editing ? 'New password (optional)' : 'Password'}<input type="password" bind:value={password} required={!editing} minlength="12" maxlength="128" autocomplete="new-password" /></label>
    <label>Role<select bind:value={role}>{#each roles as value}<option {value}>{value.replace('_', ' ')}</option>{/each}</select></label>
</div>{#if editing}<label><input type="checkbox" bind:checked={active} />Account active</label>{/if}
<small>Passwords require at least 12 characters. Editing your own account requires signing in again.</small>
<div class="actions"><button disabled={busy}>{busy ? 'Saving…' : editing ? 'Save changes' : 'Create user'}</button>{#if editing}<button type="button" class="secondary" disabled={busy} onclick={reset}>Cancel</button>{/if}</div>
</fieldset></form></div>
<div class="panel"><h2>Account directory</h2><div class="filters"><label>Search accounts<input type="search" bind:value={search} placeholder="Name or email" /></label><div><label for="account-role">Filter by role</label><select id="account-role" bind:value={roleFilter}><option value="all">All roles</option>{#each roles as value}<option {value}>{value.replaceAll('_',' ')}</option>{/each}</select></div><div><label for="account-status">Filter by status</label><select id="account-status" bind:value={statusFilter}><option value="all">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select></div><button type="button" class="secondary" disabled={loading || busy} onclick={refresh}>Refresh accounts</button></div><p class="count">{filteredUsers.length} of {users.length} accounts</p><div class="table-wrap"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody>
{#each filteredUsers as user}<tr class:editing-row={editing === user.id}><td>{user.name}</td><td>{user.email}</td><td>{user.role}</td><td>{user.active ? 'Active' : 'Inactive'}</td><td><button type="button" class="secondary" disabled={busy} aria-controls="account-editor" aria-pressed={editing === user.id} onclick={() => edit(user)}>{editing === user.id ? 'Editing' : 'Edit'}</button></td></tr>{:else}<tr><td colspan="5">{loading ? 'Loading users…' : 'No accounts match these filters.'}</td></tr>{/each}
</tbody></table></div></div>

<style>
.account-editor{scroll-margin-top:20px}.editing-row{background:#a47be012}fieldset{min-width:0;border:0;padding:0;margin:0}input[readonly]{opacity:.65}fieldset:disabled{opacity:.65}

h1{font-size:30px;font-weight:700;margin:8px 0}h2{font-size:18px;font-weight:650;margin-bottom:18px}p{font-size:14px;color:#aaa0b7;line-height:1.7}.eyebrow{font-size:10px;color:#b99bd9;letter-spacing:.18em}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:24px 0}.stats section,.panel{background:var(--color-card,#1c1724);border:1px solid #ffffff16;border-radius:16px;padding:22px;min-width:0}.stats span{font-size:12px;color:#aaa0b7}.stats strong{display:block;font-size:28px;margin-top:10px}.panel{margin:22px 0}.grid,.filters{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.filters{grid-template-columns:2fr 1fr 1fr auto;align-items:end}label{display:block;font-size:12px;color:#b9adc6}input,select{width:100%;min-width:0;background:#110d19;border:1px solid #ffffff24;border-radius:8px;padding:11px 13px;color:white;margin-top:8px}input[type=checkbox]{width:auto;margin:18px 8px 0 0}small{display:block;color:#a79ab8;font-size:11px;margin:16px 0}.actions{display:flex;gap:10px;margin-top:20px;flex-wrap:wrap}button{padding:10px 14px;background:#a47be0;color:#160f20;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer}.secondary{background:#ffffff08;color:#d9cbe9;border:1px solid #ffffff20}button:disabled{opacity:.5;cursor:default}.table-wrap{overflow:auto}table{width:100%;text-align:left;font-size:13px;border-collapse:collapse}th,td{padding:15px 12px;border-bottom:1px solid #ffffff10;white-space:nowrap}th{font-size:11px;color:#a79ab8;text-transform:uppercase}.count{font-size:11px;margin:18px 0}[role=alert]{color:#f2a5b4}[role=status]{color:#a6d5b9}button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}@media(max-width:900px){.filters{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.grid,.filters{grid-template-columns:minmax(0,1fr)}.panel{padding:16px}}
</style>
