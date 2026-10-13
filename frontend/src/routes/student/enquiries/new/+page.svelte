<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type User } from '$lib/api';

    let user = $state<User | null>(null);
    let submitted = $state(false), busy = $state(false), error = $state('');
    let form = $state({
        phone: '', qualification: '', institution: '', academic_score: '', course_interested: '',
        preferred_intake: '', preferred_mode: 'On campus', location: '', interest_area: '',
        contact_method: 'Email', remarks: ''
    });

    onMount(async () => {
        try {
            const current: User = await api('/auth/me');
            user = current;
            const profile = current.profile ?? {};
            form = { ...form,
                phone: String(profile.mobile ?? ''), qualification: String(profile.qualification ?? ''),
                institution: String(profile.institution ?? ''), course_interested: String(profile.course_interested ?? ''),
                location: String(profile.city ?? '')
            };
        } catch { window.location.assign('/login'); }
    });

    async function submit(event: SubmitEvent) {
        event.preventDefault();
        busy = true; error = '';
        try {
            await api('/student/enquiries', { method: 'POST', body: JSON.stringify({
                ...form, academic_score: form.academic_score ? Number(form.academic_score) : null
            }) });
            submitted = true;
        } catch (e) { error = (e as Error).message; }
        finally { busy = false; }
    }
</script>

<svelte:head><title>New Enquiry | DecisionIntel</title></svelte:head>
{#if submitted}
    <div class="max-w-2xl bg-card border border-accent/30 rounded-2xl p-8 text-center">
        <div class="w-14 h-14 rounded-full bg-accent/20 grid place-items-center text-accent mx-auto text-2xl">✓</div>
        <h1 class="text-2xl font-bold text-white mt-5">Enquiry Submitted</h1>
        <p class="text-text-secondary mt-3">Your enquiry is saved. The admission team can now review it.</p>
        <div class="flex justify-center gap-3 mt-7"><a href="/student/enquiries" class="px-4 py-3 rounded-xl bg-cta text-white font-bold text-sm">View Enquiries</a><a href="/student/dashboard" class="px-4 py-3 rounded-xl bg-secondary text-white text-sm">Dashboard</a></div>
    </div>
{:else}
    <div class="max-w-4xl">
        <h1 class="text-3xl font-bold text-white">Start a New Enquiry</h1>
        <p class="text-text-secondary mt-2 mb-6">Tell us about your admission interests and requirements.</p>
        {#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}
        <form onsubmit={submit} class="bg-card border border-white/10 rounded-2xl p-6 space-y-7">
            <section><h2>Personal Information</h2><div class="form-grid"><label>Full Name<input value={user?.name ?? ''} disabled /></label><label>Email<input value={user?.email ?? ''} type="email" disabled /></label><label>Phone Number<input bind:value={form.phone} required /></label></div></section>
            <section><h2>Academic Information</h2><div class="form-grid"><label>Highest Qualification<input bind:value={form.qualification} required /></label><label>Institution<input bind:value={form.institution} /></label><label>Academic Score / Percentage<input bind:value={form.academic_score} type="number" min="0" max="100" step="any" /></label></div></section>
            <section><h2>Admission Interest</h2><div class="form-grid"><label>Interested Course<input bind:value={form.course_interested} required /></label><label>Preferred Intake<input bind:value={form.preferred_intake} placeholder="e.g. July 2027" /></label><label>Preferred Mode<select bind:value={form.preferred_mode}><option>On campus</option><option>Online</option><option>Hybrid</option></select></label><label>Location Preference<input bind:value={form.location} /></label></div></section>
            <section><h2>Enquiry Details</h2><div class="form-grid"><label>Areas of Interest<input bind:value={form.interest_area} /></label><label>Preferred Contact Method<select bind:value={form.contact_method}><option>Email</option><option>Phone</option><option>WhatsApp</option></select></label></div><label class="block mt-4">Questions / Requirements<textarea bind:value={form.remarks}></textarea></label></section>
            <button disabled={busy} class="px-6 py-3 rounded-xl bg-cta text-white font-bold">{busy ? 'Submitting…' : 'Submit Enquiry'}</button>
        </form>
    </div>
{/if}
<style>
    h2{font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;color:var(--di-accent-ink);font-weight:bold;margin-bottom:1rem}
    .form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem}
    label{display:flex;flex-direction:column;gap:.45rem;font-size:.75rem;color:var(--di-muted)}
    input,select,textarea{background:var(--di-surface);border:1px solid rgba(91,33,182,.14);border-radius:.6rem;padding:.75rem .85rem;color:var(--di-text);font-size:.875rem}
    textarea{min-height:90px}
</style>
