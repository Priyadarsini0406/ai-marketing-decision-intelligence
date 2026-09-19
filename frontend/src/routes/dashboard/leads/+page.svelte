<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import DataTable from '$lib/DataTable.svelte';
    let search = $state(''), editing = $state(false), editingId = $state('');
    const defaults = {customer_id:'',age:30,gender:'Female',income:0,campaign_channel:'Email',campaign_type:'Awareness',ad_spend:0,click_through_rate:0,conversion_rate:0,website_visits:0,pages_per_visit:0,time_on_site:0,social_shares:0,email_opens:0,email_clicks:0,previous_purchases:0,loyalty_points:0};
    let draft = $state<Record<string, string | number>>({...defaults}), outcome = $state('unknown');
    function edit() { const lead = rows.find(row => row.id === selected); if (!lead) return; editingId = selected; draft = Object.fromEntries(Object.keys(defaults).map(key => [key, (lead[key] ?? defaults[key as keyof typeof defaults]) as string | number])); outcome = lead.conversion == null ? 'unknown' : lead.conversion ? 'yes' : 'no'; editing = true; }
    async function save(event: SubmitEvent) { event.preventDefault(); busy = true; error = ''; try { await api(editingId ? `/leads/${editingId}` : '/leads', {method:editingId ? 'PUT' : 'POST',body:JSON.stringify({...draft,conversion:outcome === 'unknown' ? null : outcome === 'yes'})}); editing = false; prediction = null; notice = 'Lead saved. Run a new prediction for updated features.'; await load(0); } catch(e) {error = (e as Error).message;} finally {busy = false;} }
    let rows = $state<Record<string, unknown>[]>([]), prediction = $state<Record<string, unknown> | null>(null), selected = $state(''), skip = $state(0), busy = $state(false), error = $state(''), notice = $state('');
    async function load(offset = skip) { busy = true; error = ''; try { rows = await api(`/leads?skip=${offset}&limit=50&search=${encodeURIComponent(search)}`); skip = offset; } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    async function inspect(event: SubmitEvent) { event.preventDefault(); busy = true; error = ''; notice = ''; prediction = null; try { prediction = await api(`/leads/${encodeURIComponent(selected)}/prediction`); if (!prediction) notice = 'No prediction has been generated for this lead.'; } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    onMount(() => { void load(); });
</script>
<svelte:head><title>Lead Management | DecisionIntel</title></svelte:head>
<h1 class="text-3xl font-bold mb-3">Lead Management</h1><p class="text-text-secondary mb-6">Browse stored marketing leads and inspect their available predictions.</p>
<form class="flex gap-3 my-5" onsubmit={(event) => {event.preventDefault(); void load(0);}}><label>Search customer ID<input class="block bg-card border border-white/20 p-3 rounded-lg" bind:value={search} /></label><button class="bg-secondary rounded-lg p-3" disabled={busy}>Search</button></form>
<button class="bg-cta text-black p-3 rounded-lg mb-5" onclick={() => {editingId = ''; draft = {...defaults}; outcome = 'unknown'; editing = true;}}>Add lead</button>
{#if editing}<form class="bg-card border border-white/10 rounded-xl p-6 grid sm:grid-cols-2 gap-4 mb-6" onsubmit={save}>
    {#each Object.keys(defaults) as key}<label>{key.replaceAll('_',' ')}{#if typeof defaults[key as keyof typeof defaults] === 'number'}<input class="block w-full bg-primary border border-white/20 rounded-lg p-3" type="number" min="0" step="any" bind:value={draft[key]} required />{:else}<input class="block w-full bg-primary border border-white/20 rounded-lg p-3" bind:value={draft[key]} required />{/if}</label>{/each}
    <label>Conversion outcome<select class="block bg-primary p-3 rounded-lg" bind:value={outcome}><option value="unknown">Not yet known</option><option value="yes">Converted</option><option value="no">Not converted</option></select></label>
    <div class="flex gap-3"><button class="bg-cta text-black p-3 rounded-lg" disabled={busy}>Save lead</button><button type="button" class="p-3" onclick={() => editing = false}>Cancel</button></div>
</form>{/if}
{#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}
<div class="flex gap-4 items-center mb-6"><button class="bg-secondary px-4 py-2 rounded-lg" disabled={busy || skip === 0} onclick={() => load(Math.max(0,skip-50))}>Previous</button><span>Page {skip / 50 + 1}</span><button class="bg-secondary px-4 py-2 rounded-lg" disabled={busy || rows.length < 50} onclick={() => load(skip+50)}>Next</button><button class="bg-secondary px-4 py-2 rounded-lg" disabled={busy} onclick={() => load()}>Refresh</button></div>
{#if busy}<p role="status">Loading…</p>{/if}<DataTable {rows} empty="No leads found. Import marketing leads into the backend to see them here." />
{#if rows.length}<form class="mt-8 flex gap-3 flex-wrap items-end" onsubmit={inspect}><label>Lead<select class="block bg-card border border-white/20 rounded-lg p-3 mt-2" bind:value={selected} required><option value="" disabled>Select a lead</option>{#each rows as row}<option value={String(row.id)}>{row.customer_id || row.id}</option>{/each}</select></label><button class="bg-cta text-black rounded-lg p-3" disabled={busy}>View prediction</button><button type="button" class="bg-secondary rounded-lg p-3" disabled={busy || !selected} onclick={edit}>Edit selected lead</button></form>{/if}
{#if notice}<p role="status" class="mt-5">{notice}</p>{/if}{#if prediction}<section class="mt-6"><h2 class="text-xl mb-3">Prediction details</h2><DataTable rows={[prediction]} /></section>{/if}
