<script lang="ts">
    import { onMount } from 'svelte';
    import { signIn } from '$lib/api';
    let email = $state(''), password = $state(''), error = $state(''), busy = $state(false);
    let ready = $state(false);
    onMount(() => { ready = true; });
    async function submit(event: SubmitEvent) {
        event.preventDefault(); busy = true; error = '';
        try { await signIn(email, password, true); }
        catch (e) { error = (e as Error).message; }
        finally { busy = false; }
    }
</script>
<svelte:head><title>Admin login | DecisionIntel</title></svelte:head>
<section class="login-card">
    <a href="/">DecisionIntel</a>
    <p class="eyebrow">ADMINISTRATION</p>
    <h1>Admin login</h1>
    <p>Manage your team, marketing datasets, and platform settings.</p>
    <form onsubmit={submit}>
        <label>Email<input type="email" bind:value={email} required autocomplete="username" disabled={!ready || busy} /></label>
        <label>Password<input type="password" bind:value={password} required autocomplete="current-password" maxlength="128" disabled={!ready || busy} /></label>
        {#if error}<p role="alert">{error}</p>{/if}
        <button disabled={!ready || busy}>{busy ? 'Signing in…' : 'Sign in as administrator'}</button>
    </form>
    <p>Use the account created by your platform administrator.</p>
    <a href="/login">Return to user login</a>
</section>
