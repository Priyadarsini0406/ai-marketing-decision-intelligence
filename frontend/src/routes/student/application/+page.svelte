<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    type Enquiry = { id: string; course_interested: string; preferred_intake?: string | null; status: string; created_at: number; updated_at: number };
    const steps = ['Submitted', 'Under Review', 'Counselling', 'Application', 'Admitted'];
    let enquiry = $state<Enquiry | null>(null), error = $state(''), loading = $state(true);
    let activeIndex = $derived(Math.max(0, steps.indexOf(enquiry?.status ?? 'Submitted')));
    const date = (value: number) => new Date(value * 1000).toLocaleDateString();
    onMount(async () => { try { const rows: Enquiry[] = await api('/student/enquiries'); enquiry = rows[0] ?? null; } catch (e) { error = (e as Error).message; } finally { loading = false; } });
</script>
<div class="max-w-3xl space-y-6"><div><h1 class="text-3xl font-bold text-white">Application Status</h1><p class="text-text-secondary mt-2">Review the latest status and next step for your enquiry.</p></div>
    {#if error}<p role="alert" class="text-red-400">{error}</p>{/if}
    {#if enquiry}<section class="bg-card border border-white/10 rounded-2xl p-6"><div class="flex justify-between gap-4"><div><p class="text-xs uppercase tracking-wider text-accent">{enquiry.course_interested}{enquiry.preferred_intake ? ` · ${enquiry.preferred_intake}` : ''}</p><h2 class="text-xl text-white font-bold mt-2">{enquiry.status}</h2></div><span class="text-sm text-accent bg-accent/15 px-3 py-2 h-fit rounded-full">Current stage</span></div><div class="mt-8 space-y-1">{#each steps as step,i}<div class="flex items-center gap-4"><span class:complete={i<activeIndex} class:active={i===activeIndex} class="progress-dot">{i<activeIndex?'✓':i+1}</span><p class:active-text={i===activeIndex} class="py-3 text-sm text-text-secondary">{step}</p></div>{/each}</div></section>
        <section class="bg-card border border-white/10 rounded-2xl p-6 grid sm:grid-cols-3 gap-5"><div><p class="meta">Submitted</p><p class="text-white mt-1">{date(enquiry.created_at)}</p></div><div><p class="meta">Last Updated</p><p class="text-white mt-1">{date(enquiry.updated_at)}</p></div><div><p class="meta">Next Action</p><p class="text-accent mt-1">{enquiry.status === 'Admitted' ? 'Review admission details' : enquiry.status === 'Not Converted' ? 'Contact admissions for assistance' : 'Await an update from admissions'}</p></div></section>
    {:else if !loading}<section class="bg-card border border-white/10 rounded-2xl p-6"><p class="text-text-secondary">Submit an enquiry to start tracking an application.</p><a href="/student/enquiries/new" class="text-accent inline-block mt-4">Start an enquiry</a></section>{/if}
</div>
<style>.progress-dot{width:2rem;height:2rem;border-radius:999px;display:grid;place-items:center;background:rgba(91,33,182,.08);color:var(--di-muted)}.progress-dot.complete{background:#6D28D9;color:#fff}.progress-dot.active{border:1px solid #6D28D9;color:var(--di-accent-ink)}.active-text{color:var(--di-text);font-weight:600}.meta{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--di-muted)}</style>
