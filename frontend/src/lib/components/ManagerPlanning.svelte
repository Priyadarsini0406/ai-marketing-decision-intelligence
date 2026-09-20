<script lang="ts">
    import { managerBudget, managerChannels, managerRecommendations, whatIfScenario } from '$lib/manager-demo';
    import DataTable from '$lib/DataTable.svelte';
    let { view }: { view: 'budget' | 'simulator' | 'recommendations' } = $props();
    const titles = { budget: 'Budget Optimization', simulator: 'What-If Simulator', recommendations: 'AI Recommendations' };
    const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
    const number = (value: number) => value.toLocaleString('en-IN', { maximumFractionDigits: 1 });
    const channels = managerBudget.allocations.map(allocation => ({ ...allocation, ...managerChannels.find(item => item.channel === allocation.channel)! }));
    let budget = $state<number>(managerBudget.totalBudget);
    let strategy = $state('efficiency');
    let allocation = $state<Record<string, number>>(Object.fromEntries(channels.map(item => [item.channel, item.currentAmount])));
    let error = $state('');
    let result = $state<{ allocation: Record<string, number>; budget: number; leads: number; applications: number; admissions: number } | null>(null);
    let filter = $state('All recommendations');
    const recommendations = $derived(managerRecommendations.filter(item => filter === 'All recommendations' || item.type === filter));
    const allocated = $derived(Object.values(allocation).reduce((sum, value) => sum + (Number(value) || 0), 0));
    const currentRows = channels.map(item => ({ Channel: item.channel, 'Current allocation': money(item.currentAmount), 'Budget share': `${item.percent}%`, 'Historical cost per admission': money(item.spend / item.admissions) }));
    function project(amounts: Record<string, number>, total: number) {
        const estimates = channels.reduce((sum, channel) => {
            const scale = amounts[channel.channel] / channel.spend;
            return { leads: sum.leads + scale * channel.leads, applications: sum.applications + scale * channel.applications, admissions: sum.admissions + scale * channel.admissions };
        }, { leads: 0, applications: 0, admissions: 0 });
        return { allocation: { ...amounts }, budget: total, ...estimates };
    }
    const baseline = project(Object.fromEntries(channels.map(item => [item.channel, item.currentAmount])), managerBudget.totalBudget);
    function distribute(total: number, mode: string): Record<string, number> {
        const weights = channels.map(item => mode === 'equal' ? 1 : mode === 'current' ? item.currentAmount : item.admissions / item.spend);
        const weightTotal = weights.reduce((sum, value) => sum + value, 0);
        const amounts = weights.map(weight => Math.floor(total * weight / weightTotal));
        let remainder = total - amounts.reduce((sum, value) => sum + value, 0);
        for (let index = 0; remainder > 0; index++, remainder--) amounts[index % amounts.length]++;
        return Object.fromEntries(channels.map((item, index) => [item.channel, amounts[index]]));
    }
    function validateBudget() {
        error = '';
        if (!Number.isFinite(budget) || !Number.isInteger(budget) || budget < 1 || budget > 100000000) {
            error = 'Enter a whole-rupee budget between ₹1 and ₹10,00,00,000.'; return false;
        }
        return true;
    }
    function calculate(event: SubmitEvent) {
        event.preventDefault(); result = null;
        if (!validateBudget()) return;
        if (view === 'budget') allocation = distribute(budget, strategy);
        if (channels.some(item => !Number.isFinite(allocation[item.channel]) || allocation[item.channel] < 0 || !Number.isInteger(allocation[item.channel]))) {
            error = 'Enter a non-negative whole-rupee allocation for every channel.'; return;
        }
        if (allocated !== budget) { error = 'Channel allocations must add up to the scenario budget.'; return; }
        result = project(allocation, budget);
    }
    function rebalance() {
        result = null;
        if (validateBudget()) allocation = distribute(budget, 'current');
    }
    function reset() {
        budget = managerBudget.totalBudget; strategy = 'efficiency'; error = ''; result = null;
        allocation = Object.fromEntries(channels.map(item => [item.channel, item.currentAmount]));
    }
    const resultRows = $derived(result ? channels.map(item => ({ Channel: item.channel, 'Current allocation': money(item.currentAmount), 'Scenario allocation': money(result!.allocation[item.channel]), Change: money(result!.allocation[item.channel] - item.currentAmount), 'Budget share': `${(result!.allocation[item.channel] / result!.budget * 100).toFixed(1)}%` })) : []);
    const comparisonRows = [
        { Metric: 'Leads', Current: number(whatIfScenario.current.leads), Simulated: number(whatIfScenario.simulated.leads) },
        { Metric: 'Applications', Current: number(whatIfScenario.current.applications), Simulated: number(whatIfScenario.simulated.applications) },
        { Metric: 'Admissions', Current: number(whatIfScenario.current.admissions), Simulated: number(whatIfScenario.simulated.admissions) },
        { Metric: 'Conversion rate', Current: `${whatIfScenario.current.conversionRate}%`, Simulated: `${whatIfScenario.simulated.conversionRate}%` },
        { Metric: 'Cost per admission', Current: money(whatIfScenario.current.costPerAdmission), Simulated: money(whatIfScenario.simulated.costPerAdmission) }
    ];
</script>

<svelte:head><title>{titles[view]} | DecisionIntel</title></svelte:head>
<div class="space-y-6">
    <div><p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">{view === 'recommendations' ? 'AI insights' : 'Budget intelligence'}</p><h1 class="mt-2 text-3xl font-bold text-white">{titles[view]}</h1><p class="mt-2 text-text-secondary">{view === 'budget' ? 'Compare channel allocations using the supplied budget and admission performance.' : view === 'simulator' ? 'Explore how changes in channel investment affect estimated admission outcomes.' : 'Review admission and marketing actions from the supplied recommendation set.'}</p></div>
    {#if view === 'recommendations'}
        <div class="grid gap-4 sm:grid-cols-3">
            <div class="panel"><p class="caption">Recommendations</p><strong>{managerRecommendations.length}</strong></div>
            <div class="panel"><p class="caption">Insights</p><strong>{managerRecommendations.filter(item => item.type === 'Insight').length}</strong></div>
            <div class="panel"><p class="caption">Suggested actions</p><strong>{managerRecommendations.filter(item => item.type === 'Action').length}</strong></div>
        </div>
        <div class="grid gap-2 max-w-xs"><label for="recommendation-type">Recommendation type</label><select id="recommendation-type" bind:value={filter}><option>All recommendations</option><option value="Insight">Insights</option><option value="Action">Actions</option></select></div>
        {#each recommendations as item}
            <article class="panel space-y-4">
                <div class="flex flex-wrap justify-between gap-3"><span class="badge">{item.type}</span><span class="text-sm text-text-secondary">{item.period}</span></div>
                <h2>{item.title}</h2><p>{item.recommendation}</p>
                <div class="rounded-xl bg-white/5 p-4"><h3 class="font-semibold text-white">Supporting context</h3><p class="mt-2 text-sm text-text-secondary">{item.reason}</p><p class="mt-3 text-sm text-accent font-semibold">{item.metric}</p></div>
                <a class="action inline-block" href={item.type === 'Action' ? '/admission-funnel' : item.title.startsWith('MCA') ? '/campaign-analytics' : '/channel-attribution'}>View related analytics</a>
            </article>
        {/each}
    {:else}
        <div class="grid gap-4 sm:grid-cols-3">
            <div class="panel"><p class="caption">Total budget</p><strong>{money(managerBudget.totalBudget)}</strong></div>
            <div class="panel"><p class="caption">Spent</p><strong>{money(managerBudget.spent)}</strong></div>
            <div class="panel"><p class="caption">Remaining</p><strong>{money(managerBudget.remaining)}</strong></div>
        </div>
        {#if view === 'budget'}
            <section class="panel"><h2>Current channel allocation</h2><div class="mt-5 space-y-4">{#each channels as item}<div><div class="mb-2 flex justify-between gap-3 text-sm"><span>{item.channel}</span><span>{money(item.currentAmount)} · {item.percent}%</span></div><div class="track"><div class="bar" style:width={`${item.percent}%`}></div></div></div>{/each}</div><div class="mt-6"><DataTable rows={currentRows} /></div></section>
        {:else}
            <section class="panel"><h2>Provided scenario comparison</h2><p class="note">The supplied current and simulated outcomes are shown below as a reference scenario.</p><div class="mt-4"><DataTable rows={comparisonRows} /></div></section>
        {/if}
        <section class="panel"><h2>{view === 'budget' ? 'Calculate an allocation' : 'Build your scenario'}</h2>
            <form onsubmit={calculate} oninput={() => { result = null; error = ''; }} class="mt-5 space-y-5">
                <div class="grid gap-4 sm:grid-cols-2">
                    <label class="field">Scenario budget (INR)<input type="number" min="1" max="100000000" step="1" bind:value={budget} required /></label>
                    {#if view === 'budget'}<div class="field"><label for="allocation-strategy">Allocation strategy</label><select id="allocation-strategy" bind:value={strategy}><option value="efficiency">Admission efficiency weighted</option><option value="equal">Equal allocation</option><option value="current">Current allocation mix</option></select></div>{/if}
                </div>
                {#if view === 'simulator'}
                    <button class="action" type="button" onclick={rebalance}>Distribute using current mix</button>
                    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{#each channels as item}<label class="field">{item.channel} allocation (INR)<input type="number" min="0" max="100000000" step="1" bind:value={allocation[item.channel]} required /></label>{/each}</div>
                    <p class="text-sm text-text-secondary">Allocated: {money(allocated)} · Unallocated: {money((budget || 0) - allocated)}</p>
                {/if}
                <p class="note">Estimates use each channel's leads, applications, and admissions per rupee spent. They assume constant efficiency and do not account for saturation. Calculations do not change the saved budget.</p>
                {#if error}<p role="alert" class="text-red-300">{error}</p>{/if}
                <div class="flex flex-wrap gap-3"><button class="action primary" type="submit">{view === 'budget' ? 'Calculate allocation' : 'Run simulation'}</button><button class="action" type="button" onclick={reset}>Reset</button></div>
            </form>
        </section>
        {#if result}
            <section class="panel" aria-live="polite"><h2>Scenario result</h2><p class="note">Projected outcomes for {money(result.budget)} across {channels.length} channels.</p>
                <div class="grid gap-4 my-5 sm:grid-cols-2 xl:grid-cols-4"><div><p class="caption">Estimated leads</p><strong>{number(result.leads)}</strong></div><div><p class="caption">Estimated applications</p><strong>{number(result.applications)}</strong></div><div><p class="caption">Estimated admissions</p><strong>{number(result.admissions)}</strong></div><div><p class="caption">Cost per admission</p><strong>{result.admissions ? money(result.budget / result.admissions) : '—'}</strong></div></div>
                <p class="note">Current-mix baseline at {money(managerBudget.totalBudget)}: {number(baseline.admissions)} estimated admissions. Scenario change: {result.admissions >= baseline.admissions ? '+' : ''}{number(result.admissions - baseline.admissions)} admissions.</p>
                <div class="mt-5"><DataTable rows={resultRows} /></div>
            </section>
        {/if}
    {/if}
</div>

<style>
    .panel{min-width:0;border:1px solid #ffffff1a;border-radius:1rem;background:var(--color-card,#21182b);padding:1.25rem}
    h2{font-size:1.25rem;font-weight:700;color:white}strong{display:block;font-size:1.6rem;color:white;margin-top:.6rem;overflow-wrap:anywhere}
    .caption{font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-secondary,#b6aec4)}
    .note{font-size:.875rem;line-height:1.6;color:var(--color-text-secondary,#b6aec4);margin-top:.75rem}
    .field{display:grid;gap:.5rem;font-size:.875rem;color:var(--color-text-secondary,#b6aec4)}
    input,select{min-width:0;width:100%;padding:.7rem .85rem;border:1px solid #ffffff26;border-radius:.5rem;background:#171020;color:white}
    .action{padding:.65rem 1rem;border:1px solid #ffffff26;border-radius:.65rem;color:white;cursor:pointer;font-size:.875rem}.action:hover{background:#ffffff0d}.primary{background:var(--color-accent,#a47be0);color:#171020;font-weight:600}
    .track{height:.7rem;background:#ffffff0d;border-radius:999px;overflow:hidden}.bar{height:100%;background:var(--color-accent,#a47be0);border-radius:999px}
    .badge{padding:.25rem .7rem;border-radius:999px;background:#a47be01a;color:var(--color-accent,#a47be0);font-size:.75rem;font-weight:600}
    button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #a47be0;outline-offset:3px}
</style>
