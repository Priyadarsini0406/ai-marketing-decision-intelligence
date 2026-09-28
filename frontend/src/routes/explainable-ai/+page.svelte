<script lang="ts">
    import AnalyticsChart from '$lib/components/AnalyticsChart.svelte';
  import {
    asPercent,
    factorLabel,
    factorValue,
    listLeads,
    predictLead,
    storedPrediction,
    type LeadOption,
    type LeadPrediction,
    type ShapFactor
  } from '$lib/ml-api';
  import { onMount } from 'svelte';

  let leads = $state<LeadOption[]>([]);
  let selectedId = $state('');
  let result = $state<LeadPrediction | null>(null);
  let topPositive = $state<ShapFactor[]>([]);
  let topNegative = $state<ShapFactor[]>([]);
  let baseValue = $state<number | null>(null);
  let stored = $state<{ method: string | null; base: number | null } | null>(null);
  let error = $state('');
  let busy = $state(false);
  let loaded = $state(false);

  const factors = $derived([...topPositive, ...topNegative]);
  // Bar widths are scaled against this lead's own largest |SHAP| value, so the
  // chart is honest regardless of how large this particular score is.
  const peak = $derived(Math.max(...factors.map((item) => Math.abs(item.shap_value)), 0.000001));

  async function explain(leadId: string) {
    if (!leadId) return;
    busy = true;
    error = '';
    try {
      const [live, archived] = await Promise.allSettled([
        predictLead(leadId, true),
        storedPrediction(leadId)
      ]);
      if (live.status === 'rejected') throw live.reason;
      result = live.value;
      topPositive = live.value.top_positive ?? [];
      topNegative = live.value.top_negative ?? [];
      baseValue = live.value.base_value ?? null;
      // The batch import stored an out-of-fold explanation for the same model.
      // Showing it alongside proves the live and stored paths agree.
      stored = archived.status === 'fulfilled'
        ? { method: archived.value.explanation_method, base: archived.value.base_value }
        : null;
    } catch (e) { error = (e as Error).message; }
    finally { busy = false; }
  }

  onMount(async () => {
    busy = true;
    try {
      leads = await listLeads(100);
      if (leads.length) { selectedId = leads[0].id; await explain(selectedId); }
    } catch (e) { error = (e as Error).message; }
    finally { busy = false; loaded = true; }
  });
</script>

<svelte:head>
  <title>Explainable AI | DecisionIntel</title>
</svelte:head>

<div class="space-y-6">  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">AI insights</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Explainable AI</h1>
    <p class="mt-2 text-text-secondary">Understand the factors influencing admission conversion predictions.</p>
  </div>
{#if error}<p role="alert" class="text-sm text-red-300">{error}</p>{/if}
<AnalyticsChart title="SHAP feature contributions" categories={factors.map(factorLabel)} series={[{ name: 'Contribution', values: factors.map(item => item.shap_value) }]} description={result ? `TreeSHAP values from ${result.explanation_method ?? 'shap.TreeExplainer'} for lead ${result.customer_id ?? 'selected'}. Positive values raise the model's log-odds of conversion; negative values lower them.` : 'Select a lead to compute its SHAP explanation.'} unit="Contribution" />


  <div class="rounded-2xl border border-white/10 bg-card p-5">
    <label for="student-lead-select" class="block text-sm font-medium text-text-secondary">Student lead</label>
    <select id="student-lead-select" bind:value={selectedId} onchange={() => explain(selectedId)} disabled={busy || !leads.length} class="mt-2 w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-white md:max-w-xs">
      {#each leads as lead}
        <option value={lead.id}>{lead.customer_id ?? lead.id}</option>
      {/each}
    </select>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.1fr_1.4fr]">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">Prediction Summary</h2>
      <div class="mt-4 space-y-3 text-sm text-text-secondary">
        <p><span class="text-white">Lead:</span> {result?.customer_id ?? '—'}</p>
        <p><span class="text-white">Probability:</span> <span class="font-bold text-accent">{asPercent(result?.probability)}</span></p>
        <p><span class="text-white">Category:</span> {result ? `${result.score} Potential` : '—'}</p>
        <p><span class="text-white">Segment:</span> {result?.segment ?? '—'}</p>
        <p><span class="text-white">Feature source:</span> {result?.feature_source ?? '—'}</p>
        {#if result}<p class="text-xs">{result.note}</p>{/if}
      </div>
    </div>

    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">SHAP Feature Importance</h2>
      <div class="mt-5 space-y-4">
        {#each factors as feature}
          <div>
            <div class="mb-1 flex items-center justify-between gap-3 text-xs uppercase tracking-[0.15em] text-text-secondary">
              <span>{factorLabel(feature)}</span>
              <span class={feature.shap_value >= 0 ? 'text-green-300' : 'text-red-300'}>{feature.shap_value > 0 ? '+' : ''}{feature.shap_value.toFixed(3)}</span>
            </div>
            <div class="h-2.5 overflow-hidden rounded-full bg-white/5">
              <div class={`h-full rounded-full ${feature.shap_value >= 0 ? 'bg-green-400' : 'bg-red-400'}`} style={`width: ${Math.min(100, Math.abs(feature.shap_value) / peak * 100)}%`} ></div>
            </div>
            <p class="mt-1 text-xs text-text-secondary">Value: {factorValue(feature)}</p>
          </div>
        {:else}
          <p class="text-sm text-text-secondary">{busy ? 'Computing SHAP values…' : 'No explanation available.'}</p>
        {/each}
      </div>
    </div>
  </div>

  <div class="rounded-2xl border border-white/10 bg-card p-5">
    <div class="mb-4 flex items-center justify-between gap-3">
      <h2 class="text-xl font-bold text-white">Explanation Summary</h2>
      <span class="rounded-full border border-accent/30 bg-accent/10 px-2 py-1 text-xs font-medium text-accent">{result?.explanation_method ?? 'shap.TreeExplainer'}</span>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <div class="rounded-xl border border-white/10 bg-black/10 p-4">
        <p class="mb-2 text-sm font-semibold uppercase tracking-[0.15em] text-green-300">Positive Factors</p>
        <ul class="space-y-2 text-sm text-text-secondary">
          {#each topPositive as item}
            <li>• {factorLabel(item)} {item.shap_value > 0 ? '+' : ''}{item.shap_value.toFixed(3)}</li>
          {:else}
            <li>• No feature raised the log-odds.</li>
          {/each}
        </ul>
      </div>
      <div class="rounded-xl border border-white/10 bg-black/10 p-4">
        <p class="mb-2 text-sm font-semibold uppercase tracking-[0.15em] text-red-300">Negative Factors</p>
        <ul class="space-y-2 text-sm text-text-secondary">
          {#each topNegative as item}
            <li>• {factorLabel(item)} {item.shap_value.toFixed(3)}</li>
          {:else}
            <li>• No feature lowered the log-odds.</li>
          {/each}
        </ul>
      </div>
    </div>

    <div class="mt-4 rounded-xl border border-accent/20 bg-accent/5 p-4 text-sm text-text-secondary">
      <span class="font-semibold text-white">Overall Explanation:</span>
      {#if result && baseValue !== null}
        The model's base log-odds of conversion is {baseValue.toFixed(4)}. Summing every SHAP contribution reproduces the predicted log-odds for this lead.
        {topPositive.length} feature{topPositive.length === 1 ? '' : 's'} raised the score and {topNegative.length} lowered it. SHAP values explain model behaviour, not causation.
        {#if stored?.method}
          The stored out-of-fold explanation for this lead was produced by {stored.method} with base log-odds {stored.base?.toFixed(4) ?? 'unavailable'}.
        {/if}
      {:else}
        Select a lead to see its SHAP explanation.
      {/if}
    </div>
  </div>
  {#if loaded && !leads.length}<p class="text-sm text-text-secondary">No leads available. Import the campaign dataset first.</p>{/if}
</div>
