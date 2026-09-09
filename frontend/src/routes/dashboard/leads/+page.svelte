<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import DataTable from '$lib/DataTable.svelte';
    let rows = $state<Record<string, unknown>[]>([]), prediction = $state<Record<string, unknown> | null>(null), selected = $state(''), skip = $state(0), busy = $state(false), error = $state(''), notice = $state('');
    async function load(offset = skip) { busy = true; error = ''; try { rows = await api(`/leads?skip=${offset}&limit=50`); skip = offset; } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    async function inspect(event: SubmitEvent) { event.preventDefault(); busy = true; error = ''; notice = ''; prediction = null; try { prediction = await api(`/leads/${encodeURIComponent(selected)}/prediction`); if (!prediction) notice = 'No prediction has been generated for this lead.'; } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    onMount(() => { void load(); });
</script>
<svelte:head><title>Leads & predictions | DecisionIntel</title></svelte:head>
<h1 class="text-3xl font-bold mb-3">Leads & predictions</h1><p class="text-text-secondary mb-6">Browse stored marketing leads and inspect their available predictions.</p>
{#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}
<div class="flex gap-4 items-center mb-6"><button class="bg-secondary px-4 py-2 rounded-lg" disabled={busy || skip === 0} onclick={() => load(Math.max(0,skip-50))}>Previous</button><span>Page {skip / 50 + 1}</span><button class="bg-secondary px-4 py-2 rounded-lg" disabled={busy || rows.length < 50} onclick={() => load(skip+50)}>Next</button><button class="bg-secondary px-4 py-2 rounded-lg" disabled={busy} onclick={() => load()}>Refresh</button></div>
{#if busy}<p role="status">Loading…</p>{/if}<DataTable {rows} empty="No leads found. Import marketing leads into the backend to see them here." />
{#if rows.length}<form class="mt-8 flex gap-3 flex-wrap items-end" onsubmit={inspect}><label>Lead<select class="block bg-card border border-white/20 rounded-lg p-3 mt-2" bind:value={selected} required><option value="" disabled>Select a lead</option>{#each rows as row}<option value={String(row.id)}>{row.customer_id || row.id}</option>{/each}</select></label><button class="bg-cta text-black rounded-lg p-3" disabled={busy}>View prediction</button></form>{/if}
{#if notice}<p role="status" class="mt-5">{notice}</p>{/if}{#if prediction}<section class="mt-6"><h2 class="text-xl mb-3">Prediction details</h2><DataTable rows={[prediction]} /></section>{/if}
