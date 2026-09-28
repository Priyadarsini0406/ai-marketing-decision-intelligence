<script lang="ts">
    import AnalyticsChart from '$lib/components/AnalyticsChart.svelte';
  import { asPercent, listSegments, type SegmentSummary } from '$lib/ml-api';
  import { onMount } from 'svelte';

  let segments = $state<SegmentSummary[]>([]);
  let error = $state('');
  let busy = $state(true);

  const totalLeads = $derived(segments.reduce((sum, item) => sum + item.leads, 0));
  // average_probability is nullable, so rank on a numeric fallback rather than
  // letting a null slip into the comparison.
  const rank = (item: SegmentSummary) => item.average_probability ?? -1;
  const topSegment = $derived(segments.reduce<SegmentSummary | null>(
    (best, item) => (best === null || rank(item) > rank(best) ? item : best), null));
  const weakestSegment = $derived(segments.reduce<SegmentSummary | null>(
    (worst, item) => (worst === null || rank(item) < rank(worst) ? item : worst), null));
  // Bars are scaled against the largest real segment, not a hardcoded divisor.
  const peak = $derived(Math.max(...segments.map((item) => item.leads), 1));

  onMount(async () => {
    busy = true;
    try { segments = await listSegments(); } catch (e) { error = (e as Error).message; }
    finally { busy = false; }
  });
</script>

<svelte:head>
  <title>Student Segmentation | DecisionIntel</title>
</svelte:head>

<div class="space-y-6">  <div>
    <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Lead intelligence</p>
    <h1 class="mt-2 text-3xl font-bold text-white">Student Segmentation</h1>
  </div>
{#if error}<p role="alert" class="text-sm text-red-300">{error}</p>{/if}
<div class="grid gap-5 xl:grid-cols-2"><AnalyticsChart title="Student segment distribution" kind="donut" categories={segments.map(item => item.segment)} series={[{ name: 'Leads', values: segments.map(item => item.leads) }]} unit="Leads" /><AnalyticsChart title="Segment probabilities and conversion" categories={segments.map(item => item.segment)} series={[{ name: 'Average probability', values: segments.map(item => (item.average_probability ?? 0) * 100) }, { name: 'Conversion rate', values: segments.map(item => (item.conversion_rate ?? 0) * 100) }]} description="Model probability and observed conversion rate per segment." unit="%" /></div>


  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Total Leads</p>
      <p class="mt-3 text-3xl font-bold text-white">{totalLeads.toLocaleString()}</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Active Segments</p>
      <p class="mt-3 text-3xl font-bold text-white">{segments.length}</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Highest Intent</p>
      <p class="mt-3 text-3xl font-bold text-white">{topSegment?.leads.toLocaleString() ?? '—'}</p>
      <p class="mt-1 text-xs text-text-secondary">{topSegment?.segment ?? 'No segments yet'}</p>
    </div>
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <p class="text-xs uppercase tracking-[0.16em] text-text-secondary">Lowest Intent</p>
      <p class="mt-3 text-3xl font-bold text-white">{weakestSegment?.leads.toLocaleString() ?? '—'}</p>
      <p class="mt-1 text-xs text-text-secondary">{weakestSegment?.segment ?? 'No segments yet'}</p>
    </div>
  </div>

  <div class="grid gap-6 xl:grid-cols-[1.1fr_1.3fr]">
    <div class="rounded-2xl border border-white/10 bg-card p-5">
      <h2 class="text-xl font-bold text-white">Segment Distribution</h2>
      <div class="mt-6 space-y-4">
        {#each segments as segment}
          <div>
            <div class="mb-2 flex justify-between text-sm text-text-secondary">
              <span>{segment.segment}</span>
              <span class="text-white">{segment.leads.toLocaleString()}</span>
            </div>
            <div class="h-2.5 rounded-full bg-white/5">
              <div class="h-full rounded-full bg-accent" style={`width: ${Math.min(100, segment.leads / peak * 100)}%`}></div>
            </div>
          </div>
        {:else}
          <p class="text-sm text-text-secondary">{busy ? 'Loading segmentation…' : 'No segments stored. Run backend/train_model.py to import the dataset.'}</p>
        {/each}
      </div>
    </div>

    <div class="space-y-4">
      {#each segments as segment}
        <div class="rounded-2xl border border-white/10 bg-card p-5">
          <div class="flex items-center justify-between gap-3">
            <h3 class="text-lg font-bold text-white">{segment.segment}</h3>
            <a href={`/student-leads?search=${encodeURIComponent(segment.segment)}`} class="rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-text-secondary">View Students</a>
          </div>
          <div class="mt-4 grid gap-3 sm:grid-cols-3 text-sm">
            <div>
              <p class="text-text-secondary">Lead Count</p>
              <p class="mt-1 text-xl font-bold text-white">{segment.leads.toLocaleString()}</p>
            </div>
            <div>
              <p class="text-text-secondary">Avg Probability</p>
              <p class="mt-1 text-xl font-bold text-white">{asPercent(segment.average_probability)}</p>
            </div>
            <div>
              <p class="text-text-secondary">Conversion Rate</p>
              <p class="mt-1 text-xl font-bold text-white">{asPercent(segment.conversion_rate)}</p>
            </div>
          </div>
          <p class="mt-4 text-sm text-text-secondary">
            {segment.high_score_leads.toLocaleString()} High-score leads · average {segment.average_visits ?? 0} site visits,
            {segment.average_pages_per_visit ?? 0} pages per visit and {Math.round(segment.average_time_on_site ?? 0)}s on site.
            {segment.conversions.toLocaleString()} of {segment.known_outcomes.toLocaleString()} leads with a known outcome converted.
          </p>
        </div>
      {/each}
    </div>
  </div>
</div>
