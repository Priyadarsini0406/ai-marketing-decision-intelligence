<script lang="ts">
    import AnalyticsChart from './AnalyticsChart.svelte';
    let { rows, title = 'Performance comparison' }: { rows: Record<string, unknown>[]; title?: string } = $props();
    let selected = $state('');
    const excluded = new Set(['id', 'age', 'random_seed', 'created_at', 'generated_at', 'segment_cluster']);
    const metrics = $derived([...new Set(rows.flatMap(row => Object.keys(row)))].filter(key => !excluded.has(key) && rows.some(row => typeof row[key] === 'number' && Number.isFinite(row[key]))));
    const metric = $derived(metrics.includes(selected) ? selected : metrics[0] ?? '');
    const plotted = $derived(rows.slice(0, 20));
    const categories = $derived(plotted.map((row, index) => String(row.channel_name ?? row.channel ?? row.campaign_type ?? row.scenario_name ?? row.stage ?? row.student_name ?? row.customer_id ?? row.name ?? row.segment_name ?? `Record ${index + 1}`)));
</script>
{#if metrics.length}
    <div class="metric-control"><label>Chart metric<select value={metric} onchange={event => selected = event.currentTarget.value}>{#each metrics as value}<option {value}>{value.replaceAll('_', ' ')}</option>{/each}</select></label></div>
    <AnalyticsChart {title} {categories} unit={metric.replaceAll('_',' ')} description={rows.length > 20 ? `Showing the first 20 of ${rows.length} records; the table and export retain all available records.` : 'Values from the records shown on this page.'} series={[{ name: metric.replaceAll('_',' '), values: plotted.map(row => typeof row[metric] === 'number' ? row[metric] as number : null) }]} />
{:else}<AnalyticsChart {title} categories={[]} series={[]} />{/if}
<style>.metric-control{margin-top:20px}label{display:flex;align-items:center;gap:12px;font-size:12px;color:#6F6979;flex-wrap:wrap}select{appearance:none;padding:8px 32px 8px 12px;background:#FFFFFF;color:#262230;border:1px solid #DED6C9;border-radius:8px;max-width:100%;font:inherit;font-size:12px;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236A31C4' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 8px center;transition:border-color .15s ease,box-shadow .15s ease}select:hover{border-color:#E7D6FA}select:focus-visible{outline:none;border-color:#6A31C4;box-shadow:0 0 0 4px rgba(106,49,196,.30)}</style>
