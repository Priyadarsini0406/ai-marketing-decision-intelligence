<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import { workspacePages } from '$lib/workspace-pages';
    import DataTable from '$lib/DataTable.svelte';
    let summary = $state<Record<string,number> | null>(null), channels = $state<Record<string,unknown>[]>([]), currency = $state('USD');
    let error = $state(''), exporting = $state(false);
    onMount(async () => { try { const [report,preferences] = await Promise.all([api('/workspace/overview'),api('/workspace/settings')]); summary = report.summary; channels = report.channels; currency = preferences.currency; } catch(e) {error = (e as Error).message;} });
    async function exportReport() { exporting = true; try { const report = await api('/workspace/overview'); const url = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})); const a = document.createElement('a'); a.href = url; a.download = 'marketing-summary.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000); } catch(e) {error = (e as Error).message;} finally {exporting = false;} }
</script>
<svelte:head><title>Dashboard | DecisionIntel</title></svelte:head>
<h1 class="text-3xl font-bold mb-3">Campaign Overview</h1>
<p class="text-text-secondary mb-6">Stored campaign performance and your marketing tools. Monetary values use your preferred label without currency conversion.</p>
<button class="bg-cta text-black rounded-lg px-5 py-3 mb-6" onclick={exportReport} disabled={exporting}>Export Report</button>
{#if error}<p role="alert" class="text-red-400">{error}</p>{/if}
{#if summary}<div class="cards">{#each Object.entries(summary) as [name,value]}<section class="card"><p>{name.replaceAll('_',' ')}</p><strong>{name === 'ad_spend' ? new Intl.NumberFormat(undefined,{style:'currency',currency}).format(value) : value.toLocaleString()}</strong></section>{/each}</div>{:else if !error}<p role="status">Loading metrics?</p>{/if}
<section class="card my-6"><h2 class="text-xl font-bold mb-5">Channel performance</h2><DataTable rows={channels} /></section>
<h2 class="text-xl font-bold mt-8 mb-4">Marketing workspace</h2>
<div class="cards">{#each workspacePages as item}<a class="card" href={`/dashboard/${item.slug}`}><h3 class="text-accent font-semibold mb-2">{item.label} ?</h3><p>{item.description}</p></a>{/each}</div>
<style>
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:20px}.card{min-width:0;background:linear-gradient(135deg,#21182b,#17131f);padding:24px;border:1px solid #ffffff12;border-radius:18px;transition:transform .2s,border-color .2s}.card:hover{transform:translateY(-3px);border-color:#a47be060}.card p{color:#b6aec4;line-height:1.6}.card strong{display:block;font-size:clamp(18px,2vw,28px);margin-top:12px;overflow-wrap:anywhere}@media(prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
</style>
