<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    type Enquiry = { id: string; course_interested: string; status: string; created_at: number; updated_at: number; remarks?: string | null };
    let enquiry = $state<Enquiry | null>(null), loading = $state(true), error = $state('');
    const steps = ['Submitted', 'Under Review', 'Counselling', 'Application', 'Admitted'];
    const activeIndex = $derived(Math.max(0, steps.indexOf(enquiry?.status ?? 'Submitted')));
    onMount(async () => { try { const items: Enquiry[] = await api('/student/enquiries'); enquiry = items[0] ?? null; } catch (e) { error = (e as Error).message; } finally { loading = false; } });
    const date = (value: number) => new Date(value * 1000).toLocaleDateString();
</script>
<div class="max-w-3xl space-y-6"><div><h1 class="text-3xl font-bold text-white">Enquiry Status</h1><p class="text-text-secondary mt-2">Track the latest admission enquiry saved to your account.</p></div>
    {#if error}<p role="alert" class="text-red-400">{error}</p>{/if}
    {#if enquiry}<div class="bg-card border border-white/10 rounded-2xl p-6 grid sm:grid-cols-2 gap-5"><div><p class="meta">Enquiry ID</p><p class="text-white">{enquiry.id.slice(0, 8)}</p></div><div><p class="meta">Course / Program</p><p class="text-white">{enquiry.course_interested}</p></div><div><p class="meta">Submitted Date</p><p class="text-white">{date(enquiry.created_at)}</p></div><div><p class="meta">Current Status</p><p class="text-accent">{enquiry.status}</p></div></div>
        <div class="bg-card border border-white/10 rounded-2xl p-6"><h2 class="text-white font-bold">Admission Timeline</h2><div class="mt-6 space-y-5">{#each steps as step,i}<div class="flex gap-4"><span class:complete={i<activeIndex} class:current={i===activeIndex} class="timeline-dot">{i<activeIndex?'✓':i+1}</span><div><p class="text-white font-medium">{step}</p><p class="text-sm text-text-secondary mt-1">{i<activeIndex?'Completed':i===activeIndex?'Current status':'Available after review.'}</p></div></div>{/each}</div></div>
        {#if enquiry.remarks}<div class="bg-card border border-white/10 rounded-2xl p-6"><p class="meta">Your note</p><p class="text-text-secondary mt-2">{enquiry.remarks}</p></div>{/if}
    {:else if !loading}<div class="bg-card border border-white/10 rounded-2xl p-6"><p class="text-text-secondary">No enquiry has been submitted yet.</p><a class="text-accent inline-block mt-4" href="/student/enquiries/new">Start a new enquiry</a></div>{/if}
</div>
<style>.meta{font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:var(--di-muted);margin-bottom:.3rem}.timeline-dot{width:2rem;height:2rem;flex:none;border-radius:999px;display:grid;place-items:center;background:rgba(91,33,182,.08);color:var(--di-muted)}.timeline-dot.complete{background:rgba(91,33,182,.35);color:var(--di-text)}.timeline-dot.current{border:1px solid #6D28D9;color:var(--di-accent-ink)}</style>
