<script lang="ts">
    import { onMount } from 'svelte';
    import { suppliedDatasets } from '$lib/admin-education';
    import { reportCsv } from '$lib/manager-reports';
    import DataTable from '$lib/DataTable.svelte';
    let { view = 'datasets' }: { view?: 'datasets' | 'data-import' } = $props();
    let sourceType = $state('lead');
    const source = $derived(suppliedDatasets.find(item => item.type === sourceType)!);
    function downloadSource() {
        const url = URL.createObjectURL(new Blob([reportCsv(source.rows)], { type: 'text/csv;charset=utf-8' }));
        const link = document.createElement('a'); link.href = url; link.download = `${source.type}.csv`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    async function importSource() {
        await action(async () => {
            const form = new FormData();
            form.append('file', new Blob([reportCsv(source.rows)], { type: 'text/csv' }), `${source.type}.csv`);
            await api('/admin/datasets', { method: 'POST', body: form });
            message = `${source.label} imported successfully.`; await load();
        });
    }

    import { api } from '$lib/api';
    type Dataset = { id: string; name: string; columns: string[]; row_count: number; created_at: number; rows?: Record<string, string>[] };
    let datasets = $state<Dataset[]>([]), selected = $state<Dataset | null>(null), files = $state<FileList>(), error = $state(''), message = $state(''), busy = $state(false), loading = $state(true), deleting = $state(''), rename = $state('');
    async function load() { datasets = await api('/admin/datasets'); }
    onMount(async () => { try { await load(); } catch(e) { error = (e as Error).message; } finally { loading = false; } });
    async function action(work: () => Promise<void>) { busy = true; error = ''; message = ''; try { await work(); } catch(e) { error = (e as Error).message; } finally { busy = false; } }
    async function upload(event: SubmitEvent) { event.preventDefault(); await action(async () => { if (!files?.[0]) throw new Error('Select a CSV or ZIP file'); const form = new FormData(); form.append('file', files[0]); await api('/admin/datasets', { method: 'POST', body: form }); files = undefined; message = 'Dataset uploaded successfully.'; await load(); }); }
    async function preview(id: string) { await action(async () => { selected = await api(`/admin/datasets/${id}`); rename = selected!.name; }); }
    async function remove(id: string) { await action(async () => { await api(`/admin/datasets/${id}`, { method: 'DELETE' }); if(selected?.id === id) selected = null; deleting = ''; message = 'Dataset deleted.'; await load(); }); }
    async function saveName(event: SubmitEvent) { event.preventDefault(); await action(async () => { if (!selected) return; await api(`/admin/datasets/${selected.id}`, { method: 'PUT', body: JSON.stringify({ name: rename }) }); selected.name = rename; await load(); message = 'Dataset renamed.'; }); }
</script>
<svelte:head><title>{view === 'data-import' ? 'Data Import' : 'Datasets'} | DecisionIntel</title></svelte:head>
<div class="admin-datasets"><p class="eyebrow">DATA MANAGEMENT</p><h1>{view === 'data-import' ? 'Data Import' : 'Datasets'}</h1><p>Manage source CSV files. Uploaded datasets are stored for review; they do not automatically train models or replace existing leads.</p>
{#if error}<p role="alert">{error}</p>{/if}{#if message}<p role="status">{message}</p>{/if}
<div class="summary"><section><span>Supplied datasets</span><strong>{suppliedDatasets.length}</strong></section><section><span>Uploaded datasets</span><strong>{datasets.length}</strong></section><section><span>Stored rows</span><strong>{datasets.reduce((total, item) => total + item.row_count, 0)}</strong></section></div>
<section class="panel"><div class="panel-heading"><div><h2>Supplied data library</h2><p>Preview the included admission records and analytics tables. Import a copy to manage it in the stored dataset inventory.</p></div><a href={view === 'data-import' ? '/admin/datasets' : '/admin/data-import'}>{view === 'data-import' ? 'Open dataset inventory' : 'Open Data Import'} ?</a></div>
<div class="source-controls"><div><label for="source-dataset">Supplied dataset</label><select id="source-dataset" bind:value={sourceType} disabled={busy}>{#each suppliedDatasets as item}<option value={item.type}>{item.label} ({item.rows.length} rows)</option>{/each}</select></div><button class="secondary" disabled={busy} onclick={downloadSource}>Download source CSV</button><button disabled={busy} onclick={importSource}>{busy ? 'Working...' : 'Import selected dataset'}</button></div>
<p>{source.description}</p><p class="count">{source.rows.length} rows ? {Object.keys(source.rows[0] ?? {}).length} columns</p><DataTable rows={source.rows} /></section>
<form class="panel" onsubmit={upload}><h2>Upload your dataset</h2><label>Upload CSV or ZIP<input type="file" accept=".csv,.zip,text/csv,application/zip,application/x-zip-compressed" bind:files required /></label><small>CSV or ZIP containing one UTF-8 CSV with unique headers. Maximum 5 MB for both the upload and uncompressed CSV, 10,000 rows, and 100 columns.</small><div><button disabled={busy}>{busy ? 'Working…' : 'Upload dataset'}</button></div></form>
<section class="panel"><h2>Stored dataset inventory</h2><div class="table-wrap"><table><thead><tr><th>Dataset</th><th>Rows</th><th>Uploaded</th><th>Actions</th></tr></thead><tbody>
{#each datasets as item}<tr><td>{item.name}</td><td>{item.row_count}</td><td>{new Date(item.created_at * 1000).toLocaleDateString()}</td><td><div class="actions"><button class="secondary" disabled={busy} onclick={() => preview(item.id)}>Preview / rename</button><button class="danger" disabled={busy} onclick={() => deleting = item.id}>Delete</button></div>{#if deleting === item.id}<p>Delete this dataset permanently?</p><div class="actions"><button class="danger" disabled={busy} onclick={() => remove(item.id)}>Confirm delete</button><button class="secondary" onclick={() => deleting = ''}>Cancel</button></div>{/if}</td></tr>{:else}<tr><td colspan="4">{loading ? 'Loading datasets…' : 'No datasets yet. Upload a CSV to get started.'}</td></tr>{/each}
</tbody></table></div></section>
{#if selected}<section class="panel"><h2>Dataset preview</h2><form onsubmit={saveName}><label>Dataset name<input bind:value={rename} required maxlength="200" /></label><div><button disabled={busy}>Save name</button></div></form><p>Showing the first {selected.rows?.length} of {selected.row_count} rows.</p><div class="table-wrap"><table><thead><tr>{#each selected.columns as column}<th>{column}</th>{/each}</tr></thead><tbody>{#each selected.rows ?? [] as row}<tr>{#each selected.columns as column}<td>{row[column]}</td>{/each}</tr>{/each}</tbody></table></div></section>{/if}

</div>
<style>
.admin-datasets{max-width:1300px}h1{font-size:30px;font-weight:700;margin:8px 0}h2{font-size:18px;font-weight:650;margin-bottom:12px}p{font-size:13px;color:#aaa0b7;line-height:1.7;margin:12px 0}.eyebrow{font-size:10px;color:#b99bd9;letter-spacing:.18em}.summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:24px 0}.summary section,.panel{padding:22px;background:var(--color-card,#1c1724);border:1px solid #ffffff16;border-radius:16px;min-width:0}.summary span{font-size:12px;color:#aaa0b7}.summary strong{display:block;font-size:28px;margin-top:10px}.panel{margin:22px 0}.panel-heading,.source-controls{display:flex;gap:16px;justify-content:space-between;align-items:center;flex-wrap:wrap}.source-controls{align-items:end;margin:20px 0}.source-controls>div{flex:1;min-width:180px}label{display:block;font-size:12px;color:#b9adc6}input,select{width:100%;min-width:0;border:1px solid #ffffff24;background:#110d19;border-radius:8px;padding:11px 13px;color:white;margin:8px 0 12px}.source-controls select{margin-bottom:0}small{display:block;font-size:11px;color:#a79ab8;margin:8px 0 18px}button{padding:10px 14px;border-radius:8px;background:#a47be0;color:#160f20;cursor:pointer;font-size:12px;font-weight:600}.secondary{background:#ffffff08;color:#d9cbe9;border:1px solid #ffffff20}.danger{background:#cf61701a;color:#efb1bf;border:1px solid #cf61702a}button:disabled{opacity:.5;cursor:default}.actions{display:flex;gap:9px;flex-wrap:wrap}.table-wrap{overflow:auto}table{width:100%;text-align:left;border-collapse:collapse;font-size:13px}th,td{padding:14px 12px;white-space:nowrap;border-bottom:1px solid #ffffff10}th{font-size:11px;color:#b9a6d2}.count{font-size:11px}a{font-size:12px;color:#c7a4f0}[role=alert]{color:#f2a5b4}[role=status]{color:#a6d5b9}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}@media(max-width:600px){.summary{grid-template-columns:1fr}.panel{padding:16px}}
</style>
