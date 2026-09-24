<script lang="ts">
  import { managerChannels } from '$lib/manager-demo';

  const totalSpend = managerChannels.reduce((sum, channel) => sum + channel.spend, 0);
  const totalLeads = managerChannels.reduce((sum, channel) => sum + channel.leads, 0);
  const totalAdmissions = managerChannels.reduce((sum, channel) => sum + channel.admissions, 0);
  const averageCPL = managerChannels.reduce((sum, channel) => sum + channel.costPerLead, 0) / managerChannels.length;
  const averageCPA = managerChannels.reduce((sum, channel) => sum + channel.costPerAdmission, 0) / managerChannels.length;
</script>

<svelte:head>
  <title>Channel Attribution | DecisionIntel</title>
</svelte:head>

<div class="space-y-6 pb-10">
  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Acquisition intelligence</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Channel Attribution</h1>
    <p class="mt-2 max-w-2xl text-text-secondary">Track which acquisition channels are driving the highest-value leads and the strongest admissions performance.</p>
  </div>

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Budget Spent</p>
      <p class="mt-3 text-3xl font-bold text-white">₹{(totalSpend / 100000).toFixed(1)}L</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Lead Volume</p>
      <p class="mt-3 text-3xl font-bold text-white">{totalLeads}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Admissions</p>
      <p class="mt-3 text-3xl font-bold text-white">{totalAdmissions}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Avg CPL / CPA</p>
      <p class="mt-3 text-xl font-bold text-white">₹{Math.round(averageCPL)} / ₹{Math.round(averageCPA)}</p>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
    <div class="dashboard-card p-5">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-xl font-bold text-white">Channel breakdown</h2>
        <span class="text-sm text-accent">Best performing: Website</span>
      </div>

      <div class="space-y-4">
        {#each managerChannels as channel}
          <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
            <div class="mb-2 flex items-center justify-between gap-3">
              <div>
                <p class="font-semibold text-white">{channel.channel}</p>
                <p class="text-xs text-text-secondary">Spend ₹{channel.spend.toLocaleString()}</p>
              </div>
              <div class="text-right">
                <p class="text-accent font-semibold">{channel.conversion}%</p>
                <p class="text-xs text-text-secondary">conversion</p>
              </div>
            </div>
            <div class="h-2.5 rounded-full bg-white/5">
              <div class="h-full rounded-full bg-accent" style={`width: ${Math.min(100, channel.conversion * 3.2)}%`}></div>
            </div>
            <div class="mt-3 grid gap-2 text-sm text-text-secondary sm:grid-cols-3">
              <p>Leads: <span class="text-white">{channel.leads}</span></p>
              <p>Applications: <span class="text-white">{channel.applications}</span></p>
              <p>Admissions: <span class="text-white">{channel.admissions}</span></p>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="space-y-4">
      <div class="dashboard-card p-5">
        <h2 class="text-xl font-bold text-white">Attribution notes</h2>
        <ul class="mt-4 space-y-3 text-sm text-text-secondary">
          <li class="rounded-xl border border-white/10 bg-black/10 p-3">Website traffic produces the strongest conversion quality at 25.6%.</li>
          <li class="rounded-xl border border-white/10 bg-black/10 p-3">Referral and email channels deliver high admission efficiency with lower CPA.</li>
          <li class="rounded-xl border border-white/10 bg-black/10 p-3">Google Ads still contributes the largest volume of leads; this should be balanced with retargeting spend.</li>
        </ul>
      </div>

      <div class="dashboard-card p-5">
        <h2 class="text-xl font-bold text-white">Optimization signal</h2>
        <div class="mt-4 space-y-3 text-sm text-text-secondary">
          <p>Top quality source: <span class="text-white font-semibold">Website</span></p>
          <p>Largest lead volume: <span class="text-white font-semibold">Google Ads</span></p>
          <p>Lowest cost per admission: <span class="text-white font-semibold">Referral</span></p>
        </div>
      </div>
    </div>
  </div>
</div>
