<script lang="ts">
    import { api } from '$lib/api';
    let files = $state<FileList>();
    let busy = $state(false), error = $state('');
    let uploaded = $state<{ name: string; row_count: number } | null>(null);
    async function upload(event: SubmitEvent) {
        event.preventDefault();
        busy = true; error = ''; uploaded = null;
        try {
            if (!files?.[0]) throw new Error('Select a CSV or ZIP file');
            const form = new FormData();
            form.append('file', files[0]);
            uploaded = await api('/datasets', { method: 'POST', body: form });
            files = undefined;
        } catch (e) { error = (e as Error).message; }
        finally { busy = false; }
    }
</script>

<svelte:head><title>Upload datasets | DecisionIntel</title></svelte:head>
<h1 class="text-3xl font-bold mb-3">Upload datasets</h1>
<p class="text-text-secondary mb-6">Upload marketing CSV or ZIP files for administrator review. Uploading stores the dataset; it does not automatically train a model or replace existing leads.</p>
{#if error}<p role="alert" class="text-red-400 mb-4">{error}</p>{/if}
{#if uploaded}<p role="status" class="text-accent mb-4">Dataset uploaded successfully: {uploaded.name} ({uploaded.row_count} rows).</p>{/if}
<form class="bg-card border border-white/10 rounded-2xl p-6 flex flex-col gap-5 max-w-xl" onsubmit={upload}>
    <label class="flex flex-col gap-2">Upload CSV or ZIP
        <input type="file" accept=".csv,.zip,text/csv,application/zip,application/x-zip-compressed" bind:files required disabled={busy} aria-describedby="upload-limits" class="border border-white/20 rounded-lg p-3" />
    </label>
    <p id="upload-limits" class="text-sm text-text-secondary">CSV or ZIP containing one UTF-8 CSV with unique headers. Maximum 5 MB for both the upload and uncompressed CSV, 10,000 rows, and 100 columns.</p>
    <button class="bg-cta text-black font-semibold rounded-lg p-3" disabled={busy}>{busy ? 'Uploading…' : 'Upload dataset'}</button>
</form>
