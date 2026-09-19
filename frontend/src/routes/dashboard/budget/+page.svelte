<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import DataTable from '$lib/DataTable.svelte';
    let rows = $state<Record<string, unknown>[]>([]), error = $state(''), busy = $state(false);
    async function load() { busy = true; error = ''; try { rows = await api('/budget/simulations'); } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    onMount(load);
</script>
<svelte:head><title>Budget simulator | DecisionIntel</title></svelte:head>
<h1 class="text-3xl font-bold mb-3">Budget simulator</h1><p class="text-text-secondary mb-6">Review saved budget allocations, predicted conversions, and acquisition costs.</p>
<button class="bg-secondary px-4 py-2 rounded-lg mb-6" onclick={load} disabled={busy}>{busy ? 'Loading…' : 'Refresh'}</button>
{#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}<DataTable {rows} empty="No budget simulations have been saved yet." />
<p class="text-text-secondary mt-6"><a class="text-accent" href="/dashboard/simulator">Create a what-if scenario ?</a></p>
