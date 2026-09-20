<script lang="ts">
    import AnalyticsChart from '$lib/components/AnalyticsChart.svelte';
  import { managerLeads, shapDemo } from '$lib/manager-demo';

  let selectedId = $state(managerLeads[0]?.id ?? '');
  const selectedLead = $derived(managerLeads.find((lead) => lead.id === selectedId) ?? managerLeads[0]);
</script>

<svelte:head>
  <title>Explainable AI | DecisionIntel</title>
</svelte:head>

<div class="space-y-6">  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">AI insights</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Explainable AI</h1>
    <p class="mt-2 text-text-secondary">Understand the factors influencing admission conversion predictions.</p>
  </div>
<AnalyticsChart title="SHAP feature contributions" categories={[...shapDemo.positive,...shapDemo.negative].map(item => item.name)} series={[{ name: 'Contribution', values: [...shapDemo.positive,...shapDemo.negative].map(item => item.value) }]} description="Supplied demo explanation. Positive values support the prediction; negative values reduce it." unit="Contribution" />


  <div class="rounded-2xl border border-white/10 bg-card p-5">
    <label for="student-lead-select" class="block text-sm font-medium text-text-secondary">Student lead</label>
    <select id="student-lead-select" bind:value={selectedId} class="mt-2 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-white md:max-w-xs">
      {#each managerLeads as lead}
        <option value={lead.id}>{lead.student_name}</option>
      {/each}
    </select>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.1fr_1.4fr]">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">Prediction Summary</h2>
      <div class="mt-4 space-y-3 text-sm text-text-secondary">
        <p><span class="text-white">Student:</span> {selectedLead.student_name}</p>
        <p><span class="text-white">Course:</span> {selectedLead.course_interested}</p>
        <p><span class="text-white">Probability:</span> <span class="font-bold text-accent">{selectedLead.probability}%</span></p>
        <p><span class="text-white">Category:</span> {selectedLead.prediction} Potential</p>
      </div>
    </div>

    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">SHAP Feature Importance</h2>
      <div class="mt-5 space-y-4">
        {#each [...shapDemo.positive, ...shapDemo.negative] as feature}
          <div>
            <div class="mb-1 flex items-center justify-between text-xs uppercase tracking-[0.15em] text-text-secondary">
              <span>{feature.name}</span>
              <span class={feature.value >= 0 ? 'text-green-300' : 'text-red-300'}>{feature.value > 0 ? '+' : ''}{feature.value.toFixed(2)}</span>
            </div>
            <div class="h-2.5 overflow-hidden rounded-full bg-white/5">
              <div class={`h-full rounded-full ${feature.value >= 0 ? 'bg-green-400' : 'bg-red-400'}`} style={`width: ${Math.min(100, Math.abs(feature.value) * 180)}%`} ></div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <div class="rounded-2xl border border-white/10 bg-card p-5">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">Explanation Summary</h2>
      <span class="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs font-medium text-amber-200">Demo Explanation</span>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <div class="rounded-xl border border-white/10 bg-black/10 p-4">
        <p class="mb-2 text-sm font-semibold uppercase tracking-[0.15em] text-green-300">Positive Factors</p>
        <ul class="space-y-2 text-sm text-text-secondary">
          {#each shapDemo.positive as item}
            <li>• {item.name} +{item.value.toFixed(2)}</li>
          {/each}
        </ul>
      </div>
      <div class="rounded-xl border border-white/10 bg-black/10 p-4">
        <p class="mb-2 text-sm font-semibold uppercase tracking-[0.15em] text-red-300">Negative Factors</p>
        <ul class="space-y-2 text-sm text-text-secondary">
          {#each shapDemo.negative as item}
            <li>• {item.name} {item.value.toFixed(2)}</li>
          {/each}
        </ul>
      </div>
    </div>

    <div class="mt-4 rounded-xl border border-accent/20 bg-accent/5 p-4 text-sm text-text-secondary">
      <span class="font-semibold text-white">Overall Explanation:</span>
      {shapDemo.summary}
    </div>
  </div>
</div>
