<script lang="ts">
    import { onMount } from 'svelte';
    import { page } from '$app/state';
    import { api } from '$lib/api';
    import { asPercent, bandClasses, storedPrediction, type ShapFactor, type StoredPrediction } from '$lib/ml-api';

    let lead = $state<any>(null), error = $state('');
    let prediction = $state<StoredPrediction | null>(null), predictionState = $state<'loading' | 'ready' | 'none' | 'error'>('loading'), predictionError = $state('');
    const stages = ['Enquiry', 'Contacted', 'Counselling', 'Application', 'Admission'];

    onMount(async () => {
        try { lead = await api(`/leads/${page.params.id}`); }
        catch (e) { error = (e as Error).message; return; }
        try { prediction = await storedPrediction(lead.id); predictionState = 'ready'; }
        catch (e) {
            // The endpoint answers 404 "No prediction stored for this lead" when none exists.
            const message = (e as Error).message;
            if (/no prediction stored/i.test(message)) predictionState = 'none';
            else { predictionState = 'error'; predictionError = message; }
        }
    });

    // The imported dataset uses "Select" for a field the enquirer left unanswered.
    const UNSPECIFIED = new Set(['', 'select', 'nan', 'none', 'null']);
    const isUnspecified = (value: unknown) => value === null || value === undefined || UNSPECIFIED.has(String(value).trim().toLowerCase());
    const shown = (value: unknown, fallback = 'Not provided') => isUnspecified(value) ? fallback : String(value);

    const leadTitle = $derived(lead ? (isUnspecified(lead.student_name) ? `Lead ${lead.customer_id ?? lead.student_id ?? lead.id}` : lead.student_name) : '');

    /** The journey stage the stored record supports, never guessed beyond it:
     *  an exact stage name set by staff, a recorded conversion or admission,
     *  a staff note (the lead was contacted), otherwise the initial enquiry. */
    const currentStage = $derived.by(() => {
        if (!lead) return null;
        const status = isUnspecified(lead.lead_status) ? '' : String(lead.lead_status).trim();
        const exact = stages.find(stage => stage.toLowerCase() === status.toLowerCase());
        if (exact) return exact;
        if (lead.conversion === true || lead.admission_status === true) return 'Admission';
        if (status && status.toLowerCase() !== 'new') return 'Contacted';
        return 'Enquiry';
    });

    /** One-hot factors name a category; when it differs from the lead's value the factor is about NOT having it. */
    function describeFactor(factor: ShapFactor): string {
        if (factor.category === null) return `${factor.feature}: ${shown(factor.value, 'not specified')}`;
        if (isUnspecified(factor.category)) return isUnspecified(factor.value) ? `${factor.feature} not specified` : `${factor.feature} is ${factor.value}`;
        if (String(factor.category) === String(factor.value)) return `${factor.feature} is ${factor.category}`;
        return `${factor.feature} is not ${factor.category} (${isUnspecified(factor.value) ? 'not specified' : String(factor.value)})`;
    }
    const topFactors = $derived(prediction ? [...prediction.top_positive.slice(0, 2), ...prediction.top_negative.slice(0, 2)] : []);
</script>

{#if error}<p class="text-red-300">{error}</p>{:else if lead}<div class="max-w-4xl space-y-6"><a href="/student-leads" class="text-sm text-accent">← Student Leads</a><div class="flex justify-between gap-4"><div class="min-w-0"><h1 class="lead-title text-3xl font-bold text-white">{leadTitle}</h1><p class="text-text-secondary mt-2">Lead details and operational admission journey.</p></div>{#if !isUnspecified(lead.lead_status)}<span class="h-fit px-3 py-2 rounded-full bg-accent/15 text-accent text-sm">{lead.lead_status}</span>{/if}</div><div class="grid md:grid-cols-2 gap-5"><section class="card"><h2>Student Information</h2><p>Email: {shown(lead.email)}</p><p>Location: {shown(lead.location)}</p></section><section class="card"><h2>Academic Information</h2><p>{shown(lead.qualification)}</p><p>Score: {lead.academic_score ?? '—'}</p></section><section class="card"><h2>Admission Interest</h2><p>Course: {shown(lead.course_interested, '—')}</p><p>Program: {shown(lead.program, '—')}</p></section><section class="card"><h2>AI Intelligence</h2>{#if predictionState === 'loading'}<p class="text-text-secondary">Loading prediction…</p>{:else if predictionState === 'ready' && prediction}<div class="flex items-center gap-3 flex-wrap"><span class="prob">{asPercent(prediction.conversion_probability)}</span><span class="px-2.5 py-1 rounded-full text-xs font-semibold {bandClasses[prediction.lead_score] ?? ''}">{prediction.lead_score}</span></div><p>Estimated conversion probability{prediction.segment ? ` · Segment: ${prediction.segment}` : ''}</p>{#if topFactors.length}<ul class="factors" aria-label="Top SHAP factors">{#each topFactors as factor}<li class:up={factor.shap_value > 0} class:down={factor.shap_value <= 0}><span aria-hidden="true">{factor.shap_value > 0 ? '▲' : '▼'}</span>{describeFactor(factor)}</li>{/each}</ul>{/if}<p class="note">Stored model prediction. It estimates lead conversion, not academic eligibility or an admission decision.</p>{:else if predictionState === 'error'}<p class="text-text-secondary">Prediction unavailable: {predictionError}</p>{:else}<p class="text-text-secondary">No prediction has been generated yet.</p>{/if}<div class="mt-4 flex gap-3"><a href="/admission-prediction" class="text-accent text-sm">View Prediction →</a><a href="/explainable-ai" class="text-accent text-sm">Explain Prediction →</a></div></section></div><section class="card"><h2>Lead Journey</h2><div class="flex flex-wrap gap-3 mt-4">{#each stages as stage}<span class:current={stage === currentStage} aria-current={stage === currentStage ? 'step' : undefined} class="stage">{stage}</span>{/each}</div></section></div>{:else}<p class="text-text-secondary">Loading lead…</p>{/if}<style>.card{background:var(--color-card);border:1px solid rgba(91, 33, 182, .14);padding:1.5rem;border-radius:1rem}.card h2{color:var(--di-text);font-weight:bold;margin-bottom:.75rem}.card p{font-size:.875rem;color:var(--di-muted);margin:.35rem 0}.stage{padding:.5rem .75rem;border-radius:.6rem;background:rgba(91, 33, 182, .08);font-size:.8rem;color:var(--di-muted)}.stage.current{background:rgba(91, 33, 182,.15);color:var(--di-accent-ink);border:1px solid rgba(91, 33, 182,.3)}.lead-title{overflow-wrap:anywhere}.prob{font-size:1.6rem;font-weight:700;color:var(--di-text);font-variant-numeric:tabular-nums}.factors{list-style:none;padding:0;margin:.6rem 0 0;display:flex;flex-direction:column;gap:.3rem}.factors li{display:flex;gap:.45rem;font-size:.8rem;color:var(--di-muted)}.factors li.up span{color:var(--di-green-ink)}.factors li.down span{color:var(--di-red-ink)}.card p.note{font-size:.72rem;margin-top:.6rem}</style>
