<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type User } from '$lib/api';
    let users = $state<User[]>([]), editing = $state(''), name = $state(''), email = $state(''), password = $state(''), role = $state('marketer'), active = $state(true), error = $state(''), message = $state(''), busy = $state(false), loading = $state(true);
    const roles = ['marketer', 'data_scientist', 'executive', 'admin'];
    async function load() { users = await api('/admin/users'); }
    onMount(async () => { try { await load(); } catch(e) { error = (e as Error).message; } finally { loading = false; } });
    function reset() { editing = ''; name = ''; email = ''; password = ''; role = 'marketer'; active = true; }
    function edit(user: User) { editing = user.id; name = user.name; email = user.email; role = user.role; active = user.active; password = ''; message = ''; }
    async function save(event: SubmitEvent) {
        event.preventDefault(); busy = true; error = ''; message = '';
        try {
            await api(editing ? `/admin/users/${editing}` : '/admin/users', { method: editing ? 'PUT' : 'POST', body: JSON.stringify({ name, email, role, active, ...(password ? { password } : {}) }) });
            message = editing ? 'User updated. Their previous sessions have been revoked.' : 'Account created. This user can now sign in.';
            reset(); await load();
        } catch(e) { error = (e as Error).message; } finally { busy = false; }
    }
</script>
<svelte:head><title>Manage users | DecisionIntel</title></svelte:head>
<h1>Manage users</h1><p>Create working accounts and control platform access. Deactivation prevents login immediately.</p>
{#if error}<p role="alert">{error}</p>{/if}{#if message}<p role="status">{message}</p>{/if}
<div class="panel"><h2>{editing ? 'Edit account' : 'Create account'}</h2>
<form onsubmit={save}><div class="grid">
    <label>Full name<input bind:value={name} required maxlength="100" /></label>
    <label>Email<input type="email" bind:value={email} required disabled={!!editing} /></label>
    <label>{editing ? 'New password (optional)' : 'Password'}<input type="password" bind:value={password} required={!editing} minlength="12" maxlength="128" autocomplete="new-password" /></label>
    <label>Role<select bind:value={role}>{#each roles as value}<option {value}>{value.replace('_', ' ')}</option>{/each}</select></label>
</div>{#if editing}<label><input type="checkbox" bind:checked={active} />Account active</label>{/if}
<small>Passwords require at least 12 characters. Editing your own account requires signing in again.</small>
<div class="actions"><button disabled={busy}>{busy ? 'Saving…' : editing ? 'Save changes' : 'Create user'}</button>{#if editing}<button type="button" class="secondary" onclick={reset}>Cancel</button>{/if}</div>
</form></div>
<div class="panel table-wrap"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody>
{#each users as user}<tr><td>{user.name}</td><td>{user.email}</td><td>{user.role}</td><td>{user.active ? 'Active' : 'Inactive'}</td><td><button class="secondary" onclick={() => edit(user)}>Edit</button></td></tr>{:else}<tr><td colspan="5">{loading ? 'Loading users…' : 'No users found.'}</td></tr>{/each}
</tbody></table></div>
