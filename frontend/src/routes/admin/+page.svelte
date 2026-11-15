<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    let summary = $state<Record<string, number> | null>(null), error = $state('');
    onMount(async () => { try { summary = (await api('/admin/reports')).summary; } catch(e) { error = (e as Error).message; } });
</script>
<svelte:head><title>Admin overview | DecisionIntel</title></svelte:head>
<h1>Administration</h1><p>Your team, data, and system in one place.</p>
{#if error}<p role="alert">{error}</p>{:else if summary}
<div class="grid">{#each [['Users', summary.users], ['Datasets', summary.datasets], ['Dataset rows', summary.dataset_rows], ['Admission leads', summary.leads]] as [label, value]}<div class="stat">{label}<strong>{value}</strong></div>{/each}</div>
{:else}<p>Loading overview…</p>{/if}
<div class="grid">
    <a class="panel" href="/admin/users"><h2>Manage users →</h2><p>Create accounts, assign roles, reset passwords, and deactivate access.</p></a>
    <a class="panel" href="/admin/datasets"><h2>Student Admission Datasets →</h2><p>Upload, preview, rename, and remove CSV datasets.</p></a>
    <a class="panel" href="/admin/configuration"><h2>System / model configuration →</h2><p>Manage report settings and save model parameters.</p></a>
    <a class="panel" href="/admin/reports"><h2>Analytics & reports →</h2><p>View stored analytics and export a complete report.</p></a>
</div>

<style>
    h1 { font-size: 30px; font-weight: 700; margin: 8px 0; color: var(--di-text); }
    h2 { font-size: 18px; font-weight: 650; margin: 0 0 6px; color: var(--di-text); }
    p { font-size: 14px; color: var(--di-muted); line-height: 1.6; margin: 6px 0; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 18px; margin: 20px 0; }
    .stat, .panel {
        background: var(--di-surface);
        border: 1px solid var(--di-border);
        border-radius: 16px;
        padding: 22px;
        box-shadow: var(--di-shadow);
        color: var(--di-text);
        text-decoration: none;
        display: block;
        transition: transform 200ms ease, border-color 200ms ease, box-shadow 200ms ease;
    }
    .stat { color: var(--di-muted); font-size: 13px; }
    .stat strong { display: block; font-size: 30px; font-weight: 700; color: var(--di-text); margin-top: 8px; }
    .panel:hover {
        transform: translateY(-2px);
        border-color: var(--di-accent-line);
        box-shadow: var(--di-shadow-lift);
    }
    .panel h2 { color: var(--di-accent-ink); }
    .panel:hover h2 { color: var(--di-accent); }
    [role=alert] { color: var(--di-red-ink); }
</style>
