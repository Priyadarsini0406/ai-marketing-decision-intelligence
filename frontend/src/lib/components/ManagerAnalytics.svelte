<script lang="ts">
    import { managerFunnelStages, managerChannels, managerCampaigns } from '$lib/manager-demo';
    import DataTable from '$lib/DataTable.svelte';

    let { view }: { view: 'funnel' | 'attribution' | 'campaigns' } = $props();
    const titles = { funnel: 'Admission Funnel', attribution: 'Channel Attribution', campaigns: 'Campaign Analytics' };
    const descriptions = {
        funnel: 'Follow enquiries through contact, counselling, application, and admission.',
        attribution: 'Compare acquisition channels by lead volume, admission share, and cost.',
        campaigns: 'Track campaign budgets, applications, and admission outcomes.'
    };
    let selectedChannel = $state('All channels');
    let search = $state('');
    const number = (value: number) => value.toLocaleString('en-IN');
    const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
    const percent = (value: number, total: number) => total ? `${(value / total * 100).toFixed(1)}%` : '—';
    const cost = (spend: number, count: number) => count ? money(spend / count) : '—';
    const channels = $derived(managerChannels.filter(item => selectedChannel === 'All channels' || item.channel === selectedChannel));
    const campaigns = $derived(managerCampaigns.filter(item =>
        (selectedChannel === 'All channels' || item.channel === selectedChannel) && item.name.toLowerCase().includes(search.toLowerCase())));
    const allAdmissions = managerChannels.reduce((sum, item) => sum + item.admissions, 0);
    const stages = managerFunnelStages.map((stage, index) => {
        const previous = index ? managerFunnelStages[index - 1].count : stage.count;
        return { ...stage, retained: percent(stage.count, previous), dropOffCount: previous - stage.count, dropOffRate: percent(previous - stage.count, previous) };
    });
    const totals = $derived.by(() => {
        const items = view === 'campaigns' ? campaigns : channels;
        return items.reduce((sum, item) => ({ leads: sum.leads + item.leads, applications: sum.applications + item.applications, admissions: sum.admissions + item.admissions, spend: sum.spend + item.spend }), { leads: 0, applications: 0, admissions: 0, spend: 0 });
    });
    const budget = $derived(campaigns.reduce((sum, item) => sum + item.budget, 0));
    const cards = $derived(view === 'funnel' ? [
        { label: 'Enquiries', value: number(stages[0].count) },
        { label: 'Applications', value: number(stages[3].count) },
        { label: 'Admissions', value: number(stages[4].count) },
        { label: 'Enquiry to admission', value: percent(stages[4].count, stages[0].count) }
    ] : [
        { label: 'Leads', value: number(totals.leads) },
        { label: 'Applications', value: number(totals.applications) },
        { label: 'Admissions', value: number(totals.admissions) },
        { label: 'Admission rate', value: percent(totals.admissions, totals.leads) },
        { label: 'Total spend', value: money(totals.spend) },
        { label: 'Cost per admission', value: cost(totals.spend, totals.admissions) }
    ]);
    const rows = $derived(view === 'funnel' ? stages.map((stage, index) => ({
        Stage: stage.name, Students: number(stage.count), 'Share of enquiries': percent(stage.count, stages[0].count),
        'Retention from previous stage': index ? stage.retained : '—',
        'Drop-off count': index ? number(stage.dropOffCount) : '—', 'Drop-off rate': index ? stage.dropOffRate : '—'
    })) : view === 'attribution' ? channels.map(item => ({
        Channel: item.channel, Leads: number(item.leads), Applications: number(item.applications), Admissions: number(item.admissions),
        'Admission rate': percent(item.admissions, item.leads), 'Share of all admissions': percent(item.admissions, allAdmissions),
        Spend: money(item.spend), 'Cost per lead': cost(item.spend, item.leads), 'Cost per admission': cost(item.spend, item.admissions)
    })) : campaigns.map(item => ({
        Campaign: item.name, Channel: item.channel, Budget: money(item.budget), Spend: money(item.spend),
        'Budget remaining': money(item.budget - item.spend), 'Budget used': percent(item.spend, item.budget),
        Leads: number(item.leads), Applications: number(item.applications), Admissions: number(item.admissions),
        'Admission rate': percent(item.admissions, item.leads), 'Cost per admission': cost(item.spend, item.admissions)
    })));
    const availableChannels = $derived([...new Set((view === 'campaigns' ? managerCampaigns : managerChannels).map(item => item.channel))]);
    function exportCsv() {
        if (!rows.length) return;
        const escape = (value: unknown) => '"' + String(value).replaceAll('"', '""') + '"';
        const csv = [Object.keys(rows[0]), ...rows.map(row => Object.values(row))].map(row => row.map(escape).join(',')).join('\r\n');
        const url = URL.createObjectURL(new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' }));
        const link = document.createElement('a');
        link.href = url; link.download = `${view}-demo-data.csv`; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
</script>

<svelte:head><title>{titles[view]} | DecisionIntel</title></svelte:head>
<div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
        <div><p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Admission analytics</p><h1 class="mt-2 text-3xl font-bold text-white">{titles[view]}</h1><p class="mt-2 text-text-secondary">{descriptions[view]}</p></div>
        <button class="action" onclick={exportCsv} disabled={!rows.length}>Export CSV</button>
    </div>
    {#if view !== 'funnel'}
        <div class="flex flex-wrap gap-4 items-end">
            <div class="grid gap-2 text-sm text-text-secondary"><label for="analytics-channel">Channel</label><select id="analytics-channel" bind:value={selectedChannel}><option>All channels</option>{#each availableChannels as channel}<option>{channel}</option>{/each}</select></div>
            {#if view === 'campaigns'}<label class="grid gap-2 text-sm text-text-secondary">Search campaigns<input bind:value={search} placeholder="Campaign name" /></label>{/if}
        </div>
    {/if}
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {#each cards as card}<div class="panel"><p class="text-xs uppercase tracking-wider text-text-secondary">{card.label}</p><p class="mt-3 text-2xl font-bold text-white">{card.value}</p></div>{/each}
    </div>
    {#if view === 'funnel'}
        <section class="panel"><h2>Stage progression</h2><p class="note">Counts show the supplied cumulative funnel. Retention and drop-off compare each stage with the preceding stage.</p>
            <div class="mt-6 space-y-5">{#each stages as stage, index}<div><div class="mb-2 flex justify-between gap-3 text-sm"><span>{stage.name}</span><span>{number(stage.count)} · {percent(stage.count, stages[0].count)} of enquiries</span></div><div class="track"><div class="bar" style:width={percent(stage.count, stages[0].count)}></div></div>{#if index}<p class="mt-1 text-xs text-text-secondary">{stage.retained} retained · {number(stage.dropOffCount)} drop-off ({stage.dropOffRate})</p>{/if}</div>{/each}</div>
        </section>
    {:else if view === 'attribution'}
        <section class="panel"><h2>Admission share by channel</h2><p class="note">Each channel's admissions divided by all {number(allAdmissions)} admissions in the channel dataset. This is source-level credit, not multi-touch attribution.</p>
            <div class="mt-6 space-y-4">{#each channels as item}<div><div class="mb-2 flex justify-between gap-3 text-sm"><span>{item.channel}</span><span>{item.admissions} admissions · {percent(item.admissions, allAdmissions)}</span></div><div class="track"><div class="bar" style:width={percent(item.admissions, allAdmissions)}></div></div></div>{/each}</div>
        </section>
    {:else}
        <section class="panel"><h2>Campaign budget utilization</h2><p class="note">{money(totals.spend)} spent of {money(budget)} allocated · {money(budget - totals.spend)} remaining in the selected campaigns.</p>
            <div class="mt-6 space-y-4">{#each campaigns as item}<div><div class="mb-2 flex flex-wrap justify-between gap-2 text-sm"><span>{item.name}</span><span>{money(item.spend)} / {money(item.budget)} · {percent(item.spend, item.budget)}</span></div><div class="track"><div class="bar" style:width={percent(item.spend, item.budget)}></div></div></div>{/each}</div>
        </section>
    {/if}
    <section class="panel"><h2>{view === 'funnel' ? 'Stage breakdown' : view === 'attribution' ? 'Channel performance' : 'Campaign performance'}</h2><div class="mt-4"><DataTable {rows} empty="No campaigns match these filters. Try another channel or campaign name." /></div></section>
</div>

<style>
    .panel { min-width:0; border:1px solid #ffffff1a; border-radius:1rem; background:var(--color-card,#21182b); padding:1.25rem; }
    h2 { color:white; font-size:1.25rem; font-weight:700; }
    .note { color:var(--color-text-secondary,#b6aec4); font-size:.875rem; line-height:1.6; margin-top:.5rem; }
    .track { height:.7rem; border-radius:999px; background:#ffffff0d; overflow:hidden; }
    .bar { height:100%; border-radius:999px; background:var(--color-accent,#a47be0); }
    select,input { color:white; background:#171020; border:1px solid #ffffff26; border-radius:.5rem; padding:.65rem .85rem; max-width:100%; }
    .action { padding:.65rem 1rem; border:1px solid #ffffff26; border-radius:.65rem; color:white; cursor:pointer; }
    .action:hover { background:#ffffff0d; }.action:disabled { opacity:.5; cursor:default; }
    button:focus-visible,input:focus-visible,select:focus-visible { outline:2px solid #a47be0; outline-offset:3px; }
</style>
