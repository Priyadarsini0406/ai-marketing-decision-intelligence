<script lang="ts">
    import AnalyticsChart from '$lib/components/AnalyticsChart.svelte';
  import { managerLeads } from '$lib/manager-demo';

  const summary = [
    { label: 'Total Leads', value: managerLeads.length },
    { label: 'High Probability', value: managerLeads.filter((lead) => lead.prediction === 'High').length },
    { label: 'Medium Probability', value: managerLeads.filter((lead) => lead.prediction === 'Medium').length },
    { label: 'Low Probability', value: managerLeads.filter((lead) => lead.prediction === 'Low').length }
  ];
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
      Demo / mock prediction data only
    </div>
  </div>
<AnalyticsChart title="Admission probability by student" categories={managerLeads.map(item => item.student_name)} series={[{ name: 'Predicted probability', values: managerLeads.map(item => item.probability) }]} unit="%" />


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
        <input class="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white placeholder:text-text-secondary" placeholder="Search Student" />
        <select class="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white">
          <option>Course</option>
        </select>
        <select class="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-white">
          <option>Prediction</option>
        </select>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead class="border-b border-white/10 text-xs uppercase tracking-[0.15em] text-text-secondary">
          <tr>
            <th class="px-4 py-3">Student</th>
            <th class="px-4 py-3">Course</th>
            <th class="px-4 py-3">Probability</th>
            <th class="px-4 py-3">Prediction</th>
            <th class="px-4 py-3">Lead Status</th>
            <th class="px-4 py-3">Source</th>
            <th class="px-4 py-3">Prediction Date</th>
            <th class="px-4 py-3">Action</th>
          </tr>
        </thead>
        <tbody>
          {#each managerLeads as lead}
            <tr class="border-b border-white/5 text-white">
              <td class="px-4 py-3">{lead.student_name}</td>
              <td class="px-4 py-3">{lead.course_interested}</td>
              <td class="px-4 py-3 font-semibold text-accent">{lead.probability}%</td>
              <td class="px-4 py-3">
                <span class={`rounded-full px-2 py-1 text-xs font-semibold ${lead.prediction === 'High' ? 'bg-green-500/15 text-green-300' : lead.prediction === 'Medium' ? 'bg-yellow-500/15 text-yellow-300' : 'bg-red-500/15 text-red-300'}`}>
                  {lead.prediction}
                </span>
              </td>
              <td class="px-4 py-3">{lead.lead_status}</td>
              <td class="px-4 py-3">{lead.source}</td>
              <td class="px-4 py-3">{lead.enquiry_date}</td>
              <td class="px-4 py-3">
                <a href={`/admission-prediction/${lead.id}`} class="text-accent hover:underline">View Prediction</a>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>
