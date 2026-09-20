<script lang="ts">
    import DataTable from '$lib/DataTable.svelte';
    import { fullReport, fullReportCsv, reportCatalog, reportCsv } from '$lib/manager-reports';
    let selected = $state('lead');
    let search = $state('');
    let notice = $state('');
    let exporting = $state(false);
    let exportError = $state('');
    const report = $derived(reportCatalog.find(item => item.type === selected)!);
    const rows = $derived(report.rows.filter(row => Object.values(row).some(value => String(value ?? '').toLowerCase().includes(search.trim().toLowerCase()))));
    const summary = [
        { label: 'Available reports', value: reportCatalog.length },
        { label: 'Student records', value: reportCatalog.find(item => item.type === 'lead')!.rows.length },
        { label: 'Acquisition channels', value: reportCatalog.find(item => item.type === 'channel')!.rows.length },
        { label: 'Campaigns', value: reportCatalog.find(item => item.type === 'campaign')!.rows.length }
    ];
    function download(content: string | ArrayBuffer, filename: string, mime: string) {
        const url = URL.createObjectURL(new Blob([content], { type: mime }));
        const link = document.createElement('a');
        link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        notice = `Download started: ${filename}`;
    }
    function csv(type: string) {
        const item = reportCatalog.find(report => report.type === type)!;
        download(reportCsv(item.rows), `${type}-report.csv`, 'text/csv;charset=utf-8');
    }
    function selectReport(type: string) { selected = type; search = ''; notice = ''; }
    async function downloadAll(format: 'pdf' | 'json' | 'csv') {
        exporting = true; exportError = ''; notice = '';
        try {
            const snapshot = fullReport();
            const filename = `admission-marketing-analytics.${format}`;
            if (format === 'pdf') {
                const { analyticsPdf } = await import('$lib/analytics-pdf');
                download(await analyticsPdf(snapshot), filename, 'application/pdf');
            } else if (format === 'csv') {
                download(fullReportCsv(snapshot), filename, 'text/csv;charset=utf-8');
            } else {
                download(JSON.stringify(snapshot, null, 2), filename, 'application/json');
            }
        } catch (error) {
            exportError = `Could not create the report. ${error instanceof Error ? error.message : 'Please try again.'}`;
        } finally { exporting = false; }
    }
</script>

<svelte:head><title>Reports &amp; Analytics | DecisionIntel</title></svelte:head>
<div class="space-y-6">
    <div class="flex flex-wrap justify-between items-end gap-4">
        <div><p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Admission intelligence</p><h1 class="mt-2 text-3xl font-bold text-white">Reports &amp; Analytics</h1><p class="mt-2 text-text-secondary">Review student leads, admission outcomes, marketing performance, and budget allocations.</p></div>
    </div>
    <section class="panel space-y-3" aria-label="Download entire analytics">
        <h2>Download entire analytics</h2>
        <p class="text-sm text-text-secondary">Includes all reports, budget totals, segments, recommendations, scenario comparisons, and AI explanations. Preview filters do not affect these downloads.</p>
        <div class="flex flex-wrap gap-3"><button class="action primary" disabled={exporting} onclick={() => downloadAll('pdf')}>Download entire analytics (PDF)</button><button class="action" disabled={exporting} onclick={() => downloadAll('json')}>Download entire analytics (JSON)</button><button class="action" disabled={exporting} onclick={() => downloadAll('csv')}>Download entire analytics (CSV)</button></div>
        <p class="text-xs text-text-secondary">PDF: formatted report. JSON: structured data. CSV: one combined file with section, record, field, and value columns.</p>
    </section>
    {#if exporting}<p role="status" class="text-sm text-accent">Preparing the complete report...</p>{/if}
    {#if exportError}<p role="alert" class="text-sm text-red-300">{exportError}</p>{/if}
    {#if notice}<p role="status" class="text-sm text-accent">{notice}</p>{/if}
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{#each summary as item}<div class="panel"><p class="caption">{item.label}</p><p class="mt-3 text-3xl text-white font-bold">{item.value}</p></div>{/each}</div>
    <section aria-label="Available reports" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {#each reportCatalog as item}
            <article class="panel flex flex-col gap-3">
                <div class="flex justify-between items-start gap-3"><h2>{item.label}</h2><span class="text-xs text-accent whitespace-nowrap">{item.rows.length} rows</span></div>
                <p class="text-sm text-text-secondary flex-1">{item.description}</p>
                <div class="flex flex-wrap gap-2"><button class="action" aria-label={`Preview ${item.label}`} aria-pressed={selected === item.type} onclick={() => selectReport(item.type)}>Preview</button><button class="action" aria-label={`Download ${item.label} CSV`} onclick={() => csv(item.type)}>Download CSV</button></div>
            </article>
        {/each}
    </section>
    <section class="panel space-y-5" aria-label="Report preview">
        <div class="flex flex-wrap justify-between gap-4 items-end"><div><h2>{report.label} preview</h2><p class="mt-2 text-sm text-text-secondary">Showing {rows.length} of {report.rows.length} records. Monetary columns use INR; percentage columns use 0–100.</p></div><button class="action" disabled={!rows.length} onclick={() => download(reportCsv(rows), `${report.type}-report-filtered.csv`, 'text/csv;charset=utf-8')}>Download displayed rows (CSV)</button></div>
        <div class="grid gap-4 sm:grid-cols-2"><div class="field"><label for="report-type">Report type</label><select id="report-type" value={selected} onchange={(event) => selectReport(event.currentTarget.value)}>{#each reportCatalog as item}<option value={item.type}>{item.label}</option>{/each}</select></div><label class="field">Search report<input type="search" bind:value={search} placeholder="Search any column" /></label></div>
        <DataTable {rows} empty="No records match your search. Clear the search to see all report rows." />
    </section>
</div>

<style>
    .panel{min-width:0;padding:1.25rem;border:1px solid #ffffff1a;border-radius:1rem;background:var(--color-card,#21182b)}
    h2{font-size:1.1rem;font-weight:700;color:white}.caption{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-secondary,#b6aec4)}
    .action{padding:.65rem .9rem;border:1px solid #ffffff26;border-radius:.65rem;color:white;cursor:pointer;font-size:.875rem}.action:hover,.action[aria-pressed=true]{background:#a47be01a;border-color:#a47be080}.primary{background:var(--color-accent,#a47be0);color:#171020;font-weight:600}.action:disabled{opacity:.5;cursor:default}
    .field{display:grid;gap:.5rem;font-size:.875rem;color:var(--color-text-secondary,#b6aec4)}input,select{min-width:0;width:100%;padding:.7rem .85rem;border:1px solid #ffffff26;border-radius:.5rem;background:#171020;color:white}
    button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #a47be0;outline-offset:3px}
</style>
