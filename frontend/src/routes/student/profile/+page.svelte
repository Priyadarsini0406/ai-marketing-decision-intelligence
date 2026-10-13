<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type User } from '$lib/api';
    let user = $state<User | null>(null), editing = $state(false), saved = $state(false), busy = $state(false), error = $state('');
    let profile = $state<Record<string, string>>({});
    const fields = [
        ['mobile', 'Phone'], ['qualification', 'Highest Qualification'], ['institution', 'Institution'],
        ['completion_year', 'Completion Year'], ['course_interested', 'Interested Course'],
        ['city', 'City'], ['district', 'District'], ['state', 'State'], ['pincode', 'PIN Code']
    ];
    onMount(async () => {
        try { user = await api('/auth/me'); profile = Object.fromEntries(fields.map(([key]) => [key, String(user?.profile?.[key] ?? '')])); }
        catch { window.location.assign('/login'); }
    });
    async function save() {
        if (!user) return;
        busy = true; error = ''; saved = false;
        try {
            user = await api('/student/profile', { method: 'PUT', body: JSON.stringify({ name: user.name, profile: { ...(user.profile ?? {}), ...profile } }) });
            profile = Object.fromEntries(fields.map(([key]) => [key, String(user?.profile?.[key] ?? '')]));
            editing = false; saved = true;
        } catch (e) { error = (e as Error).message; }
        finally { busy = false; }
    }
</script>

{#if user}<div class="max-w-4xl space-y-6">
    <div class="flex justify-between"><div><h1 class="text-3xl font-bold text-white">My Profile</h1><p class="text-text-secondary mt-2">Your saved account and admission details.</p></div><button onclick={() => editing = !editing} class="px-4 py-2 rounded-xl bg-secondary border border-accent/30 text-white text-sm">{editing ? 'Cancel' : 'Edit Profile'}</button></div>
    {#if saved}<p role="status" class="text-sm p-3 rounded-xl bg-green-500/10 text-green-400 border border-green-500/20">Profile changes saved.</p>{/if}
    {#if error}<p role="alert" class="text-sm text-red-400">{error}</p>{/if}
    <div class="bg-card border border-white/10 rounded-2xl p-6 space-y-7">
        <section><h2 class="section-title">Personal Information</h2><div class="grid sm:grid-cols-2 gap-4"><label>Full Name<input disabled={!editing} bind:value={user.name}/></label><label>Email<input disabled value={user.email}/></label>{#each fields as [key, label]}<label>{label}<input disabled={!editing} bind:value={profile[key]} /></label>{/each}</div></section>
        {#if editing}<button disabled={busy} onclick={save} class="px-5 py-3 bg-cta text-white rounded-xl font-bold text-sm">{busy ? 'Saving…' : 'Save Changes'}</button>{/if}
    </div>
</div>{/if}
<style>
    label{display:flex;flex-direction:column;gap:.45rem;font-size:.75rem;color:var(--di-muted)}input{background:var(--di-surface);border:1px solid rgba(91,33,182,.14);border-radius:.6rem;padding:.7rem .85rem;color:var(--di-text);font-size:.875rem}.section-title{font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;color:var(--di-accent-ink);font-weight:bold;margin-bottom:1rem}
</style>
