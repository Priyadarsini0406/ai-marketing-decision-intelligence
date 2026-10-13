<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';

    type Lead = {
        id: string; enquiry_id?: string | null; student_name: string; email?: string; phone?: string;
        course_interested?: string; qualification?: string; enquiry_source?: string;
        enquiry_date?: string | number | null; lead_status?: string;
    };
    let leads = $state<Lead[]>([]);
    let error = $state(''), query = $state(''), adding = $state(false), submitting = $state(false), loading = $state(true);
    let filtered = $derived(leads.filter((lead) =>
        `${lead.student_name} ${lead.email ?? ''} ${lead.course_interested ?? ''} ${lead.enquiry_source ?? ''}`
            .toLowerCase().includes(query.toLowerCase())
    ));

    async function load() {
        loading = true;
        error = '';
        try { leads = await api('/workspace/students'); }
        catch (e) { error = (e as Error).message; }
        finally { loading = false; }
    }
    onMount(() => { void load(); });

    async function add(event: SubmitEvent) {
        event.preventDefault();
        submitting = true;
        const form = new FormData(event.currentTarget as HTMLFormElement);
        try {
            const lead = await api('/leads/', { method: 'POST', body: JSON.stringify(Object.fromEntries(form)) });
            leads = [{ ...lead, lead_status: lead.lead_status ?? 'New' }, ...leads];
            adding = false;
        } catch (e) { error = (e as Error).message; }
        finally { submitting = false; }
    }

    async function updateStatus(lead: Lead, status: string) {
        if (!lead.enquiry_id) return;
        try {
            await api(`/workspace/student-enquiries/${lead.enquiry_id}`, { method: 'PUT', body: JSON.stringify({ status }) });
            leads = leads.map((item) => item.enquiry_id === lead.enquiry_id ? { ...item, lead_status: status } : item);
        } catch (e) { error = (e as Error).message; }
    }
</script>

<div class="space-y-6">
    <div class="flex flex-col sm:flex-row justify-between gap-4">
        <div><h1 class="text-3xl font-bold text-white">Student Leads</h1><p class="text-text-secondary mt-2">Registered students and their saved admission enquiries.</p></div>
        <button onclick={() => adding = !adding} class="px-5 py-3 rounded-xl bg-cta text-white font-bold text-sm">+ Add Student Lead</button>
    </div>
    {#if error}<p role="alert" class="p-3 rounded-xl border border-red-400/20 bg-red-400/10 text-red-300 text-sm">{error}</p>{/if}
    {#if adding}
        <form onsubmit={add} class="bg-card border border-accent/25 rounded-2xl p-6 space-y-5">
            <h2 class="text-white font-bold">Add Student Lead</h2>
            <div class="grid sm:grid-cols-3 gap-4">
                <label>Student Name<input name="student_name" required /></label><label>Email<input name="email" type="email" /></label><label>Phone<input name="phone" /></label>
                <label>Location<input name="location" /></label><label>Qualification<input name="qualification" /></label><label>Percentage / CGPA<input name="academic_score" type="number" step=".01" /></label>
                <label>Interested Course<input name="course_interested" /></label><label>Preferred Program<input name="program" /></label>
                <label>Source<select name="enquiry_source"><option>Walk-in</option><option>Phone</option><option>Offline</option><option>Referral</option><option>Other</option></select></label>
            </div>
            <label>Remarks<textarea name="remarks"></textarea></label>
            <button disabled={submitting} class="px-5 py-3 rounded-xl bg-cta text-white font-bold text-sm">{submitting ? 'Creating…' : 'Create Lead'}</button>
        </form>
    {/if}
    <div class="flex flex-wrap gap-3"><input bind:value={query} placeholder="Search student, course or source" class="bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white text-sm w-full max-w-md"/><button class="px-4 py-2 bg-secondary rounded-lg" disabled={loading} onclick={load}>Refresh</button></div>
    <div class="bg-card border border-white/10 rounded-2xl overflow-x-auto">
        <table class="min-w-[900px] w-full text-sm"><thead class="text-left text-xs text-text-secondary uppercase border-b border-white/10"><tr><th class="p-5">Student</th><th>Email</th><th>Course</th><th>Qualification</th><th>Source</th><th>Status</th></tr></thead>
            <tbody>{#each filtered as lead}
                <tr class="border-b border-white/5 text-text-secondary"><td class="p-5 text-white font-medium">{lead.student_name}</td><td>{lead.email ?? '—'}</td><td>{lead.course_interested ?? '—'}</td><td>{lead.qualification ?? '—'}</td><td>{lead.enquiry_source ?? '—'}</td>
                    <td>{#if lead.enquiry_id}<select value={lead.lead_status ?? 'Submitted'} onchange={(event) => updateStatus(lead, (event.currentTarget as HTMLSelectElement).value)}><option>Submitted</option><option>Under Review</option><option>Counselling</option><option>Application</option><option>Admitted</option><option>Not Converted</option></select>{:else}{lead.lead_status ?? 'New'}{/if}</td>
                </tr>
            {:else}<tr><td colspan="6" class="p-5">{loading ? 'Loading students…' : 'No student records yet.'}</td></tr>{/each}</tbody>
        </table>
    </div>
</div>
<style>
    label{display:flex;flex-direction:column;gap:.4rem;color:var(--di-muted);font-size:.75rem}
    input,select,textarea{background:var(--di-surface);border:1px solid rgba(91,33,182,.14);border-radius:.6rem;padding:.7rem;color:var(--di-text)}
    textarea{min-height:75px}
</style>
