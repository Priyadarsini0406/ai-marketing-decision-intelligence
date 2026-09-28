<script lang="ts">
    import AnalyticsChart from '$lib/components/AnalyticsChart.svelte';
  import { asPercent, bandClasses, workspaceOverview, type PredictionPreview } from '$lib/ml-api';
  import { onMount } from 'svelte';

  let rows = $state<PredictionPreview[]>([]);
  let error = $state('');
  let busy = $state(true);
  let search = $state('');

  const visible = $derived(rows.filter((row) => String(row.customer_id ?? '').toLowerCase().includes(search.toLowerCase())));
  const summary = $derived([
    { label: 'Total Leads', value: rows.length },
    { label: 'High Probability', value: rows.filter((row) => row.score === 'High').length },
    { label: 'Medium Probability', value: rows.filter((row) => row.score === 'Medium').length },
    { label: 'Low Probability', value: rows.filter((row) => row.score === 'Low').length }
  ]);

  onMount(async () => {
    busy = true;
    try { rows = (await workspaceOverview()).prediction_preview; } catch (e) { error = (e as Error).message; }
    finally { busy = false; }
  });
</script>

<svelte:head>
  <title>Admission Prediction | DecisionIntel</title>
</svelte:head>

<div class="space-y-6">  <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Manager intelligence</p>
      <h1 class="mt-2 text-3xl font-bold text-white">Admission Prediction</h1>
    </div>
    <div class="rounded-xl border border-white/10 bg-card px-3 py-2 text-sm text-text-secondary">
      {busy ? 'Loading model output…' : 'XGBoost out-of-fold scores · stored in ml_predictions'}
    </div>
  </div>
{#if error}<p role="alert" class="text-sm text-red-300">{error}</p>{/if}
<AnalyticsChart title="Admission probability by lead" categories={visible.map(item => String(item.customer_id ?? item.lead_id))} series={[{ name: 'Predicted probability', values: visible.map(item => Number(item.probability) * 100) }]} description="Out-of-fold conversion probability from the trained XGBoost model, in percent." unit="%" />


  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    {#each summary as item}
      <div class="rounded-2xl border border-white/10 bg-card p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-text-secondary">{item.label}</p>
        <p class="mt-3 text-3xl font-bold text-white">{item.value}</p>
      </div>
    {/each}
  </div>

  <div class="rounded-2xl border border-white/10 bg-card p-5">
    <div class="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">Prediction Overview</h2>
      </div>
      <div class="flex flex-wrap gap-2 text-sm text-text-secondary">
        <input bind:value={search} class="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white placeholder:text-text-secondary" placeholder="Search lead" aria-label="Search lead" />
        <span class="self-center">{visible.length} of {rows.length} shown</span>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
          <tr>
            <th class="px-4 py-3">Lead</th>
            <th class="px-4 py-3">Source</th>
            <th class="px-4 py-3">Probability</th>
            <th class="px-4 py-3">Prediction</th>
            <th class="px-4 py-3">Segment</th>
            <th class="px-4 py-3">Observed Outcome</th>
            <th class="px-4 py-3">Action</th>
          </tr>
        </thead>
        <tbody>
          {#each visible as lead}
            <tr class="border-b border-white/5 text-white">
              <td class="px-4 py-3">{lead.customer_id ?? lead.lead_id}</td>
              <td class="px-4 py-3">{lead.source ?? '—'}</td>
              <td class="px-4 py-3 font-semibold text-accent">{asPercent(lead.probability)}</td>
              <td class="px-4 py-3">
                <span class={`rounded-full px-2 py-1 text-xs font-semibold ${bandClasses[lead.score] ?? ''}`}>
                  {lead.score}
                </span>
              </td>
              <td class="px-4 py-3">{lead.segment ?? '—'}</td>
              <td class="px-4 py-3">{lead.observed_conversion === null ? 'Unknown' : lead.observed_conversion ? 'Converted' : 'Not converted'}</td>
              <td class="px-4 py-3">
                <a href={`/student-leads/${lead.lead_id}`} class="text-accent hover:underline">View Prediction</a>
              </td>
            </tr>
          {:else}
            <tr><td colspan="7" class="px-4 py-6 text-text-secondary">{busy ? 'Loading model output…' : 'No stored predictions. Run backend/train_model.py to import the dataset.'}</td></tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
