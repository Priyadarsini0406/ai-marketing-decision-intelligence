<script lang="ts">
  import { managerSegments } from '$lib/manager-demo';
</script>

<svelte:head>
  <title>Student Segmentation | DecisionIntel</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Lead intelligence</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Student Segmentation</h1>
  </div>

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Leads</p>
      <p class="mt-3 text-3xl font-bold text-white">896</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Active Segments</p>
      <p class="mt-3 text-3xl font-bold text-white">3</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">High Intent</p>
      <p class="mt-3 text-3xl font-bold text-white">286</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Medium Intent</p>
      <p class="mt-3 text-3xl font-bold text-white">412</p>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.1fr_1.3fr]">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">Segment Distribution</h2>
      <div class="mt-6 space-y-4">
        {#each managerSegments as segment}
          <div>
            <div class="mb-2 flex justify-between text-sm text-text-secondary">
              <span>{segment.title}</span>
              <span class="text-white">{segment.count}</span>
            </div>
            <div class="h-2.5 rounded-full bg-white/5">
              <div class="h-full rounded-full bg-accent" style={`width: ${Math.min(100, segment.count / 4.5)}%`}></div>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="space-y-4">
      {#each managerSegments as segment}
        <div class="rounded-2xl border border-white/10 bg-card p-5">
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-lg font-bold text-white">{segment.title}</h3>
            <button class="rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-text-secondary">View Students</button>
          </div>
          <div class="mt-4 grid gap-3 sm:grid-cols-3 text-sm">
            <div>
              <p class="text-text-secondary">Student Count</p>
              <p class="mt-1 text-xl font-bold text-white">{segment.count}</p>
            </div>
            <div>
              <p class="text-text-secondary">Avg Probability</p>
              <p class="mt-1 text-xl font-bold text-white">{segment.avgProbability}%</p>
            </div>
            <div>
              <p class="text-text-secondary">Conversion Rate</p>
              <p class="mt-1 text-xl font-bold text-white">{segment.conversionRate}%</p>
            </div>
          </div>
          <p class="mt-4 text-sm text-text-secondary">{segment.characteristics}</p>
        </div>
      {/each}
    </div>
  </div>
</div>
