<script lang="ts">
  import { onMount } from 'svelte';
  import { managerBudget, managerCampaigns, managerChannels, managerFunnelStages, whatIfScenario } from '$lib/manager-demo';

  type Priority = 'High' | 'Medium' | 'Low';
  type RecommendationStatus = 'New' | 'Reviewed' | 'Dismissed';
  type RecommendationCategory = 'Lead Conversion' | 'Marketing Channel' | 'Campaign Performance' | 'Budget Allocation' | 'Admission Funnel' | 'Student Leads';

  type Recommendation = {
    id: string;
    title: string;
    priority: Priority;
    category: RecommendationCategory;
    recommendation: string;
    reason: string;
    supportingMetric: string;
    potentialImpact: string;
    generatedDate: string;
    status: RecommendationStatus;
    channel?: string;
    campaign?: string;
    currentMetric: string;
    referenceMetric: string;
    daysAgo: number;
  };

  const baseRecommendations: Recommendation[] = [
    {
      id: 'rec-portal-allocation',
      title: 'Review Education Portal Allocation',
      priority: 'Medium',
      category: 'Budget Allocation',
      recommendation: 'Consider reviewing the current Education Portal allocation based on its recent admission conversion performance.',
      reason: 'Recent campaign data shows lower admission conversion from Education Portals compared with selected channels and a higher cost per admission profile.',
      supportingMetric: 'Conversion Rate: 4.2%',
      potentialImpact: 'Potential improvement in budget efficiency',
      generatedDate: '2026-09-12',
      status: 'New',
      channel: 'Education Portals',
      currentMetric: '4.2%',
      referenceMetric: 'Website: 25.6%',
      daysAgo: 6
    },
    {
      id: 'rec-google-retarget',
      title: 'Review Google Ads Retargeting Mix',
      priority: 'High',
      category: 'Marketing Channel',
      recommendation: 'Shift a portion of the Google Ads budget toward retargeting and high-intent landing-page traffic to improve conversion quality.',
      reason: 'Google Ads remains the largest lead generator, but lower conversion efficiency relative to website and referral traffic suggests a need to review the campaign mix.',
      supportingMetric: 'CPL: ₹710 | CPA: ₹3,793',
      potentialImpact: 'Estimated impact on lead quality',
      generatedDate: '2026-09-10',
      status: 'New',
      channel: 'Google Ads',
      currentMetric: '18.7% conversion',
      referenceMetric: 'Website: 25.6% conversion',
      daysAgo: 8
    },
    {
      id: 'rec-referral-priority',
      title: 'Increase Referral Channel Focus',
      priority: 'High',
      category: 'Lead Conversion',
      recommendation: 'Prioritize referral campaigns and partner outreach for high-probability leads that already show strong application intent.',
      reason: 'Referral traffic has the highest conversion efficiency and the lowest cost per admission among the current acquisition sources.',
      supportingMetric: 'CPA: ₹1,250',
      potentialImpact: 'Estimated impact on conversion efficiency',
      generatedDate: '2026-09-09',
      status: 'Reviewed',
      channel: 'Referral',
      currentMetric: '28.1% conversion',
      referenceMetric: 'Average CPA: ₹3,800',
      daysAgo: 9
    },
    {
      id: 'rec-funnel-dropoff',
      title: 'Address Application Stage Drop-off',
      priority: 'High',
      category: 'Admission Funnel',
      recommendation: 'Review the counselling-to-application transition workflow to reduce drop-off before the final submission stage.',
      reason: 'The application stage shows a sharper drop-off than the earlier counselling stage, indicating friction in the application journey.',
      supportingMetric: 'Application drop-off: 41.0%',
      potentialImpact: 'Potential improvement in admission volume',
      generatedDate: '2026-09-08',
      status: 'New',
      currentMetric: '41.0% drop-off',
      referenceMetric: 'Counselling: 23.7% drop-off',
      daysAgo: 10
    },
    {
      id: 'rec-campaign-scholarship',
      title: 'Evaluate Scholarship Campaign Efficiency',
      priority: 'Medium',
      category: 'Campaign Performance',
      recommendation: 'Assess the scholarship campaign’s pacing and audience targeting against the better-performing referral and website sources.',
      reason: 'The campaign produces moderate conversion but is spending at a higher efficiency cost than the more efficient referral and website channels.',
      supportingMetric: 'Conversion Rate: 14.5%',
      potentialImpact: 'Potential improvement in cost efficiency',
      generatedDate: '2026-09-06',
      status: 'New',
      campaign: 'Scholarship Campaign',
      channel: 'Instagram',
      currentMetric: '14.5% conversion',
      referenceMetric: 'Website: 25.6% conversion',
      daysAgo: 12
    },
    {
      id: 'rec-lead-prioritization',
      title: 'Prioritize High-Intent Leads for Follow-up',
      priority: 'Low',
      category: 'Student Leads',
      recommendation: 'Continue a measured follow-up cadence for medium and high-intent leads with incomplete applications to preserve momentum.',
      reason: 'Lead quality remains strongest when counselling and application follow-up are aligned with the student’s current intent and engagement level.',
      supportingMetric: 'High-Intent leads: 286',
      potentialImpact: 'Potential impact on lead nurturing efficiency',
      generatedDate: '2026-09-03',
      status: 'Dismissed',
      currentMetric: '286 high-intent leads',
      referenceMetric: '198 low-intent leads',
      daysAgo: 15
    }
  ];

  let recommendations: Recommendation[] = $state(baseRecommendations);
  let query = $state('');
  let selectedPriority = $state<'All' | Priority>('All');
  let selectedCategory = $state<'All' | RecommendationCategory>('All');
  let selectedChannel = $state<'All' | string>('All');
  let selectedCampaign = $state<'All' | string>('All');
  let selectedStatus = $state<'All' | RecommendationStatus>('All');
  let selectedDateRange = $state<'All' | '7d' | '30d' | '90d'>('30d');
  let selectedRecommendation: Recommendation | null = $state(null);
  let loading = $state(true);
  let pageError = $state<string | null>(null);

  const dateRanges = ['All', '7d', '30d', '90d'] as const;
  const priorityNames: Array<'All' | Priority> = ['All', 'High', 'Medium', 'Low'];
  const categoryNames: Array<'All' | RecommendationCategory> = ['All', 'Lead Conversion', 'Marketing Channel', 'Campaign Performance', 'Budget Allocation', 'Admission Funnel', 'Student Leads'];
  const channelNames: Array<'All' | string> = ['All', ...new Set(managerChannels.map((channel) => channel.channel))];
  const campaignNames: Array<'All' | string> = ['All', ...new Set(managerCampaigns.map((campaign) => campaign.name))];
  const statusNames: Array<'All' | RecommendationStatus> = ['All', 'New', 'Reviewed', 'Dismissed'];

  const priorityTone: Record<Priority, string> = {
    High: 'border-red-400/30 bg-red-500/10 text-red-200',
    Medium: 'border-amber-400/30 bg-amber-500/10 text-amber-200',
    Low: 'border-sky-400/30 bg-sky-500/10 text-sky-200'
  };

  const statusTone: Record<RecommendationStatus, string> = {
    New: 'border-accent/30 bg-accent/10 text-accent',
    Reviewed: 'border-emerald-400/30 bg-emerald-500/10 text-emerald-200',
    Dismissed: 'border-white/10 bg-white/5 text-text-secondary'
  };

  const filteredRecommendations = $derived.by((): Recommendation[] => {
    const term = query.trim().toLowerCase();
    return recommendations.filter((item: Recommendation) => {
      const priorityMatch = selectedPriority === 'All' || item.priority === selectedPriority;
      const categoryMatch = selectedCategory === 'All' || item.category === selectedCategory;
      const channelMatch = selectedChannel === 'All' || item.channel === selectedChannel;
      const campaignMatch = selectedCampaign === 'All' || item.campaign === selectedCampaign;
      const statusMatch = selectedStatus === 'All' || item.status === selectedStatus;
      const dateMatch = selectedDateRange === 'All' || item.daysAgo <= Number(selectedDateRange.replace('d', ''));
      const searchMatch = !term || [item.title, item.category, item.channel ?? '', item.campaign ?? '', item.reason].join(' ').toLowerCase().includes(term);
      return priorityMatch && categoryMatch && channelMatch && campaignMatch && statusMatch && dateMatch && searchMatch;
    });
  });

  const overview = $derived.by(() => {
    const total = recommendations.length;
    const high = recommendations.filter((item: Recommendation) => item.priority === 'High').length;
    const medium = recommendations.filter((item: Recommendation) => item.priority === 'Medium').length;
    const low = recommendations.filter((item: Recommendation) => item.priority === 'Low').length;
    return {
      total,
      high,
      medium,
      low,
      conversionImpact: '12.4%',
      budgetEfficiency: '8.7%'
    };
  });

  type ChannelInsight = (typeof managerChannels)[number] & { insight: string };
  const channelInsights: ChannelInsight[] = managerChannels.map((channel) => {
    let insight = 'Requires monitoring';
    if (channel.conversion >= 20) insight = 'High conversion performance';
    else if (channel.costPerAdmission > 4500) insight = 'High cost per admission';
    else if (channel.leads >= 200) insight = 'Strong lead generation';
    else if (channel.applications / Math.max(channel.leads, 1) < 0.45) insight = 'Low application conversion';
    return { ...channel, insight };
  });

  type CampaignInsight = (typeof managerCampaigns)[number] & { insight: string };
  const campaignInsights: CampaignInsight[] = managerCampaigns.map((campaign) => {
    let insight = 'Requires monitoring';
    if (campaign.conversion >= 16) insight = 'Strong campaign efficiency';
    else if (campaign.conversion < 12) insight = 'Needs campaign review';
    else if (campaign.admissions > 50) insight = 'High admission yield';
    return { ...campaign, insight };
  });

  type FunnelInsight = (typeof managerFunnelStages)[number] & { insight: string };
  const funnelInsights: FunnelInsight[] = managerFunnelStages.map((stage, index) => {
    let insight = 'Stable performance';
    if (index === 3 && stage.dropOff > 35) insight = 'Application stage has a higher drop-off than the previous stage.';
    else if (index === 2 && stage.dropOff > 20) insight = 'Counselling conversion is declining compared with earlier stages.';
    else if (index === 4) insight = 'Admission stage shows strong final conversion quality.';
    return { ...stage, insight };
  });

  type BudgetInsight = {
    channel: string;
    currentAllocation: number;
    recommendedAllocation: number;
    difference: number;
    efficiencyMetric: string;
    insight: string;
  };
  const budgetInsights: BudgetInsight[] = managerBudget.allocations.map((allocation) => {
    const source = managerChannels.find((channel) => channel.channel === allocation.channel);
    const recommendedPercent = Math.max(6, Math.min(35, allocation.percent + (source && source.conversion >= 20 ? 4 : -2) + (source && source.costPerAdmission > 4500 ? -2 : 1)));
    const delta = recommendedPercent - allocation.percent;
    let insight = 'Requires review';
    if (delta > 0) insight = 'Allocation increased';
    else if (delta < 0) insight = 'Allocation decreased';
    if (source && source.conversion >= 20 && delta >= 0) insight = 'Stronger conversion efficiency';
    if (source && source.costPerAdmission > 4500) insight = 'Higher CPA';
    return {
      channel: allocation.channel,
      currentAllocation: allocation.currentAmount,
      recommendedAllocation: Math.round((managerBudget.totalBudget * recommendedPercent) / 100),
      difference: Math.round(((recommendedPercent - allocation.percent) / 100) * managerBudget.totalBudget),
      efficiencyMetric: source ? `${source.conversion}% conversion` : 'N/A',
      insight
    };
  });

  const simulationSummary = {
    currentBudget: `₹${managerBudget.totalBudget.toLocaleString()}`,
    simulatedBudget: `₹${(managerBudget.totalBudget * 0.92).toLocaleString()}`,
    currentAdmissions: whatIfScenario.current.admissions,
    simulatedAdmissions: whatIfScenario.simulated.admissions,
    change: `+${whatIfScenario.simulated.admissions - whatIfScenario.current.admissions} admissions`
  };

  function openRecommendation(item: Recommendation) {
    selectedRecommendation = item;
  }

  function updateRecommendationStatus(nextStatus: RecommendationStatus) {
    if (!selectedRecommendation) return;
    const activeId = selectedRecommendation.id;
    recommendations = recommendations.map((item: Recommendation) =>
      item.id === activeId ? { ...item, status: nextStatus } : item
    );
    selectedRecommendation = { ...selectedRecommendation, status: nextStatus };
  }

  function clearFilters() {
    query = '';
    selectedPriority = 'All';
    selectedCategory = 'All';
    selectedChannel = 'All';
    selectedCampaign = 'All';
    selectedStatus = 'All';
    selectedDateRange = '30d';
  }

  onMount(() => {
    const timer = window.setTimeout(() => {
      loading = false;
    }, 150);
    return () => window.clearTimeout(timer);
  });
</script>

<svelte:head>
  <title>AI Recommendations | DecisionIntel</title>
</svelte:head>

<div class="space-y-6 pb-10">
  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Decision support</p>
    <h1 class="mt-2 text-3xl font-bold text-white">AI Recommendations</h1>
    <p class="mt-2 max-w-3xl text-text-secondary">Use marketing and admission intelligence to identify actionable opportunities for improving student lead conversion and budget efficiency.</p>
    <div class="mt-3 inline-flex items-center rounded-full border border-accent/25 bg-accent/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-accent">Demo Recommendation Engine</div>
  </div>

  {#if pageError}
    <div class="dashboard-card border border-red-500/30 bg-red-500/8 p-4 text-sm text-red-200">{pageError}</div>
  {/if}

  <section class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <h2 class="text-xl font-bold text-white">Recommendation Overview</h2>
      <span class="text-xs uppercase tracking-[0.18em] text-text-secondary">Demo Insights</span>
    </div>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Recommendations</p>
        <p class="mt-3 text-3xl font-bold text-white">{overview.total}</p>
      </div>
      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">High Priority</p>
        <p class="mt-3 text-3xl font-bold text-white">{overview.high}</p>
      </div>
      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Medium Priority</p>
        <p class="mt-3 text-3xl font-bold text-white">{overview.medium}</p>
      </div>
      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Low Priority</p>
        <p class="mt-3 text-3xl font-bold text-white">{overview.low}</p>
      </div>
      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Potential Conversion Improvement</p>
        <p class="mt-3 text-3xl font-bold text-white">{overview.conversionImpact}</p>
      </div>
      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Potential Budget Efficiency</p>
        <p class="mt-3 text-3xl font-bold text-white">{overview.budgetEfficiency}</p>
      </div>
    </div>
  </section>

  <section class="dashboard-card p-5">
    <div class="mb-4 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">Priority Recommendations</h2>
        <p class="mt-1 text-sm text-text-secondary">Recommendation logic is rule-based demo analysis using current channel, campaign, funnel, and budget data.</p>
      </div>
      <button type="button" class="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-text-secondary hover:text-white" onclick={clearFilters}>Reset Filters</button>
    </div>

    <div class="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-6">
      <label class="block text-sm">
        <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Search</span>
        <input bind:value={query} class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white placeholder:text-text-secondary" placeholder="Search recommendations..." />
      </label>
      <label class="block text-sm">
        <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Date Range</span>
        <select bind:value={selectedDateRange} class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white">
          {#each dateRanges as range}
            <option value={range}>{range === 'All' ? 'All' : range}</option>
          {/each}
        </select>
      </label>
      <label class="block text-sm">
        <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Priority</span>
        <select bind:value={selectedPriority} class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white">
          {#each priorityNames as priority}
            <option value={priority}>{priority === 'All' ? 'All' : priority}</option>
          {/each}
        </select>
      </label>
      <label class="block text-sm">
        <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Category</span>
        <select bind:value={selectedCategory} class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white">
          {#each categoryNames as category}
            <option value={category}>{category === 'All' ? 'All' : category}</option>
          {/each}
        </select>
      </label>
      <label class="block text-sm">
        <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Channel</span>
        <select bind:value={selectedChannel} class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white">
          {#each channelNames as channel}
            <option value={channel}>{channel === 'All' ? 'All' : channel}</option>
          {/each}
        </select>
      </label>
      <label class="block text-sm">
        <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Status</span>
        <select bind:value={selectedStatus} class="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-white">
          {#each statusNames as status}
            <option value={status}>{status === 'All' ? 'All' : status}</option>
          {/each}
        </select>
      </label>
    </div>

    {#if loading}
      <div class="rounded-2xl border border-white/10 bg-black/10 p-6 text-sm text-text-secondary">Loading recommendations…</div>
    {:else if filteredRecommendations.length === 0}
      <div class="rounded-2xl border border-dashed border-white/15 bg-black/10 p-6 text-sm text-text-secondary">No recommendations available for the selected filters.</div>
    {:else}
      <div class="grid gap-4 xl:grid-cols-2">
        {#each filteredRecommendations as recommendation}
          <article class="rounded-2xl border border-white/10 bg-black/10 p-5 transition-all duration-200 hover:border-accent/70 hover:bg-accent/4 hover:shadow-[0_0_18px_rgba(164,123,224,0.12)]">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-xs uppercase tracking-[0.18em] text-accent">{recommendation.category}</p>
                <h3 class="mt-2 text-xl font-bold text-white">{recommendation.title}</h3>
              </div>
              <span class={`inline-flex rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] ${priorityTone[recommendation.priority]}`}>
                {recommendation.priority}
              </span>
            </div>

            <div class="mt-4 space-y-3 text-sm text-text-secondary">
              <p><span class="font-semibold text-white">Recommendation:</span> {recommendation.recommendation}</p>
              <p><span class="font-semibold text-white">Reason:</span> {recommendation.reason}</p>
              <p><span class="font-semibold text-white">Supporting Metric:</span> {recommendation.supportingMetric}</p>
              <p><span class="font-semibold text-white">Potential Impact:</span> {recommendation.potentialImpact}</p>
            </div>

            <div class="mt-4 flex flex-wrap items-center gap-2 text-xs">
              <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-text-secondary">{recommendation.generatedDate}</span>
              <span class={`rounded-full border px-2 py-1 ${statusTone[recommendation.status]}`}>{recommendation.status}</span>
            </div>

            <div class="mt-5 flex items-center justify-between">
              <button type="button" class="rounded-xl border border-white/10 bg-card px-3 py-2 text-sm font-medium text-white hover:border-accent/40" onclick={() => openRecommendation(recommendation)}>View Details</button>
              <a href="/channel-attribution" class="text-sm text-accent">Related Data</a>
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </section>

  <section class="grid gap-6 xl:grid-cols-2">
    <div class="dashboard-card p-5">
      <h2 class="text-xl font-bold text-white">Channel Insights</h2>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
            <tr>
              <th class="px-2 py-2">Channel</th>
              <th class="px-2 py-2">Spend</th>
              <th class="px-2 py-2">Leads</th>
              <th class="px-2 py-2">Admissions</th>
              <th class="px-2 py-2">Conversion</th>
              <th class="px-2 py-2">CPL</th>
              <th class="px-2 py-2">CPA</th>
              <th class="px-2 py-2">Insight</th>
            </tr>
          </thead>
          <tbody>
            {#each channelInsights as channel}
              <tr class="border-b border-white/5 text-white">
                <td class="px-2 py-3">{channel.channel}</td>
                <td class="px-2 py-3">₹{channel.spend.toLocaleString()}</td>
                <td class="px-2 py-3">{channel.leads}</td>
                <td class="px-2 py-3">{channel.admissions}</td>
                <td class="px-2 py-3">{channel.conversion}%</td>
                <td class="px-2 py-3">₹{channel.costPerLead}</td>
                <td class="px-2 py-3">₹{channel.costPerAdmission}</td>
                <td class="px-2 py-3 text-text-secondary">{channel.insight}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <div class="dashboard-card p-5">
      <h2 class="text-xl font-bold text-white">Campaign Insights</h2>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
            <tr>
              <th class="px-2 py-2">Campaign</th>
              <th class="px-2 py-2">Channel</th>
              <th class="px-2 py-2">Spend</th>
              <th class="px-2 py-2">Leads</th>
              <th class="px-2 py-2">Admissions</th>
              <th class="px-2 py-2">Conversion</th>
              <th class="px-2 py-2">CPA</th>
              <th class="px-2 py-2">Insight</th>
            </tr>
          </thead>
          <tbody>
            {#each campaignInsights as campaign}
              <tr class="border-b border-white/5 text-white">
                <td class="px-2 py-3">{campaign.name}</td>
                <td class="px-2 py-3">{campaign.channel}</td>
                <td class="px-2 py-3">₹{campaign.spend.toLocaleString()}</td>
                <td class="px-2 py-3">{campaign.leads}</td>
                <td class="px-2 py-3">{campaign.admissions}</td>
                <td class="px-2 py-3">{campaign.conversion}%</td>
                <td class="px-2 py-3">₹{Math.round(campaign.spend / Math.max(campaign.admissions, 1))}</td>
                <td class="px-2 py-3 text-text-secondary">{campaign.insight}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="grid gap-6 xl:grid-cols-2">
    <div class="dashboard-card p-5">
      <h2 class="text-xl font-bold text-white">Admission Funnel Insights</h2>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
            <tr>
              <th class="px-2 py-2">Stage</th>
              <th class="px-2 py-2">Current Count</th>
              <th class="px-2 py-2">Conversion Rate</th>
              <th class="px-2 py-2">Drop-off</th>
              <th class="px-2 py-2">Insight</th>
            </tr>
          </thead>
          <tbody>
            {#each funnelInsights as stage}
              <tr class="border-b border-white/5 text-white">
                <td class="px-2 py-3">{stage.name}</td>
                <td class="px-2 py-3">{stage.count}</td>
                <td class="px-2 py-3">{stage.conversion}%</td>
                <td class="px-2 py-3">{stage.dropOff}%</td>
                <td class="px-2 py-3 text-text-secondary">{stage.insight}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <div class="dashboard-card p-5">
      <h2 class="text-xl font-bold text-white">Budget Insights</h2>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
            <tr>
              <th class="px-2 py-2">Channel</th>
              <th class="px-2 py-2">Current</th>
              <th class="px-2 py-2">Recommended</th>
              <th class="px-2 py-2">Difference</th>
              <th class="px-2 py-2">Efficiency</th>
              <th class="px-2 py-2">Insight</th>
            </tr>
          </thead>
          <tbody>
            {#each budgetInsights as item}
              <tr class="border-b border-white/5 text-white">
                <td class="px-2 py-3">{item.channel}</td>
                <td class="px-2 py-3">₹{item.currentAllocation.toLocaleString()}</td>
                <td class="px-2 py-3">₹{item.recommendedAllocation.toLocaleString()}</td>
                <td class="px-2 py-3">₹{item.difference.toLocaleString()}</td>
                <td class="px-2 py-3">{item.efficiencyMetric}</td>
                <td class="px-2 py-3 text-text-secondary">{item.insight}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="dashboard-card p-5">
    <div class="flex items-center justify-between gap-4">
      <h2 class="text-xl font-bold text-white">Related Simulation</h2>
      <a href="/what-if" class="text-sm text-accent">View What-If</a>
    </div>
    <div class="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Current Budget</p>
        <p class="mt-2 text-xl font-bold text-white">{simulationSummary.currentBudget}</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Simulated Budget</p>
        <p class="mt-2 text-xl font-bold text-white">{simulationSummary.simulatedBudget}</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Current Admissions</p>
        <p class="mt-2 text-xl font-bold text-white">{simulationSummary.currentAdmissions}</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Simulated Admissions</p>
        <p class="mt-2 text-xl font-bold text-white">{simulationSummary.simulatedAdmissions}</p>
      </div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Change</p>
        <p class="mt-2 text-xl font-bold text-white">{simulationSummary.change}</p>
      </div>
    </div>
    <div class="mt-4 rounded-xl border border-accent/25 bg-accent/10 p-3 text-sm text-accent">Simulation Result: No actual budget changes were made.</div>
  </section>

  <section class="dashboard-card p-5">
    <h2 class="text-xl font-bold text-white">Recommendation Details</h2>
    <p class="mt-1 text-sm text-text-secondary">Each recommendation remains a decision-support suggestion requiring human review before any action is taken.</p>
  </section>
</div>

{#if selectedRecommendation}
  <div class="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" aria-modal="true" role="dialog">
    <aside class="h-full w-full max-w-xl overflow-y-auto border-l border-white/10 bg-card p-6">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent">{selectedRecommendation.category}</p>
          <h3 class="mt-2 text-2xl font-bold text-white">{selectedRecommendation.title}</h3>
        </div>
        <button type="button" class="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-text-secondary hover:text-white" onclick={() => (selectedRecommendation = null)}>Close</button>
      </div>

      <div class="mt-6 space-y-4 text-sm text-text-secondary">
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Recommendation</p>
          <p class="mt-2 text-white">{selectedRecommendation.recommendation}</p>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Priority</p>
            <p class="mt-2 text-white">{selectedRecommendation.priority}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Status</p>
            <p class="mt-2 text-white">{selectedRecommendation.status}</p>
          </div>
        </div>
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Reason</p>
          <p class="mt-2 text-white">{selectedRecommendation.reason}</p>
        </div>
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Supporting Data</p>
          <p class="mt-2 text-white">{selectedRecommendation.supportingMetric}</p>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Current Metric</p>
            <p class="mt-2 text-white">{selectedRecommendation.currentMetric}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Reference Metric</p>
            <p class="mt-2 text-white">{selectedRecommendation.referenceMetric}</p>
          </div>
        </div>
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
          <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Potential Impact</p>
          <p class="mt-2 text-white">{selectedRecommendation.potentialImpact}</p>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Related Channel</p>
            <p class="mt-2 text-white">{selectedRecommendation.channel ?? 'General'}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Related Campaign</p>
            <p class="mt-2 text-white">{selectedRecommendation.campaign ?? 'General'}</p>
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Generated Date</p>
            <p class="mt-2 text-white">{selectedRecommendation.generatedDate}</p>
          </div>
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Status</p>
            <p class="mt-2 text-white">{selectedRecommendation.status}</p>
          </div>
        </div>
      </div>

      <div class="mt-6 flex flex-wrap gap-3">
        <button type="button" class="rounded-xl bg-accent px-4 py-2 text-sm font-bold text-white" onclick={() => updateRecommendationStatus('Reviewed')}>Mark as Reviewed</button>
        <button type="button" class="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white" onclick={() => updateRecommendationStatus('Dismissed')}>Dismiss</button>
        <a href="/channel-attribution" class="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white">View Related Data</a>
      </div>
    </aside>
  </div>
{/if}
