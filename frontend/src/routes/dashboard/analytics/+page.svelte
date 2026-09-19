<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import DataTable from '$lib/DataTable.svelte';
    let rows = $state<Record<string, unknown>[]>([]), error = $state(''), busy = $state(false);
    async function load() { busy = true; error = ''; try { rows = await api('/analytics/channels'); } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    onMount(load);
</script>
<svelte:head><title>Attribution & segments | DecisionIntel</title></svelte:head>
<h1 class="text-3xl font-bold mb-3">Attribution & segments</h1><p class="text-text-secondary mb-6">Stored channel performance, acquisition costs, and conversion rates. Lead-level segment information is available with each prediction.</p>
<div class="flex gap-4 items-center mb-6"><button class="bg-secondary px-4 py-2 rounded-lg" onclick={load} disabled={busy}>{busy ? 'Loading…' : 'Refresh'}</button><a class="text-accent" href="/dashboard/leads">View lead predictions and segments →</a></div>
{#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}<DataTable {rows} empty="No channel metrics have been stored yet." />
