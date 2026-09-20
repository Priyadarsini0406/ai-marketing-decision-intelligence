<script lang="ts">
    import AnalyticsChart from '$lib/components/AnalyticsChart.svelte';
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    let summary = $state<Record<string, number> | null>(null);
    onMount(async () => { try { summary = (await api('/admin/reports')).summary; } catch { summary = { users: 0, datasets: 0, dataset_rows: 0, leads: 0 }; } });
    const labels = [['Total Students', 'users'], ['Total Managers', 'users'], ['Total Courses', 'datasets'], ['Total Leads', 'leads']];
</script>
<svelte:head><title>Admin Dashboard | DecisionIntel</title></svelte:head>
<div class="space-y-8"><div><h1 class="text-3xl font-bold text-white">System overview</h1><p class="text-text-secondary mt-2">Monitor users, education data and Decision-Intel system health.</p></div>
{#if summary}<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">{#each labels as [label, key]}<div class="bg-card border border-white/10 rounded-2xl p-5"><p class="text-xs uppercase tracking-wider text-text-secondary">{label}</p><p class="text-3xl font-bold text-white mt-2">{summary[key] ?? 0}</p></div>{/each}</div>{/if}
{#if summary}<AnalyticsChart title="Stored platform records" categories={['Users','Datasets','Dataset rows','Leads']} series={[{ name: 'Records', values: ['users','datasets','dataset_rows','leads'].map(key => summary![key] ?? 0) }]} unit="Records" />{/if}
<div class="grid lg:grid-cols-3 gap-5">{#each [['Recent User Activity', 'New user and access events will appear here.'], ['Recent Data Activity', 'Dataset imports and updates will appear here.'], ['System Status', 'Core services are ready for administration.']] as [title, text]}<section class="bg-card border border-white/10 rounded-2xl p-6"><h2 class="text-white font-bold">{title}</h2><p class="text-sm text-text-secondary mt-3">{text}</p></section>{/each}</div></div>
