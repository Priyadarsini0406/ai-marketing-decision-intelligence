<script lang="ts">
  import { managerBudget } from '$lib/manager-demo';

  const spentPercent = (managerBudget.spent / managerBudget.totalBudget) * 100;
  const remainingPercent = (managerBudget.remaining / managerBudget.totalBudget) * 100;
</script>

<svelte:head>
  <title>Budget Optimization | DecisionIntel</title>
</svelte:head>

<div class="space-y-6 pb-10">
  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Budget intelligence</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Budget Optimization</h1>
    <p class="mt-2 max-w-2xl text-text-secondary">Rebalance channel investment based on performance, efficiency, and projected admissions value.</p>
  </div>

  <div class="grid gap-4 md:grid-cols-3">
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Budget</p>
      <p class="mt-3 text-3xl font-bold text-white">₹{managerBudget.totalBudget.toLocaleString()}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Spent</p>
      <p class="mt-3 text-3xl font-bold text-white">₹{managerBudget.spent.toLocaleString()}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Remaining</p>
      <p class="mt-3 text-3xl font-bold text-white">₹{managerBudget.remaining.toLocaleString()}</p>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
    <div class="dashboard-card p-5">
      <h2 class="text-xl font-bold text-white">Allocation overview</h2>
      <div class="mt-5 space-y-4">
        {#each managerBudget.allocations as allocation}
          <div>
            <div class="mb-2 flex items-center justify-between text-sm">
              <span class="text-white">{allocation.channel}</span>
              <span class="text-text-secondary">₹{allocation.currentAmount.toLocaleString()} ({allocation.percent}%)</span>
            </div>
            <div class="h-2.5 rounded-full bg-white/5">
              <div class="h-full rounded-full bg-accent" style={`width: ${allocation.percent}%`}></div>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="dashboard-card p-5">
      <h2 class="text-xl font-bold text-white">Recommendation</h2>
      <div class="mt-4 space-y-3 text-sm text-text-secondary">
        <p>Increase spend for <span class="text-white font-semibold">Website</span> and <span class="text-white font-semibold">Referral</span> channels.</p>
        <p>Reduce inefficient spend in campaigns with weak conversion efficiency.</p>
        <p>Projected uplift: <span class="text-accent font-semibold">+9.2%</span> admissions in the next cycle.</p>
      </div>
      <div class="mt-5 h-2.5 rounded-full bg-white/5">
        <div class="h-full rounded-full bg-accent" style={`width: ${spentPercent}%`}></div>
      </div>
    </div>
  </div>
</div>
