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
<div class="report-page">
<h1>Analytics & reports</h1><p>All stored leads, predictions, channel metrics, budget simulations, and dataset summaries.</p>
<div class="actions"><button onclick={load} disabled={busy}>{busy ? 'Loading…' : 'Refresh'}</button><button class="secondary" onclick={download} disabled={!report || busy}>Download full report (JSON)</button></div>
{#if error}<p role="alert">{error}</p>{/if}
{#if report}<p>{report.configuration.organization_name} · Generated {new Date(report.generated_at * 1000).toLocaleString()}</p>
<div class="grid">{#each Object.entries(report.summary) as [label, value], index}<div class="stat" style:--delay={`${index * 55}ms`}>{label.replaceAll('_', ' ')}<strong>{label === 'ad_spend' ? new Intl.NumberFormat(undefined, {style:'currency', currency:report.configuration.currency}).format(value) : value.toLocaleString()}</strong></div>{/each}</div>
{#each [['Channel analytics', report.channels], ['Budget simulations', report.simulations], ['Lead predictions and segments', report.predictions], ['Marketing leads', report.leads], ['Dataset inventory', report.datasets]] as section, index}
{@const rows = section[1] as Record<string, unknown>[]}
<section class="panel" style:--delay={`${180 + index * 70}ms`}><h2>{section[0]}</h2>{#if rows.length}<p>{rows.length} records. Showing up to 100; the download includes all records.</p><div class="table-wrap"><table><thead><tr>{#each Object.keys(rows[0]) as key}<th>{key.replaceAll('_', ' ')}</th>{/each}</tr></thead><tbody>{#each rows.slice(0,100) as row}<tr>{#each Object.values(row) as value}<td>{display(value)}</td>{/each}</tr>{/each}</tbody></table></div>{:else}<p>No stored records available.</p>{/if}</section>
{/each}{/if}

</div>

<style>
    .report-page { min-width: 0; animation: page-enter 450ms ease-out; }
    .report-page .grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 20px; }
    .report-page .stat {
        min-width: 0;
        container-type: inline-size;
        position: relative;
        background: linear-gradient(145deg, #21192b, #17131f);
        border-radius: 20px;
        padding: 24px;
        color: #d3c6e2;
        text-transform: capitalize;
        transition: transform 250ms ease, border-color 250ms ease, box-shadow 250ms ease;
        animation: card-enter 550ms ease-out backwards;
        animation-delay: var(--delay, 0ms);
    }
    .report-page .stat::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: inherit;
        pointer-events: none;
        background: radial-gradient(ellipse at top right, #a47be024, transparent 70%);
        opacity: 0;
        transition: opacity 250ms ease;
    }
    .report-page .stat strong {
        position: relative;
        font-size: clamp(18px, 9cqi, 32px);
        line-height: 1.3;
        letter-spacing: -0.035em;
        font-variant-numeric: tabular-nums;
        color: #f5efff;
        overflow-wrap: anywhere;
        text-transform: none;
    }
    .report-page .panel {
        min-width: 0;
        border-radius: 20px;
        background: linear-gradient(135deg, #1c1624, #17131f);
        transition: border-color 250ms ease, box-shadow 250ms ease;
        animation: card-enter 550ms ease-out backwards;
        animation-delay: var(--delay, 0ms);
    }
    .report-page .panel h2 { display: flex; align-items: center; gap: 12px; }
    .report-page .panel h2::before { content: ''; width: 4px; height: 20px; border-radius: 4px; background: linear-gradient(#c7a4f0, #f2a62b); flex-shrink: 0; }
    .report-page .table-wrap { max-width: 100%; border-radius: 12px; scrollbar-color: #584667 #17131f; }
    .report-page th { background: #241b30; }
    .report-page tbody tr { transition: background-color 180ms ease; }
    .report-page button { transition: transform 180ms ease, box-shadow 180ms ease; }
    .report-page button:focus-visible { outline: 2px solid #c7a4f0; outline-offset: 4px; }
    @media (hover: hover) {
        .report-page .stat:hover { transform: translateY(-6px); border-color: #a47be080; box-shadow: 0 14px 32px #00000030, 0 0 25px #a47be01c; }
        .report-page .stat:hover::before { opacity: 1; }
        .report-page .panel:hover { border-color: #a47be050; box-shadow: 0 0 25px #a47be010; }
        .report-page tbody tr:hover { background: #a47be012; }
        .report-page button:not(:disabled):hover { transform: translateY(-2px); box-shadow: 0 5px 18px #a47be025; }
    }
    @keyframes page-enter { from { opacity: 0; } to { opacity: 1; } }
    @keyframes card-enter { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
    @media (prefers-reduced-motion: reduce) {
        .report-page, .report-page .stat, .report-page .panel { animation: none; }
        .report-page .stat, .report-page .stat::before, .report-page .panel, .report-page tbody tr, .report-page button { transition: none; }
        .report-page .stat:hover, .report-page button:not(:disabled):hover { transform: none; }
    }
</style>
