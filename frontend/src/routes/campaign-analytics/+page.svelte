<script lang="ts">
  import { managerCampaigns } from '$lib/manager-demo';

  const totalSpend = managerCampaigns.reduce((sum, campaign) => sum + campaign.spend, 0);
  const totalLeads = managerCampaigns.reduce((sum, campaign) => sum + campaign.leads, 0);
  const totalAdmissions = managerCampaigns.reduce((sum, campaign) => sum + campaign.admissions, 0);
  const avgConversion = managerCampaigns.reduce((sum, campaign) => sum + campaign.conversion, 0) / managerCampaigns.length;
</script>

<svelte:head>
  <title>Campaign Analytics | DecisionIntel</title>
</svelte:head>

<div class="space-y-6 pb-10">
  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Admission analytics</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Campaign Analytics</h1>
    <p class="mt-2 max-w-2xl text-text-secondary">Compare spend efficiency, lead quality, and conversion outcomes across active admission campaigns.</p>
  </div>

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Campaign Spend</p>
      <p class="mt-3 text-3xl font-bold text-white">₹{(totalSpend / 100000).toFixed(1)}L</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Qualified Leads</p>
      <p class="mt-3 text-3xl font-bold text-white">{totalLeads}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Admissions</p>
      <p class="mt-3 text-3xl font-bold text-white">{totalAdmissions}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Avg Conversion</p>
      <p class="mt-3 text-3xl font-bold text-white">{avgConversion.toFixed(1)}%</p>
    </div>
  </div>

  <div class="dashboard-card p-5">
    <div class="mb-5 flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">Campaign performance</h2>
      <span class="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs font-medium text-accent">Live cohorts</span>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
          <tr>
            <th class="px-3 py-2">Campaign</th>
            <th class="px-3 py-2">Channel</th>
            <th class="px-3 py-2">Spend</th>
            <th class="px-3 py-2">Leads</th>
            <th class="px-3 py-2">Admissions</th>
            <th class="px-3 py-2">Conversion</th>
          </tr>
        </thead>
        <tbody>
          {#each managerCampaigns as campaign}
            <tr class="border-b border-white/5 text-white">
              <td class="px-3 py-3 font-medium">{campaign.name}</td>
              <td class="px-3 py-3 text-text-secondary">{campaign.channel}</td>
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
