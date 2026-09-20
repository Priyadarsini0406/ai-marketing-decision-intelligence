<script lang="ts">
    import { courses, institutions } from '$lib/admin-education';
    import { reportCsv } from '$lib/manager-reports';
    import DataTable from '$lib/DataTable.svelte';
    let { view }: { view: 'courses' | 'institutions' } = $props();
    let search = $state('');
    const records = $derived(view === 'courses' ? courses : institutions);
    const rows = $derived(records.filter(row => Object.values(row).some(value => String(value ?? '').toLowerCase().includes(search.toLowerCase()))));
    function download() {
        const url = URL.createObjectURL(new Blob([reportCsv(rows)], { type: 'text/csv;charset=utf-8' }));
        const link = document.createElement('a'); link.href = url; link.download = `admin-${view}.csv`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
</script>
<svelte:head><title>{view === 'courses' ? 'Courses / Programs' : 'Institutions'} | Administration</title></svelte:head>
<div class="education">
    <p class="eyebrow">EDUCATION MANAGEMENT</p><h1>{view === 'courses' ? 'Courses / Programs' : 'Institutions'}</h1><p>{view === 'courses' ? 'Explore the expanded program catalog and admission outcomes. New programs have no enquiries yet; intakes and managers can be assigned later.' : 'Institution details and professional contacts from the supplied profile.'}</p>
    <div class="summary"><strong>{records.length}</strong><span>{view === 'courses' ? 'Programs in the course catalog' : 'Institution in the supplied data'}</span><a href="/admin/data-import">Open Data Import →</a></div>
    {#if view === 'institutions'}{#each institutions as item}<section class="institution"><div class="initial" aria-hidden="true">DI</div><div><h2>{item.institution}</h2><p>{item.contact_name} · {item.contact_role}</p><a href={`mailto:${item.email}`}>{item.email}</a><p>{item.phone}</p></div></section>{/each}{/if}
    <section class="panel"><div class="toolbar"><label>Search {view === 'courses' ? 'programs' : 'institutions'}<input type="search" bind:value={search} placeholder="Search records" /></label><button disabled={!rows.length} onclick={download}>Download CSV</button></div><p class="count">Showing {rows.length} of {records.length} records</p><DataTable {rows} empty="No records match your search." /></section>
</div>
<style>
    .education{max-width:1300px}h1{font-size:30px;font-weight:700;margin:8px 0}h2{font-size:20px;font-weight:650}p{font-size:14px;color:#aaa0b7;line-height:1.7}.eyebrow{font-size:10px;color:#b99bd9;letter-spacing:.18em}.summary,.panel,.institution{padding:24px;border:1px solid #ffffff16;border-radius:16px;background:var(--color-card,#1c1724);margin-top:24px;min-width:0}.summary{display:flex;align-items:center;gap:20px;flex-wrap:wrap}.summary strong{font-size:36px}.summary span{font-size:13px;color:#b9adc6;flex:1}.summary a,a{font-size:13px;color:#c7a4f0}.institution{display:flex;align-items:center;gap:20px}.institution a{overflow-wrap:anywhere}.initial{width:65px;height:65px;border-radius:16px;background:#a47be022;display:grid;place-items:center;color:#c7a4f0;font-size:22px;flex-shrink:0}.toolbar{display:flex;align-items:end;justify-content:space-between;gap:18px;flex-wrap:wrap}label{display:grid;gap:8px;font-size:12px;color:#b9adc6;flex:1;min-width:180px}input{min-width:0;width:100%;background:#110d19;border:1px solid #ffffff24;border-radius:8px;padding:11px 13px;color:white}button{padding:11px 16px;background:#a47be0;color:#160f20;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer}button:disabled{opacity:.4;cursor:default}.count{font-size:11px;margin:16px 0}button:focus-visible,a:focus-visible,input:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}@media(max-width:600px){.panel,.institution,.summary{padding:16px}.institution{align-items:flex-start}}
</style>
