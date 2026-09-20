<script lang="ts">
    import { managerLeads, managerProfile } from '$lib/manager-demo';
    import DataTable from '$lib/DataTable.svelte';
    import { reportCsv, type ReportRow } from '$lib/manager-reports';
    let { view }: { view: 'students' | 'managers' } = $props();
    let search = $state(''), status = $state('All statuses');
    const managers = [...new Set([managerProfile.name, ...managerLeads.map(item => item.assigned_to)])].map(name => {
        const leads = managerLeads.filter(item => item.assigned_to === name);
        return { name, email: name === managerProfile.name ? managerProfile.email : 'Not provided', institution: name === managerProfile.name ? managerProfile.institution : 'Not provided', assigned_students: leads.length, programs: leads.map(item => item.course_interested).join(', ') || 'No assignments', students: leads.map(item => item.student_name).join(', ') || 'No assignments' };
    });
    const students = $derived(managerLeads.filter(item => (status === 'All statuses' || item.lead_status === status) && [item.student_name, item.email, item.course_interested, item.assigned_to, item.location].some(value => value.toLowerCase().includes(search.toLowerCase()))));
    const visibleManagers = $derived(managers.filter(item => Object.values(item).some(value => String(value).toLowerCase().includes(search.toLowerCase()))));
    const rows: ReportRow[] = $derived(view === 'students' ? students.map(item => ({ Student: item.student_name, Email: item.email, Phone: item.phone, Program: item.course_interested, Intake: item.preferred_intake, Location: item.location, Qualification: item.qualification, 'Academic score (%)': item.academic_score, Status: item.lead_status, Potential: item.prediction, 'Prediction (%)': item.probability, Manager: item.assigned_to, Source: item.lead_source, 'Enquiry date': item.enquiry_date })) : visibleManagers.map(item => ({ Manager: item.name, Email: item.email, Institution: item.institution, 'Assigned students': item.assigned_students, Programs: item.programs, Students: item.students })));
    const cards = $derived(view === 'students' ? [
        { label: 'Student records', value: managerLeads.length }, { label: 'High potential', value: managerLeads.filter(item => item.prediction === 'High').length }, { label: 'Applications', value: managerLeads.filter(item => item.lead_status === 'Application').length }, { label: 'Admitted', value: managerLeads.filter(item => item.lead_status === 'Admitted').length }
    ] : [{ label: 'Managers listed', value: managers.length }, { label: 'Assigned students', value: managerLeads.length }, { label: 'Managers with assignments', value: managers.filter(item => item.assigned_students).length }, { label: 'Programs covered', value: new Set(managerLeads.map(item => item.course_interested)).size }]);
    function download() {
        const url = URL.createObjectURL(new Blob([reportCsv(rows)], { type: 'text/csv;charset=utf-8' }));
        const link = document.createElement('a'); link.href = url; link.download = `admin-${view}.csv`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
</script>

<svelte:head><title>{view === 'students' ? 'Students' : 'Managers'} | Administration</title></svelte:head>
<div class="directory">
    <header><div><p class="eyebrow">USER MANAGEMENT</p><h1>{view === 'students' ? 'Students' : 'Managers'}</h1><p>{view === 'students' ? 'Student enquiries, program interests, and admission progress.' : 'Manager profiles, student assignments, and program coverage.'}</p></div><a class="button" href="/admin/users">Manage user accounts</a></header>
    <div class="stats">{#each cards as item}<section class="panel"><span>{item.label}</span><strong>{item.value}</strong></section>{/each}</div>
    <section class="panel"><div class="toolbar"><label>Search {view}<input type="search" bind:value={search} placeholder="Search name, contact, or program" /></label>{#if view === 'students'}<div class="field"><label for="student-status">Admission status</label><select id="student-status" bind:value={status}><option>All statuses</option>{#each [...new Set(managerLeads.map(item => item.lead_status))] as value}<option>{value}</option>{/each}</select></div>{/if}<button disabled={!rows.length} onclick={download}>Download CSV</button></div>
        <p class="note">Directory records from the supplied admission data. Sign-in accounts are managed separately under User Accounts.</p>
        <p class="note">Showing {rows.length} of {view === 'students' ? managerLeads.length : managers.length} records</p>
        <DataTable {rows} empty="No records match these filters." />
    </section>
</div>

<style>
    .directory{max-width:1300px}header,.toolbar{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap;align-items:center}h1{font-size:30px;font-weight:700;margin:8px 0}p{font-size:14px;color:#aaa0b7;line-height:1.7}.eyebrow{font-size:10px;color:#b99bd9;letter-spacing:.18em}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:24px 0}.panel{min-width:0;padding:22px;border:1px solid #ffffff16;border-radius:16px;background:var(--color-card,#1c1724)}.stats span{font-size:12px;color:#aaa0b7}.stats strong{display:block;font-size:28px;margin-top:10px}.toolbar label,.field{display:grid;gap:8px;font-size:12px;color:#b9adc6}.toolbar{align-items:end}.toolbar>label{flex:1;min-width:180px}input,select{min-width:0;width:100%;background:#110d19;border:1px solid #ffffff24;border-radius:8px;padding:11px 13px;color:white}button,.button{padding:10px 14px;background:#a47be0;color:#160f20;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer}button:disabled{opacity:.4;cursor:default}.note{font-size:11px;margin:16px 0}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}@media(max-width:700px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.panel{padding:16px}}
</style>
