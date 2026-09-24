<script lang="ts">
  import {
    managerBudget,
    managerCampaigns,
    managerChannels,
    managerFunnelStages,
    managerLeads,
    managerRecommendations,
    whatIfScenario,
    type LeadStatus
  } from '$lib/manager-demo';

  const reportTypes = [
    'Lead Performance',
    'Admission Prediction',
    'Admission Funnel',
    'Channel Attribution',
    'Campaign Analytics',
    'Budget Performance',
    'Conversion Performance',
    'Executive Summary'
  ] as const;

  type ReportType = (typeof reportTypes)[number];
  const dateRanges = ['Last 7 Days', 'Last 30 Days', 'Last 3 Months', 'Last 6 Months', 'This Year'] as const;
  type DateRange = (typeof dateRanges)[number];

  let selectedReportType: ReportType = $state('Executive Summary');
  let selectedDateRange: DateRange = $state('Last 30 Days');
  let startDate = $state('2026-08-01');
  let endDate = $state('2026-09-18');
  let selectedCourse = $state('All');
  let selectedChannel = $state('All');
  let selectedCampaign = $state('All');
  let selectedLeadSource = $state('All');
  let selectedLeadStatus: 'All' | LeadStatus = $state('All');

  const courseOptions = ['All', ...new Set(managerLeads.map((lead) => lead.course_interested))];
  const channelOptions = ['All', ...new Set(managerChannels.map((channel) => channel.channel))];
  const campaignOptions = ['All', ...new Set(managerCampaigns.map((campaign) => campaign.name))];
  const leadSourceOptions = ['All', ...new Set(managerLeads.map((lead) => lead.lead_source))];
  const leadStatusOptions = ['All', ...new Set(managerLeads.map((lead) => lead.lead_status))] as Array<'All' | LeadStatus>;

  const dateRangeFactor: Record<DateRange, number> = {
    'Last 7 Days': 0.62,
    'Last 30 Days': 1,
    'Last 3 Months': 1.38,
    'Last 6 Months': 1.76,
    'This Year': 2.2
  };

  const reportIcon: Record<ReportType, string> = {
    'Lead Performance': '◌',
    'Admission Prediction': '◇',
    'Admission Funnel': '▽',
    'Channel Attribution': '↗',
    'Campaign Analytics': '◧',
    'Budget Performance': '◒',
    'Conversion Performance': '◐',
    'Executive Summary': '▤'
  };

  const filteredLeads = $derived.by(() =>
    managerLeads.filter((lead) => {
      const courseMatch = selectedCourse === 'All' || lead.course_interested === selectedCourse;
      const channelMatch = selectedChannel === 'All' || lead.source === selectedChannel || lead.lead_source === selectedChannel;
      const campaignMatch = selectedCampaign === 'All' || lead.assigned_to === selectedCampaign || lead.source === selectedCampaign;
      const sourceMatch = selectedLeadSource === 'All' || lead.lead_source === selectedLeadSource || lead.source === selectedLeadSource;
      const statusMatch = selectedLeadStatus === 'All' || lead.lead_status === selectedLeadStatus;
      return courseMatch && channelMatch && campaignMatch && sourceMatch && statusMatch;
    })
  );

  const filteredChannels = $derived.by(() => {
    const factor = dateRangeFactor[selectedDateRange];
    return managerChannels
      .filter((channel) => selectedChannel === 'All' || channel.channel === selectedChannel)
      .map((channel) => ({
        ...channel,
        spend: Math.round(channel.spend * factor),
        leads: Math.round(channel.leads * factor),
        applications: Math.round(channel.applications * factor),
        admissions: Math.round(channel.admissions * factor),
        conversion: Number(((channel.conversion * (1 + (factor - 1) * 0.18)).toFixed(1)))
      }));
  });

  const filteredCampaigns = $derived.by(() => {
    const factor = dateRangeFactor[selectedDateRange];
    return managerCampaigns
      .filter((campaign) => selectedCampaign === 'All' || campaign.name === selectedCampaign)
      .map((campaign) => ({
        ...campaign,
        spend: Math.round(campaign.spend * factor),
        leads: Math.round(campaign.leads * factor),
        applications: Math.round(campaign.applications * factor),
        admissions: Math.round(campaign.admissions * factor),
        conversion: Number(((campaign.conversion * (1 + (factor - 1) * 0.12)).toFixed(1)))
      }));
  });

  const funnelData = $derived.by(() => {
    const factor = dateRangeFactor[selectedDateRange];
    return managerFunnelStages.map((stage) => ({
      ...stage,
      count: Math.round(stage.count * factor),
      conversion: Number((stage.conversion * (1 + (factor - 1) * 0.06)).toFixed(1)),
      dropOff: Number((stage.dropOff * (1 + (factor - 1) * 0.08)).toFixed(1))
    }));
  });

  const kpis = $derived.by(() => {
    const totalEnquiries = Math.round(managerFunnelStages[0].count * dateRangeFactor[selectedDateRange]);
    const applications = filteredChannels.reduce((sum, channel) => sum + channel.applications, 0);
    const admissions = filteredChannels.reduce((sum, channel) => sum + channel.admissions, 0);
    const spend = filteredChannels.reduce((sum, channel) => sum + channel.spend, 0);
    const conversionRate = applications > 0 ? (admissions / applications) * 100 : 0;
    const cpa = admissions > 0 ? spend / admissions : 0;
    return {
      totalEnquiries,
      applications,
      admissions,
      conversionRate,
      spend,
      cpa,
      totalLeads: filteredLeads.length
    };
  });

  const leadStatusDistribution = $derived.by(() => {
    const statuses: LeadStatus[] = ['New', 'Contacted', 'Counselling', 'Application', 'Admitted', 'Not Converted'];
    const total = filteredLeads.length || 1;
    return statuses.map((status) => ({
      status,
      count: filteredLeads.filter((lead) => lead.lead_status === status).length,
      share: ((filteredLeads.filter((lead) => lead.lead_status === status).length / total) * 100).toFixed(1)
    }));
  });

  const budgetTable = $derived.by(() =>
    managerBudget.allocations
      .filter((allocation) => selectedChannel === 'All' || allocation.channel === selectedChannel)
      .map((allocation) => {
        const actual = filteredChannels.find((channel) => channel.channel === allocation.channel);
        const currentSpend = actual ? actual.spend : allocation.currentAmount;
        const remaining = allocation.currentAmount - currentSpend;
        const utilization = (currentSpend / Math.max(allocation.currentAmount, 1)) * 100;
        const admissions = actual ? actual.admissions : 0;
        const cpa = admissions > 0 ? currentSpend / admissions : 0;
        return {
          channel: allocation.channel,
          allocated: allocation.currentAmount,
          actualSpend: currentSpend,
          remaining: Math.max(remaining, 0),
          utilization: Number(utilization.toFixed(1)),
          admissions,
          cpa: Math.round(cpa)
        };
      })
  );

  let generationState = $state<'idle' | 'loading' | 'success' | 'error'>('idle');
  let generationMessage = $state('No snapshot generated yet.');

  function generateReport() {
    generationState = 'loading';
    generationMessage = 'Generating report snapshot from the current manager dataset...';

    window.setTimeout(() => {
      if (!selectedReportType) {
        generationState = 'error';
        generationMessage = 'A report type is required before generating a summary.';
        return;
      }

      generationState = 'success';
      generationMessage = `${selectedReportType} snapshot generated for ${selectedDateRange}.`;
    }, 400);
  }

  const aiInsights = managerRecommendations.slice(0, 2);
  const exportConfigured = false;
</script>

<div class="space-y-6 pb-10">
  <div class="dashboard-card p-5 md:p-6">
    <p class="text-xs uppercase tracking-[0.22em] text-accent font-semibold">Manager reporting</p>
    <p class="mt-2 max-w-2xl text-text-secondary">Generate and review consolidated admission, marketing and budget performance reports.</p>
  </div>

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
    <div class="dashboard-card p-5">
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Student Enquiries</p>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.12em] text-accent">Demo Data</span>
      </div>
      <p class="mt-4 text-3xl font-bold text-white">{kpis.totalEnquiries.toLocaleString()}</p>
    </div>

    <div class="dashboard-card p-5">
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Applications</p>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.12em] text-accent">Demo Data</span>
      </div>
      <p class="mt-4 text-3xl font-bold text-white">{kpis.applications.toLocaleString()}</p>
    </div>

    <div class="dashboard-card p-5">
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Admissions</p>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.12em] text-accent">Demo Data</span>
      </div>
      <p class="mt-4 text-3xl font-bold text-white">{kpis.admissions.toLocaleString()}</p>
    </div>

    <div class="dashboard-card p-5">
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Overall Conversion Rate</p>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.12em] text-accent">Demo Data</span>
      </div>
      <p class="mt-4 text-3xl font-bold text-white">{kpis.conversionRate.toFixed(1)}%</p>
    </div>

    <div class="dashboard-card p-5">
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Marketing Spend</p>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.12em] text-accent">Demo Data</span>
      </div>
      <p class="mt-4 text-3xl font-bold text-white">₹{(kpis.spend / 100000).toFixed(1)}L</p>
    </div>

    <div class="dashboard-card p-5">
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Cost Per Admission</p>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.12em] text-accent">Demo Data</span>
      </div>
      <p class="mt-4 text-3xl font-bold text-white">₹{Math.round(kpis.cpa).toLocaleString()}</p>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.7fr_1fr]">
    <div class="dashboard-card p-5 md:p-6">
      <div class="mb-5 flex items-center justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Report type</p>
          <h2 class="mt-2 text-xl font-bold text-white">Generate report</h2>
        </div>
      </div>

      <div class="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {#each reportTypes as type}
          <button
            type="button"
            class={`rounded-xl border px-3 py-2 text-left text-sm transition-all duration-200 ${selectedReportType === type ? 'border-accent bg-accent/10 text-white shadow-[0_0_18px_rgba(164,123,224,0.15)]' : 'border-white/10 bg-white/5 text-text-secondary hover:border-accent/40 hover:text-white'}`}
            onclick={() => (selectedReportType = type)}
          >
            <span class="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-lg border border-white/10 bg-black/20 text-[10px]">{reportIcon[type]}</span>
            {type}
          </button>
        {/each}
      </div>

      <div class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Date range</span>
          <select bind:value={selectedDateRange} class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70">
            {#each dateRanges as range}
              <option value={range}>{range}</option>
            {/each}
          </select>
        </label>

        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Start date</span>
          <input bind:value={startDate} type="date" class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70" />
        </label>

        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">End date</span>
          <input bind:value={endDate} type="date" class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70" />
        </label>
      </div>

      <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Course / program</span>
          <select bind:value={selectedCourse} class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70">
            {#each courseOptions as course}
              <option value={course}>{course}</option>
            {/each}
          </select>
        </label>

        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Marketing channel</span>
          <select bind:value={selectedChannel} class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70">
            {#each channelOptions as channel}
              <option value={channel}>{channel}</option>
            {/each}
          </select>
        </label>

        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Campaign</span>
          <select bind:value={selectedCampaign} class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70">
            {#each campaignOptions as campaign}
              <option value={campaign}>{campaign}</option>
            {/each}
          </select>
        </label>

        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Lead source</span>
          <select bind:value={selectedLeadSource} class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70">
            {#each leadSourceOptions as source}
              <option value={source}>{source}</option>
            {/each}
          </select>
        </label>

        <label class="block text-sm text-text-secondary">
          <span class="mb-2 block text-xs uppercase tracking-[0.14em] text-text-secondary">Lead status</span>
          <select bind:value={selectedLeadStatus} class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-accent/70">
            {#each leadStatusOptions as status}
              <option value={status}>{status}</option>
            {/each}
          </select>
        </label>
      </div>

      <div class="mt-6 flex flex-wrap items-center gap-3">
        <button type="button" class="rounded-xl border border-accent/50 bg-accent/15 px-4 py-2 text-sm font-medium text-white shadow-[0_0_18px_rgba(164,123,224,0.15)] hover:border-accent" onclick={generateReport}>
          {generationState === 'loading' ? 'Generating...' : 'Generate Report'}
        </button>
        <span class={`text-sm ${generationState === 'error' ? 'text-red-300' : generationState === 'success' ? 'text-emerald-300' : 'text-text-secondary'}`}>
          {generationMessage}
        </span>
      </div>
    </div>

    <div class="space-y-4">
      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">AI Insights</p>
        <h2 class="mt-2 text-xl font-bold text-white">Recommendation summary</h2>
        <div class="mt-4 space-y-3 text-sm text-text-secondary">
          {#each aiInsights as insight}
            <div class="rounded-xl border border-white/10 bg-black/10 p-3">
              <p class="font-semibold text-white">{insight.title}</p>
              <p class="mt-2">{insight.recommendation}</p>
            </div>
          {/each}
        </div>
        <a href="/ai-recommendations" class="mt-4 inline-flex rounded-xl border border-white/10 bg-card px-3 py-2 text-sm font-medium text-white hover:border-accent/40">View AI Recommendations</a>
      </div>

      <div class="dashboard-card p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Export</p>
        <h2 class="mt-2 text-xl font-bold text-white">Report output</h2>
        <div class="mt-4 rounded-xl border border-dashed border-white/10 bg-black/10 p-4 text-sm text-text-secondary">
          {#if exportConfigured}
            <p>Export options are available.</p>
          {:else}
            <p>Export is not configured for this manager reporting workflow.</p>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <div class="dashboard-card p-5 md:p-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Executive summary</p>
        <h2 class="mt-2 text-2xl font-bold text-white">Executive Summary</h2>
      </div>
      <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Demo Data</span>
    </div>

    <div class="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Total Enquiries</p><p class="mt-2 text-2xl font-bold text-white">{kpis.totalEnquiries.toLocaleString()}</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Total Leads</p><p class="mt-2 text-2xl font-bold text-white">{kpis.totalLeads.toLocaleString()}</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Total Applications</p><p class="mt-2 text-2xl font-bold text-white">{kpis.applications.toLocaleString()}</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Total Admissions</p><p class="mt-2 text-2xl font-bold text-white">{kpis.admissions.toLocaleString()}</p></div>
    </div>

    <div class="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Conversion Rate</p><p class="mt-2 text-2xl font-bold text-white">{kpis.conversionRate.toFixed(1)}%</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Marketing Spend</p><p class="mt-2 text-2xl font-bold text-white">₹{(kpis.spend / 100000).toFixed(1)}L</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Cost Per Lead</p><p class="mt-2 text-2xl font-bold text-white">₹{Math.round(kpis.spend / Math.max(kpis.totalLeads, 1)).toLocaleString()}</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Cost Per Admission</p><p class="mt-2 text-2xl font-bold text-white">₹{Math.round(kpis.cpa).toLocaleString()}</p></div>
    </div>

    <div class="mt-5 rounded-2xl border border-white/10 bg-black/10 p-4 text-sm text-text-secondary">
      <p><span class="font-semibold text-white">System-generated insight:</span> Admission conversion is higher at the application stage than at the counselling stage.</p>
      <p class="mt-2">Website and referral channels continue to deliver stronger admission efficiency relative to the broader paid media mix.</p>
    </div>
  </div>

  <div class="dashboard-card p-5 md:p-6">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Funnel</p>
        <h2 class="mt-2 text-2xl font-bold text-white">Admission Funnel</h2>
      </div>
      <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Demo Data</span>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm text-text-secondary">
        <thead>
          <tr class="border-b border-white/10 text-xs uppercase tracking-[0.12em] text-text-secondary">
            <th class="px-2 py-3">Stage</th>
            <th class="px-2 py-3">Count</th>
            <th class="px-2 py-3">Conversion</th>
            <th class="px-2 py-3">Drop-off</th>
            <th class="px-2 py-3">Stage-to-stage</th>
          </tr>
        </thead>
        <tbody>
          {#each funnelData as stage, index}
            <tr class="border-b border-white/5 text-white">
              <td class="px-2 py-3">{stage.name}</td>
              <td class="px-2 py-3">{stage.count.toLocaleString()}</td>
              <td class="px-2 py-3">{stage.conversion}%</td>
              <td class="px-2 py-3">{stage.dropOff}%</td>
              <td class="px-2 py-3">
                {index === 0 ? '—' : `${Math.max(0, Number((stage.conversion / Math.max(funnelData[index - 1].conversion, 1)).toFixed(1)))}%`}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <div class="mt-6 grid gap-3 md:grid-cols-5">
      {#each funnelData as stage}
        <div class="rounded-xl border border-white/10 bg-black/10 p-3">
          <div class="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.12em] text-text-secondary">
            <span>{stage.name}</span>
            <span>{stage.conversion}%</span>
          </div>
          <div class="h-2.5 rounded-full bg-white/5">
            <div class="h-full rounded-full bg-accent" style={`width: ${Math.min(100, stage.conversion * 3)}%`}></div>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-2">
    <div class="dashboard-card p-5 md:p-6">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Channel</p>
          <h2 class="mt-2 text-2xl font-bold text-white">Marketing Channel Performance</h2>
        </div>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Demo Data</span>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full text-left text-sm text-text-secondary">
          <thead>
            <tr class="border-b border-white/10 text-xs uppercase tracking-[0.12em] text-text-secondary">
              <th class="px-2 py-3">Channel</th>
              <th class="px-2 py-3">Spend</th>
              <th class="px-2 py-3">Enquiries</th>
              <th class="px-2 py-3">Leads</th>
              <th class="px-2 py-3">Applications</th>
              <th class="px-2 py-3">Admissions</th>
              <th class="px-2 py-3">Conv.</th>
              <th class="px-2 py-3">CPL</th>
              <th class="px-2 py-3">CPA</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredChannels as channel}
              <tr class="border-b border-white/5 text-white">
                <td class="px-2 py-3">{channel.channel}</td>
                <td class="px-2 py-3">₹{channel.spend.toLocaleString()}</td>
                <td class="px-2 py-3">{Math.round(channel.leads * 1.12).toLocaleString()}</td>
                <td class="px-2 py-3">{channel.leads.toLocaleString()}</td>
                <td class="px-2 py-3">{channel.applications.toLocaleString()}</td>
                <td class="px-2 py-3">{channel.admissions.toLocaleString()}</td>
                <td class="px-2 py-3">{channel.conversion}%</td>
                <td class="px-2 py-3">₹{channel.costPerLead.toLocaleString()}</td>
                <td class="px-2 py-3">₹{channel.costPerAdmission.toLocaleString()}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <div class="dashboard-card p-5 md:p-6">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Campaign</p>
          <h2 class="mt-2 text-2xl font-bold text-white">Campaign Performance</h2>
        </div>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Demo Data</span>
      </div>

      <div class="space-y-4">
        {#each filteredCampaigns as campaign}
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-white">{campaign.name}</p>
                <p class="text-xs text-text-secondary">{campaign.channel}</p>
              </div>
              <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">{campaign.conversion}%</span>
            </div>
            <div class="mt-3 grid gap-2 text-sm text-text-secondary sm:grid-cols-3">
              <p>Spend: <span class="text-white">₹{campaign.spend.toLocaleString()}</span></p>
              <p>Leads: <span class="text-white">{campaign.leads.toLocaleString()}</span></p>
              <p>Admissions: <span class="text-white">{campaign.admissions.toLocaleString()}</span></p>
            </div>
            <div class="mt-3 h-2.5 rounded-full bg-white/5">
              <div class="h-full rounded-full bg-accent" style={`width: ${Math.min(100, campaign.conversion * 5)}%`}></div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
    <div class="dashboard-card p-5 md:p-6">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Budget</p>
          <h2 class="mt-2 text-2xl font-bold text-white">Budget Performance</h2>
        </div>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Actual vs projected</span>
      </div>

      <div class="grid gap-4 md:grid-cols-4">
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Total Budget</p><p class="mt-2 text-xl font-bold text-white">₹{managerBudget.totalBudget.toLocaleString()}</p></div>
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Current Spend</p><p class="mt-2 text-xl font-bold text-white">₹{managerBudget.spent.toLocaleString()}</p></div>
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Remaining</p><p class="mt-2 text-xl font-bold text-white">₹{managerBudget.remaining.toLocaleString()}</p></div>
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Utilization %</p><p class="mt-2 text-xl font-bold text-white">{((managerBudget.spent / managerBudget.totalBudget) * 100).toFixed(1)}%</p></div>
      </div>

      <div class="mt-6 overflow-x-auto">
        <table class="min-w-full text-left text-sm text-text-secondary">
          <thead>
            <tr class="border-b border-white/10 text-xs uppercase tracking-[0.12em] text-text-secondary">
              <th class="px-2 py-3">Channel</th>
              <th class="px-2 py-3">Allocated</th>
              <th class="px-2 py-3">Actual Spend</th>
              <th class="px-2 py-3">Remaining</th>
              <th class="px-2 py-3">Utilization</th>
              <th class="px-2 py-3">Admissions</th>
              <th class="px-2 py-3">CPA</th>
            </tr>
          </thead>
          <tbody>
            {#each budgetTable as item}
              <tr class="border-b border-white/5 text-white">
                <td class="px-2 py-3">{item.channel}</td>
                <td class="px-2 py-3">₹{item.allocated.toLocaleString()}</td>
                <td class="px-2 py-3">₹{item.actualSpend.toLocaleString()}</td>
                <td class="px-2 py-3">₹{item.remaining.toLocaleString()}</td>
                <td class="px-2 py-3">{item.utilization}%</td>
                <td class="px-2 py-3">{item.admissions}</td>
                <td class="px-2 py-3">₹{item.cpa.toLocaleString()}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <div class="dashboard-card p-5 md:p-6">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Prediction</p>
          <h2 class="mt-2 text-2xl font-bold text-white">Admission Prediction Summary</h2>
        </div>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Not Available</span>
      </div>

      <div class="rounded-2xl border border-dashed border-white/10 bg-black/10 p-5 text-sm text-text-secondary">
        <p>Prediction data is not available yet.</p>
      </div>
    </div>
  </div>

  <div class="dashboard-card p-5 md:p-6">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Conversion</p>
        <h2 class="mt-2 text-2xl font-bold text-white">Lead Conversion Performance</h2>
      </div>
      <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Demo Data</span>
    </div>

    <div class="grid gap-4 md:grid-cols-4">
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Total Leads</p><p class="mt-2 text-2xl font-bold text-white">{filteredLeads.length}</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Converted Leads</p><p class="mt-2 text-2xl font-bold text-white">{filteredLeads.filter((lead) => lead.lead_status === 'Admitted' || lead.lead_status === 'Application').length}</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Non-converted</p><p class="mt-2 text-2xl font-bold text-white">{filteredLeads.filter((lead) => lead.lead_status === 'Not Converted' || lead.lead_status === 'New').length}</p></div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4"><p class="text-xs uppercase tracking-[0.14em] text-text-secondary">Conversion Rate</p><p class="mt-2 text-2xl font-bold text-white">{filteredLeads.length ? (((filteredLeads.filter((lead) => lead.lead_status === 'Admitted' || lead.lead_status === 'Application').length) / filteredLeads.length) * 100).toFixed(1) : '0.0'}%</p></div>
    </div>

    <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {#each leadStatusDistribution as item}
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
          <div class="flex items-center justify-between gap-3">
            <p class="text-white">{item.status}</p>
            <span class="text-accent">{item.share}%</span>
          </div>
          <div class="mt-3 h-2.5 rounded-full bg-white/5">
            <div class="h-full rounded-full bg-accent" style={`width: ${Math.min(100, Number(item.share) * 2)}%`}></div>
          </div>
          <p class="mt-3 text-sm text-text-secondary">{item.count} leads</p>
        </div>
      {/each}
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-2">
    <div class="dashboard-card p-5 md:p-6">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Simulation</p>
          <h2 class="mt-2 text-2xl font-bold text-white">Projected scenario</h2>
        </div>
        <span class="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-text-secondary">Not Actual</span>
      </div>

      <div class="space-y-3 text-sm text-text-secondary">
        <p>Current admissions: <span class="text-white font-semibold">{whatIfScenario.current.admissions}</span></p>
        <p>Projected admissions: <span class="text-white font-semibold">{whatIfScenario.simulated.admissions}</span></p>
        <p>Projected budget: <span class="text-white font-semibold">₹{(whatIfScenario.simulated.admissions * 3500).toLocaleString()}</span></p>
      </div>
    </div>

    <div class="dashboard-card p-5 md:p-6">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-accent font-semibold">Status</p>
          <h2 class="mt-2 text-2xl font-bold text-white">Report state</h2>
        </div>
      </div>
      <div class="rounded-2xl border border-white/10 bg-black/10 p-4 text-sm text-text-secondary">
        <p>{generationMessage}</p>
      </div>
    </div>
  </div>
</div>
