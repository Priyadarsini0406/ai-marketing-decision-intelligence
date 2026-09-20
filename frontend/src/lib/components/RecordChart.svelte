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
<style>.metric-control{margin-top:20px}label{display:flex;align-items:center;gap:12px;font-size:12px;color:#C9C5CE;flex-wrap:wrap}select{padding:8px 12px;background:#171320;color:white;border:1px solid #A47BE040;border-radius:8px;max-width:100%}</style>
