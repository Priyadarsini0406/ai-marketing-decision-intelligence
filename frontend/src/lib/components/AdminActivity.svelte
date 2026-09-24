<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type User } from '$lib/api';
    import { reportCsv } from '$lib/manager-reports';
    import AnalyticsChart from './AnalyticsChart.svelte';
    let { view }: { view: 'activity' | 'audit-logs' } = $props();
    type Dataset = { id: string; name: string; row_count: number; columns: string[]; created_at: number };
    let datasets = $state<Dataset[]>([]), users = $state<User[]>([]);
    let config = $state<{ organization_name: string; currency: string; model: string } | null>(null);
    let loading = $state(true), error = $state(''), notice = $state(''), search = $state(''), period = $state('all'), selected = $state('');
    let refreshed = $state<number | null>(null);
    const events = $derived([...datasets].sort((a,b) => b.created_at - a.created_at || a.id.localeCompare(b.id)));
    const filtered = $derived(events.filter(item => `${item.name} ${item.id}`.toLowerCase().includes(search.toLowerCase()) && (period === 'all' || item.created_at * 1000 >= (refreshed ?? Date.now()) - Number(period) * 86400000)));
    const details = $derived(datasets.find(item => item.id === selected));
    const totalRows = $derived(datasets.reduce((sum,item) => sum + item.row_count,0));
    const roleNames = ['student','admission_manager','marketing_manager','admin'];
    async function load() {
        loading = true; error = ''; notice = '';
        try {
            const [records, accounts, settings] = await Promise.all([api('/admin/datasets'),api('/admin/users'),api('/admin/configuration')]);
            datasets = records; users = accounts; config = settings; refreshed = Date.now();
        } catch(e) { error = (e as Error).message; }
        finally { loading = false; }
    }
    onMount(load);
    function download() {
        const rows = filtered.map(item => ({ record_id: item.id, event: 'Dataset created', dataset: item.name, recorded_at_utc: new Date(item.created_at * 1000).toISOString(), actor: 'Not recorded', current_rows: item.row_count, current_columns: item.columns.length, evidence: 'Stored dataset creation timestamp' }));
        const url = URL.createObjectURL(new Blob([reportCsv(rows)], {type:'text/csv;charset=utf-8'}));
        const link = document.createElement('a'); link.href = url; link.download = `admin-${view}.csv`; link.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
        notice = `Downloaded ${rows.length} records.`;
    }
</script>

<svelte:head><title>{view === 'activity' ? 'System Activity' : 'Audit Logs'} | Administration</title></svelte:head>
<div class="activity-page">
    <header><div><p class="eyebrow">ADMINISTRATION / SYSTEM</p><h1>{view === 'activity' ? 'System Activity' : 'Audit Logs'}</h1><p>{view === 'activity' ? 'Review current platform activity and stored data records.' : 'Inspect the available creation records for stored datasets.'}</p></div><div class="actions"><button class="secondary" disabled={loading} onclick={load}>{loading ? 'Refreshing...' : 'Refresh'}</button><button disabled={loading || !filtered.length} onclick={download}>Download CSV</button></div></header>
    {#if error}<p role="alert">{error}</p>{/if}{#if notice}<p role="status">{notice}</p>{/if}
    {#if loading && !refreshed}<p role="status">Loading system records...</p>{/if}
    {#if refreshed}
        <p class="refresh-time">Last refreshed {new Date(refreshed).toLocaleString()}</p>
        <div class="stats"><section><span>Registered accounts</span><strong>{users.length}</strong></section><section><span>Active accounts</span><strong>{users.filter(user => user.active).length}</strong></section><section><span>Stored datasets</span><strong>{datasets.length}</strong></section><section><span>Stored rows</span><strong>{totalRows.toLocaleString()}</strong></section></div>
        {#if view === 'activity'}
            <div class="overview-grid"><AnalyticsChart title="Account role distribution" kind="donut" categories={roleNames.map(role => role.replaceAll('_',' '))} series={[{name:'Accounts',values:roleNames.map(role => users.filter(user => user.role === role).length)}]} unit="Accounts" />
                <section class="panel configuration"><p class="eyebrow">CURRENT CONFIGURATION</p><h2>{config?.organization_name}</h2><dl><dt>Report currency</dt><dd>{config?.currency}</dd><dt>Configured model</dt><dd>{config?.model.replaceAll('_',' ')}</dd><dt>Inactive accounts</dt><dd>{users.filter(user => !user.active).length}</dd></dl><a href="/admin/settings">Open platform settings →</a><p class="note">This is the current configuration, not a record of past configuration changes.</p></section>
            </div>
        {/if}
        <section class="panel"><div class="section-heading"><h2>{view === 'activity' ? 'Dataset activity' : 'Available audit records'}</h2><span>{filtered.length} records</span></div>
            <p class="note">Creation dates come from stored datasets. Historical actors, changes, deletions, and sign-in events were not recorded. Names, row counts, and columns show the current dataset state.</p>
            <div class="filters"><label>Search records<input type="search" bind:value={search} placeholder="Dataset name or record ID" /></label><div><label for="activity-period">Time period</label><select id="activity-period" bind:value={period}><option value="all">All time</option><option value="1">Last 24 hours</option><option value="7">Last 7 days</option><option value="30">Last 30 days</option></select></div></div>
            {#if view === 'activity'}<div class="timeline">{#each filtered as item}<article><span class="timeline-dot" aria-hidden="true"></span><div class="event-body"><div class="event-heading"><h3>Dataset created</h3><time datetime={new Date(item.created_at * 1000).toISOString()}>{new Date(item.created_at * 1000).toLocaleString()}</time></div><p>{item.name}</p><div class="event-footer"><span>{item.row_count} current rows · {item.columns.length} columns</span><button class="secondary" aria-label={`View ${item.name} details`} onclick={() => selected = item.id}>View details</button></div></div></article>{:else}<p class="empty">No creation records match these filters.</p>{/each}</div>
            {:else}<div class="table-wrap"><table><thead><tr><th>Recorded time</th><th>Event</th><th>Dataset</th><th>Actor</th><th>Current rows</th><th>Details</th></tr></thead><tbody>{#each filtered as item}<tr><td>{new Date(item.created_at * 1000).toLocaleString()}</td><td><span class="badge">Dataset created</span></td><td>{item.name}</td><td>Not recorded</td><td>{item.row_count}</td><td><button class="secondary" aria-label={`View ${item.name} details`} onclick={() => selected = item.id}>View details</button></td></tr>{:else}<tr><td colspan="6">No creation records match these filters.</td></tr>{/each}</tbody></table></div>{/if}
        </section>
        {#if details}<section class="panel" aria-label="Record details"><div class="section-heading"><h2>Record details</h2><button class="secondary" onclick={() => selected = ''}>Close details</button></div><dl><dt>Record ID</dt><dd>{details.id}</dd><dt>Dataset</dt><dd>{details.name}</dd><dt>Created (UTC)</dt><dd>{new Date(details.created_at * 1000).toISOString()}</dd><dt>Actor</dt><dd>Not recorded</dd><dt>Current rows</dt><dd>{details.row_count}</dd><dt>Current columns</dt><dd>{details.columns.join(', ')}</dd></dl><a href="/admin/datasets">Open dataset inventory →</a></section>{/if}
    {/if}
</div>

<style>
    .activity-page{max-width:1300px}header,.actions,.section-heading,.event-heading,.event-footer{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}h1{font-size:30px;font-weight:700;margin:8px 0}h2{font-size:18px;font-weight:650}h3{font-size:14px;font-weight:600}p{font-size:13px;line-height:1.7;color:#aaa0b7}.eyebrow{font-size:10px;color:#b99bd9;letter-spacing:.18em}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:24px 0}.stats section,.panel{padding:22px;border:1px solid #ffffff16;border-radius:16px;background:var(--color-card,#1c1724);min-width:0}.stats span{font-size:12px;color:#aaa0b7}.stats strong{display:block;font-size:28px;margin-top:10px}.panel{margin:20px 0}.overview-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px}.configuration{align-self:start}.configuration h2{margin:12px 0}.section-heading>span,.refresh-time,.note{font-size:11px;color:#a79ab8}.note{margin:14px 0}.refresh-time{margin-top:16px}.filters{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:18px;margin:22px 0}label{display:block;font-size:12px;color:#b9adc6}input,select{width:100%;min-width:0;padding:11px 13px;margin-top:8px;background:#110d19;border:1px solid #ffffff24;border-radius:8px;color:white}button{padding:10px 14px;background:#a47be0;color:#160f20;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer}.secondary{background:#ffffff08;color:#d9cbe9;border:1px solid #ffffff20}button:disabled{opacity:.4;cursor:default}.timeline article{display:flex;gap:16px;padding:20px 0;border-top:1px solid #ffffff10}.timeline-dot{width:10px;height:10px;margin-top:5px;border-radius:50%;background:#a47be0;box-shadow:0 0 12px #a47be040;flex-shrink:0}.event-body{flex:1;min-width:0}.event-body>p{overflow-wrap:anywhere;margin:8px 0}.event-heading time,.event-footer>span{font-size:11px;color:#a79ab8}.table-wrap{overflow:auto}table{width:100%;text-align:left;font-size:13px;border-collapse:collapse}th,td{padding:14px 12px;border-bottom:1px solid #ffffff10;white-space:nowrap}th{color:#b9a6d2;font-size:11px;text-transform:uppercase}.badge{color:#cbb1e7;font-size:11px;background:#a47be017;padding:5px 8px;border-radius:6px}dl{display:grid;grid-template-columns:140px minmax(0,1fr);gap:15px;margin:24px 0;font-size:13px}dt{color:#a79ab8}dd{overflow-wrap:anywhere}a{color:#c7a4f0;font-size:12px}.empty{padding:20px}[role=alert]{color:#f2a5b4}[role=status]{color:#a6d5b9}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}@media(max-width:700px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.overview-grid,.filters{grid-template-columns:minmax(0,1fr)}.panel{padding:16px}dl{grid-template-columns:minmax(0,1fr);gap:8px}dd{margin-bottom:10px}}
</style>
