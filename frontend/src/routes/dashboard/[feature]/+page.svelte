<script lang="ts">
    import { api } from '$lib/api';
    import DataTable from '$lib/DataTable.svelte';
    let { data } = $props();
    type Row = Record<string, unknown>;
    type Overview = { summary: Record<string, number>; channels: Row[]; funnel: Row[]; campaigns: Row[]; recommendations: Row[]; cohorts: Row[]; prediction_preview: Row[]; saved_scenarios: Row[] };
    let overview = $state<Overview | null>(null), rows = $state<Row[]>([]), leads = $state<Row[]>([]);
    let selected = $state(''), error = $state(''), notice = $state(''), busy = $state(false);
    let result = $state<Row | null>(null), budget = $state(100000), mode = $state('optimized'), cap = $state(100);
    let allocations = $state<Record<string, number>>({}), search = $state(''), offset = $state(0);
    let currency = $state('USD'), compact = $state(false);
    let generation = 0;
    const slug = $derived(data.feature.slug);
    const visibleLeads = $derived(leads.filter(l => String(l.customer_id).toLowerCase().includes(search.toLowerCase())));
    $effect(() => { void load(data.feature.slug); });
    async function load(feature: string) {
        const current = ++generation;
        busy = true; error = ''; notice = ''; result = null; rows = []; selected = ''; offset = 0;
        try {
            if (feature === 'prediction' || feature === 'explainability') {
                const [response, details] = await Promise.all([api('/leads?skip=0&limit=100'), api('/workspace/overview')]);
                if (current === generation) { leads = response; overview = details; }
            } else if (feature === 'segmentation') {
                const [response, details] = await Promise.all([api('/workspace/segments'), api('/workspace/overview')]);
                if (current === generation) { rows = response; overview = details; }
            } else if (feature === 'settings') {
                const response = await api('/workspace/settings');
                if (current === generation) { currency = response.currency; compact = response.compact; }
            } else {
                const response: Overview = await api('/workspace/overview');
                if (current !== generation) return;
                overview = response;
                const total = response.channels.reduce((sum, c) => sum + Number(c.conversions), 0);
                rows = feature === 'campaigns' ? response.campaigns : feature === 'recommendations' ? response.recommendations : feature === 'funnel' ? response.funnel : response.channels.map(c => ({...c, conversion_credit_percent: total ? Number((Number(c.conversions) / total * 100).toFixed(2)) : 0}));
                allocations = Object.fromEntries(response.channels.filter(c => Number(c.spend) > 0).map(c => [String(c.channel), 0]));
            }
        } catch (e) { if (current === generation) error = (e as Error).message; }
        finally { if (current === generation) busy = false; }
    }
    async function action(work: () => Promise<void>) { busy = true; error = ''; notice = ''; try { await work(); } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    async function predict(event: SubmitEvent) { event.preventDefault(); result = null; await action(async () => { result = await api(`/workspace/prediction/${encodeURIComponent(selected)}?explain=${slug === 'explainability'}`); }); }
    async function nextLeads(next: number) { await action(async () => { leads = await api(`/leads?skip=${next}&limit=100`); offset = next; selected = ''; search = ''; result = null; }); }
    async function simulate(event: SubmitEvent) { event.preventDefault(); result = null; await action(async () => { result = await api('/workspace/simulate', {method:'POST', body:JSON.stringify({budget, mode:slug === 'simulator' ? 'custom' : mode, max_channel_share:cap / 100, allocations})}); }); }
    async function save(event: SubmitEvent) { event.preventDefault(); await action(async () => { await api('/workspace/settings', {method:'PUT', body:JSON.stringify({currency,compact})}); notice = 'Preferences saved.'; }); }
    function exportReport() { if (!overview) return; const blob = new Blob([JSON.stringify(overview,null,2)], {type:'application/json'}); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'marketing-workspace-report.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url),1000); }
</script>

<svelte:head><title>{data.feature.label} | DecisionIntel</title></svelte:head>
<div class="workspace-page">
    <h1>{data.feature.label}</h1><p class="intro">{data.feature.description}</p>
    {#if error}<p role="alert">{error}</p>{/if}
    {#if notice}<p role="status">{notice}</p>{/if}
    {#if busy}<p role="status">Loading...</p>{/if}
    {#if slug === 'prediction' || slug === 'explainability'}
        <section class="workspace-panel">
            <div class="controls"><button disabled={busy || offset === 0} onclick={() => nextLeads(Math.max(0, offset-100))}>Previous leads</button><span>Page {offset / 100 + 1}</span><button disabled={busy || leads.length < 100} onclick={() => nextLeads(offset+100)}>Next leads</button></div>
            <label>Filter this page by customer ID<input bind:value={search} placeholder="Customer ID" /></label>
            <form onsubmit={predict}><label>Lead<select bind:value={selected} required><option value="" disabled>Select a lead</option>{#each visibleLeads as lead}<option value={String(lead.id)}>{lead.customer_id}</option>{/each}</select></label><button disabled={busy || !selected}>{slug === 'explainability' ? 'Explain prediction' : 'Predict conversion'}</button></form>
            {#if !busy && !leads.length}<p>No leads available. Import the campaign dataset first.</p>{/if}
        </section>
        {#if result}<section class="workspace-panel"><h2>Conversion probability: {(Number(result.probability) * 100).toFixed(1)}%</h2><p>{result.score} propensity ? {result.note}</p>
            {#if result.factors}<p>Positive SHAP values increase the model's log-odds of conversion; negative values decrease them. These explain model behavior, not causation. Base log-odds: {Number(result.base_log_odds).toFixed(4)}.</p><DataTable rows={result.factors as Row[]} />{/if}
        </section>{/if}
    {:else if slug === 'optimization' || slug === 'simulator'}
        <section class="workspace-panel"><form onsubmit={simulate}>
            <label>Total budget (source currency)<input type="number" min="0.01" max="100000000" step="0.01" bind:value={budget} required /></label>
            {#if slug === 'optimization'}<label>Allocation strategy<select bind:value={mode}><option value="optimized">Maximize estimated conversions</option><option value="efficiency">Historical efficiency weighted</option><option value="equal">Equal allocation</option></select></label>{#if mode === 'optimized'}<label>Maximum budget per channel (%)<input type="number" min="1" max="100" bind:value={cap} required /></label>{/if}
            {:else}{#each Object.keys(allocations) as channel}<label>{channel} allocation<input type="number" min="0" max="100000000" step="0.01" bind:value={allocations[channel]} required /></label>{/each}<p>Allocated: {Object.values(allocations).reduce((a,b) => a + Number(b || 0),0).toLocaleString()} / {budget?.toLocaleString()}</p>{/if}
            <button disabled={busy || !Object.keys(allocations).length}>{slug === 'optimization' ? 'Calculate allocation' : 'Run simulation'}</button>
        </form></section>
        {#if result}<section class="workspace-panel"><h2>Scenario result</h2><DataTable rows={Object.entries(result.allocations as Record<string,number>).map(([channel,amount])=>({channel,amount}))} /><p>Estimated conversions: {result.predicted_conversions} ? Estimated cost per conversion: {result.predicted_cpa ?? 'Unavailable'}</p><p>{result.assumption}</p></section>{/if}
    {:else if slug === 'settings'}
        <section class="workspace-panel"><form onsubmit={save}><label>Preferred display currency<select bind:value={currency} disabled={busy}>{#each ['USD','INR','EUR','GBP'] as item}<option value={item}>{item}</option>{/each}</select></label><label class="checkbox"><input type="checkbox" bind:checked={compact} disabled={busy} /> Compact workspace spacing</label><p>Currency controls labels only; it does not convert source values. Reload the dashboard after saving to apply preferences.</p><button disabled={busy}>Save preferences</button></form></section>
    {:else}
        <div class="controls"><button disabled={busy} onclick={() => load(slug)}>Refresh</button>{#if slug === 'reports'}<button disabled={busy || !overview} onclick={exportReport}>Export report (JSON)</button>{/if}</div>
        {#if slug === 'reports' && overview}<div class="summary-grid">{#each Object.entries(overview.summary) as [key,value]}<div class="workspace-panel"><p>{key.replaceAll('_',' ')}</p><strong>{value.toLocaleString()}</strong></div>{/each}</div><section class="workspace-panel"><h2>Campaign performance</h2><DataTable rows={overview.campaigns} /></section>{/if}
        {#if slug === 'funnel' && overview}<section class="workspace-panel">{#each overview.funnel as stage}<div class="funnel-stage"><span>{stage.stage}: {stage.count}</span><meter min="0" max={Math.max(1, overview.summary.leads)} value={Number(stage.count)}>{stage.count}</meter></div>{/each}<p>Conversions without a recorded website visit are outside this nested cohort; stage order cannot be inferred from this dataset.</p></section>{/if}
        <section class="workspace-panel"><DataTable {rows} /></section>
    {/if}
    {#if overview && !busy && !error && slug !== 'settings'}
        {#if slug === 'prediction' || slug === 'explainability'}
            <section class="workspace-panel"><h2>Stored prediction examples</h2><p>Up to 50 stored predictions. These are separate from the current-model scores and SHAP explanations generated above.</p><DataTable rows={overview.prediction_preview} /></section>
        {:else if slug === 'optimization' || slug === 'simulator'}
            <section class="workspace-panel"><h2>Saved budget scenarios</h2><p>Compare up to 50 saved illustrative scenarios with your calculations above.</p><DataTable rows={overview.saved_scenarios} /></section>
        {:else}
            <section class="workspace-panel"><h2>Channel, campaign and age breakdown</h2><p>{overview.cohorts.length} observed cohorts from the imported leads. Each lead appears in one cohort; these rows partition the same dataset rather than represent additional leads. Conversion rates use known outcomes.</p><DataTable rows={overview.cohorts} /></section>
            {#if slug === 'reports'}<section class="workspace-panel"><h2>Stored prediction examples</h2><DataTable rows={overview.prediction_preview} /></section><section class="workspace-panel"><h2>Saved budget scenarios</h2><DataTable rows={overview.saved_scenarios} /></section>{/if}
        {/if}
    {/if}
</div>

<style>
    .workspace-page { max-width:1200px; animation:enter .35s ease-out; }
    h1 {font-size:30px;font-weight:700;margin-bottom:12px} h2 {font-size:20px;font-weight:600;margin-bottom:16px}
    p {color:#b6aec4;margin:12px 0;line-height:1.7}.intro {margin-bottom:28px;max-width:850px}
    .workspace-panel {min-width:0;background:linear-gradient(135deg,#21182b,#17131f);border:1px solid #ffffff15;border-radius:18px;padding:24px;margin:20px 0;transition:border-color .2s,box-shadow .2s}
    .workspace-panel:hover {border-color:#a47be055;box-shadow:0 0 25px #a47be012}
    .summary-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:18px}.summary-grid strong{font-size:25px;overflow-wrap:anywhere}
    form {display:grid;gap:18px;max-width:640px} label {display:grid;gap:8px;margin:12px 0;color:#d9c9e9}
    input,select {background:#110d19;border:1px solid #584667;border-radius:8px;padding:12px;color:white;min-width:0}
    button {background:#f2a62b;color:#171020;border-radius:9px;padding:10px 18px;font-weight:600;cursor:pointer}button:disabled{opacity:.5;cursor:default}
    button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}
    .controls {display:flex;gap:12px;align-items:center;flex-wrap:wrap}.checkbox {display:flex;align-items:center}.checkbox input{width:auto}
    [role=alert]{color:#ffadb9}[role=status]{color:#bceacb}.funnel-stage{display:grid;gap:8px;margin:20px 0}meter{width:100%;height:24px;accent-color:#a47be0}
    @keyframes enter{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
    @media(prefers-reduced-motion:reduce){.workspace-page{animation:none}.workspace-panel{transition:none}}
</style>
