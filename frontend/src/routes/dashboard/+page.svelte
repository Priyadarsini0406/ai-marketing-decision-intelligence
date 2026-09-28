<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type User } from '$lib/api';
  import { managerCampaigns, managerFunnelStages, managerRecommendations, managerChannels } from '$lib/manager-demo';
  import { asPercent, workspaceOverview, type PredictionPreview, type WorkspaceOverview } from '$lib/ml-api';

  let user = $state<User | null>(null);
  let firstName = $derived(user?.name.trim().split(/\s+/)[0] ?? '');
  let overview = $state<WorkspaceOverview | null>(null);
  let overviewError = $state('');
  let busy = $state(false);

  // Real XGBoost scores, highest probability first.
  const topLeads = $derived<PredictionPreview[]>(
    [...(overview?.prediction_preview ?? [])]
      .sort((a, b) => b.probability - a.probability)
      .slice(0, 5)
  );

  const liveStats = $derived(
    overview
      ? [
          { label: 'Student Enquiries', value: overview.summary.leads.toLocaleString(), delta: `${asPercent(overview.summary.leads ? overview.summary.conversions / overview.summary.leads : null)} converted` },
          { label: 'Scored Leads', value: (overview.prediction_summary?.scored ?? 0).toLocaleString(), delta: `mean ${asPercent(overview.prediction_summary?.mean_probability)}` },
          { label: 'High-Potential Leads', value: (overview.prediction_summary?.high ?? 0).toLocaleString(), delta: `${asPercent(overview.prediction_summary?.scored ? overview.prediction_summary.high / overview.prediction_summary.scored : null)} of scored` },
          { label: 'Predicted Admissions', value: (overview.prediction_summary?.predicted_admissions ?? 0).toLocaleString(), delta: 'probability ≥ 50%' },
          { label: 'Marketing Spend', value: `₹${(overview.summary.ad_spend / 100000).toFixed(1)}L`, delta: 'ad spend recorded' }
        ]
      : []
  );

  async function loadOverview() {
    busy = true;
    overviewError = '';
    try { overview = await workspaceOverview(); } catch (error) { overviewError = (error as Error).message; } finally { busy = false; }
  }

  onMount(async () => {
    try { user = await api('/auth/me'); } catch { user = null; }
    await loadOverview();
  });
</script>

<svelte:head>
  <title>Manager Dashboard | DecisionIntel</title>
</svelte:head>

<div class="space-y-6 pb-10">
  <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Manager dashboard</p>
      <h1 class="mt-2 text-3xl font-bold text-white">{firstName ? `Welcome back, ${firstName}` : 'Welcome back'}</h1>
      <p class="mt-2 max-w-2xl text-text-secondary">Track your admission performance and make data-driven marketing decisions.</p>
    </div>
  <div class="flex flex-wrap gap-3">
    <a href="/student-leads/new" class="rounded-xl border border-white/10 bg-card px-4 py-2 text-sm font-medium text-white">+ Add Student Lead</a>
    <a href="/budget-optimization" class="rounded-xl bg-accent px-4 py-2 text-sm font-bold text-white">Optimize Budget</a>
    <button class="rounded-xl border border-white/10 bg-card px-4 py-2 text-sm font-medium text-white disabled:opacity-50" onclick={loadOverview} disabled={busy}>{busy ? 'Refreshing…' : 'Refresh model data'}</button>
  </div>
</div>

{#if overviewError}<p role="alert" class="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">{overviewError}</p>{/if}

<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
  {#each liveStats as stat}
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.18em] text-text-secondary">{stat.label}</p>
      <div class="mt-3 flex items-end justify-between">
        <span class="text-3xl font-bold text-white">{stat.value}</span>
        <span class="text-sm font-semibold text-text-secondary">{stat.delta}</span>
      </div>
    </div>
  {/each}
</div>

  <div class="rounded-2xl border border-white/10 bg-card p-5">
    <div class="mb-5 flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">Admission Funnel</h2>

      <a href="/admission-funnel" class="text-sm font-medium text-accent">View Full Funnel</a>
    </div>

    <div class="grid gap-4 md:grid-cols-5">
      {#each managerFunnelStages as stage}
        <div class="rounded-xl border border-white/10 bg-black/10 p-4">
          <div class="mb-3 flex items-center justify-between">
            <span class="text-xs uppercase tracking-[0.16em] text-text-secondary">{stage.name}</span>
            <span class="text-xs text-accent">{stage.conversion}%</span>
          </div>
          <div class="mb-2 text-3xl font-bold text-white">{stage.count}</div>
          <div class="text-sm text-text-secondary">Drop-off: {stage.dropOff}%</div>
        </div>
      {/each}
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-xl font-bold text-white">Marketing Channel Performance</h2>
        <a href="/channel-attribution" class="text-sm font-medium text-accent">View Channel Analytics</a>
      </div>

      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {#each managerChannels.slice(0, 6) as channel}
          <div class="rounded-xl border border-white/10 bg-black/10 p-4">
            <div class="mb-3 flex items-center justify-between">
              <span class="text-sm font-semibold text-white">{channel.channel}</span>
              <span class="text-xs text-accent">{channel.conversion}%</span>
            </div>
            <div class="space-y-2 text-sm text-text-secondary">
              <p>Leads: <span class="text-white">{channel.leads}</span></p>
              <p>Applications: <span class="text-white">{channel.applications}</span></p>
              <p>Admissions: <span class="text-white">{channel.admissions}</span></p>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">Budget Overview</h2>
      <div class="mt-4 space-y-3 text-sm text-text-secondary">
        <p>Total Budget: <span class="text-white">₹10,00,000</span></p>
        <p>Spent: <span class="text-white">₹7,20,000</span></p>
        <p>Remaining: <span class="text-white">₹2,80,000</span></p>
      </div>
      <div class="mt-5 h-2.5 rounded-full bg-white/5">
        <div class="h-full rounded-full bg-accent" style="width: 72%"></div>
      </div>
      <a href="/budget-optimization" class="mt-5 inline-block rounded-xl bg-accent px-4 py-2 text-sm font-bold text-white">Optimize Budget</a>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-xl font-bold text-white">Highest-Propensity Scored Leads</h2>
        <a href="/admission-prediction" class="text-sm font-medium text-accent">View all</a>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
            <tr>
              <th class="px-3 py-2">Lead</th>
              <th class="px-3 py-2">Probability</th>
              <th class="px-3 py-2">Band</th>
              <th class="px-3 py-2">Segment</th>
              <th class="px-3 py-2">Source</th>
              <th class="px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {#each topLeads as lead}
              <tr class="border-b border-white/5 text-white">
                <td class="px-3 py-3">{lead.customer_id ?? lead.lead_id}</td>
                <td class="px-3 py-3 text-accent">{asPercent(lead.probability)}</td>
                <td class="px-3 py-3">{lead.score}</td>
                <td class="px-3 py-3">{lead.segment}</td>
                <td class="px-3 py-3">{lead.source}</td>
                <td class="px-3 py-3"><a href={`/admission-prediction?lead=${lead.lead_id}`} class="text-accent">View</a></td>
              </tr>
            {:else}
              <tr><td colspan="6" class="px-3 py-6 text-text-secondary">No scored leads yet. Run the training import to populate predictions.</td></tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">AI Insights</h2>
      <div class="mt-4 space-y-4">
        {#each managerRecommendations.slice(0, 2) as recommendation}
          <div class="rounded-xl border border-white/10 bg-black/10 p-4">
            <p class="text-sm font-semibold text-white">{recommendation.title}</p>
            <p class="mt-2 text-sm text-text-secondary">{recommendation.reason}</p>
          </div>
        {/each}
      </div>
      <a href="/ai-recommendations" class="mt-5 inline-block rounded-xl border border-white/10 bg-card px-4 py-2 text-sm font-medium text-white">View Recommendations</a>
    </div>
  </div>

  <div class="rounded-2xl border border-white/10 bg-card p-5">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">Campaign Performance</h2>
      <a href="/campaign-analytics" class="text-sm font-medium text-accent">View Campaign Analytics</a>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
          <tr>
            <th class="px-3 py-2">Campaign</th>
            <th class="px-3 py-2">Spend</th>
            <th class="px-3 py-2">Leads</th>
            <th class="px-3 py-2">Admissions</th>
            <th class="px-3 py-2">Conversion</th>
          </tr>
        </thead>
        <tbody>
          {#each managerCampaigns as campaign}
            <tr class="border-b border-white/5 text-white">
              <td class="px-3 py-3">{campaign.name}</td>
              <td class="px-3 py-3">₹{campaign.spend.toLocaleString()}</td>
              <td class="px-3 py-3">{campaign.leads}</td>
              <td class="px-3 py-3">{campaign.admissions}</td>
              <td class="px-3 py-3 text-accent">{campaign.conversion}%</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
