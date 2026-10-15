<script lang="ts">
    import AnalyticsChart from '$lib/components/AnalyticsChart.svelte';
  import { asPercent, bandClasses, listStudentIntelligence, workspaceOverview, type PredictionPreview, type StudentIntelligence } from '$lib/ml-api';
  import { onMount } from 'svelte';
  import { startLiveSync } from '$lib/live-sync';

  let rows = $state<PredictionPreview[]>([]);
  let students = $state<StudentIntelligence[]>([]);
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

  async function load(showBusy = false) {
    if (showBusy) busy = true;
    try {
      const [overviewResult, studentsResult] = await Promise.allSettled([workspaceOverview(), listStudentIntelligence()]);
      if (overviewResult.status === 'fulfilled') rows = overviewResult.value.prediction_preview;
      else error = (overviewResult.reason as Error).message;
      if (studentsResult.status === 'fulfilled') students = studentsResult.value;
      else error ||= (studentsResult.reason as Error).message;
    }
    finally { if (showBusy) busy = false; }
  }
  onMount(() => { void load(true); return startLiveSync(() => load()); });
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
      {busy ? 'Loading model output…' : 'Stored XGBoost scores'}
    </div>
  </div>
{#if error}<p role="alert" class="text-sm text-red-300">{error}</p>{/if}
<AnalyticsChart title="Admission probability by lead" categories={visible.map(item => String(item.student_name ?? item.customer_id ?? item.lead_id))} series={[{ name: 'Predicted probability', values: visible.map(item => Number(item.probability) * 100) }]} description="Stored XGBoost conversion probabilities. Account scores use synthetic website activity inputs; imported rows use out-of-fold scores." unit="%" />


  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    {#each summary as item}
      <div class="rounded-2xl border border-white/10 bg-card p-5">
        <p class="text-xs uppercase tracking-[0.18em] text-text-secondary">{item.label}</p>
        <p class="mt-3 text-3xl font-bold text-white">{item.value}</p>
      </div>
    {/each}
  </div>

  <section class="rounded-2xl border border-white/10 bg-card p-5">
    <div class="mb-4">
      <h2 class="text-xl font-bold text-white">Student Accounts</h2>
      <p class="mt-1 text-sm text-text-secondary">Registered student details and their linked model predictions, when available.</p>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary"><tr><th class="px-3 py-3">Student</th><th class="px-3 py-3">Course</th><th class="px-3 py-3">Qualification</th><th class="px-3 py-3">Academic score</th><th class="px-3 py-3">Account status</th><th class="px-3 py-3">Model prediction</th></tr></thead>
        <tbody>
          {#each students as student}
            <tr class="border-b border-white/5 text-white"><td class="px-3 py-3">{student.name}</td><td class="px-3 py-3">{student.course_interested ?? '—'}</td><td class="px-3 py-3">{student.qualification ?? '—'}</td><td class="px-3 py-3">{student.academic_score ?? '—'}</td><td class="px-3 py-3">{student.status}</td><td class="px-3 py-3">{student.probability !== null ? `${asPercent(student.probability)} · ${student.score}` : 'Not scored — no linked lead data'}</td></tr>
          {:else}<tr><td colspan="6" class="px-3 py-5 text-text-secondary">{busy ? 'Loading student accounts…' : 'No student accounts found.'}</td></tr>{/each}
        </tbody>
      </table>
    </div>
  </section>

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
              <td class="px-4 py-3">{lead.student_name ?? lead.customer_id ?? lead.lead_id}</td>
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
