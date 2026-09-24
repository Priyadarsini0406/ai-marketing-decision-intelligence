<script lang="ts">
  import { managerFunnelStages } from '$lib/manager-demo';

  const totalLeads = managerFunnelStages.reduce((sum, stage) => sum + stage.count, 0);
  const finalStage = managerFunnelStages[managerFunnelStages.length - 1];
</script>

<svelte:head>
  <title>Admission Funnel | DecisionIntel</title>
</svelte:head>

<div class="space-y-6 pb-10">
  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Lead intelligence</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Admission Funnel</h1>
    <p class="mt-2 max-w-2xl text-text-secondary">Monitor how interest converts from enquiry through application to final admission across the latest cycle.</p>
  </div>

  <div class="grid gap-4 md:grid-cols-3">
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Enquiries</p>
      <p class="mt-3 text-3xl font-bold text-white">{totalLeads}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Applications</p>
      <p class="mt-3 text-3xl font-bold text-white">{managerFunnelStages[3].count}</p>
    </div>
    <div class="dashboard-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Admissions</p>
      <p class="mt-3 text-3xl font-bold text-white">{finalStage.count}</p>
    </div>
  </div>

  <div class="dashboard-card p-5">
    <div class="mb-5 flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">Funnel performance</h2>
      <span class="text-sm text-accent">Overall conversion: {managerFunnelStages[managerFunnelStages.length - 1].conversion}%</span>
    </div>

    <div class="grid gap-4 md:grid-cols-5">
      {#each managerFunnelStages as stage}
        <div class="rounded-2xl border border-white/10 bg-black/10 p-4">
          <div class="mb-3 flex items-center justify-between">
            <span class="text-xs uppercase tracking-[0.16em] text-text-secondary">{stage.name}</span>
            <span class="text-xs text-accent">{stage.conversion}%</span>
          </div>
          <div class="mb-2 text-3xl font-bold text-white">{stage.count}</div>
          <div class="text-sm text-text-secondary">Drop-off: {stage.dropOff}%</div>
          <div class="mt-4 h-2.5 rounded-full bg-white/5">
            <div class="h-full rounded-full bg-accent" style={`width: ${Math.min(100, stage.conversion * 1.8)}%`}></div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>
