<script lang="ts">
    import { onMount } from 'svelte';
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
<svelte:head><title>Marketing datasets | DecisionIntel</title></svelte:head>
<h1>Marketing datasets</h1><p>Manage source CSV or ZIP files. Uploaded datasets are stored for review; they do not automatically train models or replace existing leads.</p>
{#if error}<p role="alert">{error}</p>{/if}{#if message}<p role="status">{message}</p>{/if}
<form class="panel" onsubmit={upload}><label>Upload CSV or ZIP<input type="file" accept=".csv,.zip,text/csv,application/zip,application/x-zip-compressed" bind:files required /></label><small>CSV or ZIP containing one UTF-8 CSV with unique headers. Maximum 5 MB for both the upload and uncompressed CSV, 10,000 rows, and 100 columns.</small><div><button disabled={busy}>{busy ? 'Working…' : 'Upload dataset'}</button></div></form>
<div class="panel table-wrap"><table><thead><tr><th>Dataset</th><th>Rows</th><th>Uploaded</th><th>Actions</th></tr></thead><tbody>
{#each datasets as item}<tr><td>{item.name}</td><td>{item.row_count}</td><td>{new Date(item.created_at * 1000).toLocaleDateString()}</td><td><div class="actions"><button class="secondary" disabled={busy} onclick={() => preview(item.id)}>Preview / rename</button><button class="danger" disabled={busy} onclick={() => deleting = item.id}>Delete</button></div>{#if deleting === item.id}<p>Delete this dataset permanently?</p><div class="actions"><button class="danger" disabled={busy} onclick={() => remove(item.id)}>Confirm delete</button><button class="secondary" onclick={() => deleting = ''}>Cancel</button></div>{/if}</td></tr>{:else}<tr><td colspan="4">{loading ? 'Loading datasets…' : 'No datasets yet. Upload a CSV to get started.'}</td></tr>{/each}
</tbody></table></div>
{#if selected}<section class="panel"><h2>Dataset preview</h2><form onsubmit={saveName}><label>Dataset name<input bind:value={rename} required maxlength="200" /></label><div><button disabled={busy}>Save name</button></div></form><p>Showing the first {selected.rows?.length} of {selected.row_count} rows.</p><div class="table-wrap"><table><thead><tr>{#each selected.columns as column}<th>{column}</th>{/each}</tr></thead><tbody>{#each selected.rows ?? [] as row}<tr>{#each selected.columns as column}<td>{row[column]}</td>{/each}</tr>{/each}</tbody></table></div></section>{/if}
