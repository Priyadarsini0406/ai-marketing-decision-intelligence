<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    let summary = $state<Record<string, number> | null>(null), error = $state('');
    onMount(async () => { try { summary = (await api('/admin/reports')).summary; } catch(e) { error = (e as Error).message; } });
</script>
<svelte:head><title>Admin overview | DecisionIntel</title></svelte:head>
<h1>Administration</h1><p>Your team, data, and system in one place.</p>
{#if error}<p role="alert">{error}</p>{:else if summary}
<div class="grid">{#each [['Users', summary.users], ['Datasets', summary.datasets], ['Dataset rows', summary.dataset_rows], ['Marketing leads', summary.leads]] as [label, value]}<div class="stat">{label}<strong>{value}</strong></div>{/each}</div>
{:else}<p>Loading overview…</p>{/if}
<div class="grid">
    <a class="panel" href="/admin/users"><h2>Manage users →</h2><p>Create accounts, assign roles, reset passwords, and deactivate access.</p></a>
    <a class="panel" href="/admin/datasets"><h2>Marketing datasets →</h2><p>Upload, preview, rename, and remove CSV datasets.</p></a>
    <a class="panel" href="/admin/configuration"><h2>System / model configuration →</h2><p>Manage report settings and save model parameters.</p></a>
    <a class="panel" href="/admin/reports"><h2>Analytics & reports →</h2><p>View stored analytics and export a complete report.</p></a>
</div>
