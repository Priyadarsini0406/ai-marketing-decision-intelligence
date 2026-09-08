<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    type Report = {generated_at: number; configuration: {organization_name: string; currency: string}; summary: Record<string, number>; channels: Record<string, unknown>[]; simulations: Record<string, unknown>[]; predictions: Record<string, unknown>[]; leads: Record<string, unknown>[]; datasets: Record<string, unknown>[]};
    let report = $state<Report | null>(null), error = $state(''), busy = $state(false);
    async function load() { busy = true; error = ''; try { report = await api('/admin/reports'); } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    onMount(load);
    function download() { if (!report) return; const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'})); const a = document.createElement('a'); a.href = url; a.download = 'marketing-report.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
    function display(value: unknown) { return value === null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value); }
</script>
<svelte:head><title>Analytics & reports | DecisionIntel</title></svelte:head>
<h1>Analytics & reports</h1><p>All stored leads, predictions, channel metrics, budget simulations, and dataset summaries.</p>
<div class="actions"><button onclick={load} disabled={busy}>{busy ? 'Loading…' : 'Refresh'}</button><button class="secondary" onclick={download} disabled={!report || busy}>Download full report (JSON)</button></div>
{#if error}<p role="alert">{error}</p>{/if}
{#if report}<p>{report.configuration.organization_name} · Generated {new Date(report.generated_at * 1000).toLocaleString()}</p>
<div class="grid">{#each Object.entries(report.summary) as [label, value]}<div class="stat">{label.replaceAll('_', ' ')}<strong>{label === 'ad_spend' ? new Intl.NumberFormat(undefined, {style:'currency', currency:report.configuration.currency}).format(value) : value.toLocaleString()}</strong></div>{/each}</div>
{#each [['Channel analytics', report.channels], ['Budget simulations', report.simulations], ['Lead predictions and segments', report.predictions], ['Marketing leads', report.leads], ['Dataset inventory', report.datasets]] as section}
{@const rows = section[1] as Record<string, unknown>[]}
<section class="panel"><h2>{section[0]}</h2>{#if rows.length}<p>{rows.length} records. Showing up to 100; the download includes all records.</p><div class="table-wrap"><table><thead><tr>{#each Object.keys(rows[0]) as key}<th>{key.replaceAll('_', ' ')}</th>{/each}</tr></thead><tbody>{#each rows.slice(0,100) as row}<tr>{#each Object.values(row) as value}<td>{display(value)}</td>{/each}</tr>{/each}</tbody></table></div>{:else}<p>No stored records available.</p>{/if}</section>
{/each}{/if}
