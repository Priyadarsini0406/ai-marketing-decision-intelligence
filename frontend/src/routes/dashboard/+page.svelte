<script lang="ts">
  import { dashboardStats, managerCampaigns, managerFunnelStages, managerLeads, managerRecommendations, managerChannels } from '$lib/manager-demo';

  const topLeads = managerLeads.slice(0, 4);
</script>

<svelte:head>
  <title>Manager Dashboard | DecisionIntel</title>
</svelte:head>

<div class="space-y-6 pb-10">
  <div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Manager dashboard</p>
      <h1 class="mt-2 text-3xl font-bold text-white">Welcome back, Adminstrator</h1>
      <p class="mt-2 max-w-2xl text-text-secondary">Track your admission performance and make data-driven marketing decisions.</p>
    </div>
    <div class="flex flex-wrap gap-3">
      <a href="/student-leads/new" class="rounded-xl border border-white/10 bg-card px-4 py-2 text-sm font-medium text-white">+ Add Student Lead</a>
      <a href="/budget-optimization" class="rounded-xl bg-accent px-4 py-2 text-sm font-bold text-white">Optimize Budget</a>
    </div>
  </div>


  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
    {#each dashboardStats as stat}
      <div class="rounded-2xl border border-white/10 bg-card p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-text-secondary">{stat.label}</p>
        <div class="mt-3 flex items-end justify-between">
          <span class="text-3xl font-bold text-white">{stat.value}</span>
          <span class="text-sm font-semibold text-green-300">{stat.delta}</span>
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
        <h2 class="text-xl font-bold text-white">High-Potential Student Leads</h2>
        <a href="/student-leads" class="text-sm font-medium text-accent">View all</a>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full text-left text-sm">
          <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
            <tr>
              <th class="px-3 py-2">Student</th>
              <th class="px-3 py-2">Course</th>
              <th class="px-3 py-2">Probability</th>
              <th class="px-3 py-2">Prediction</th>
              <th class="px-3 py-2">Source</th>
              <th class="px-3 py-2">Stage</th>
              <th class="px-3 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {#each topLeads as lead}
              <tr class="border-b border-white/5 text-white">
                <td class="px-3 py-3">{lead.student_name}</td>
                <td class="px-3 py-3">{lead.course_interested}</td>
                <td class="px-3 py-3 text-accent">{lead.probability}%</td>
                <td class="px-3 py-3">{lead.prediction}</td>
                <td class="px-3 py-3">{lead.source}</td>
                <td class="px-3 py-3">{lead.lead_status}</td>
                <td class="px-3 py-3"><a href={`/student-leads/${lead.id}`} class="text-accent">View</a></td>
              </tr>
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
