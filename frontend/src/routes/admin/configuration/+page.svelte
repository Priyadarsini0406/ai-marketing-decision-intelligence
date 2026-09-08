<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    type Config = {organization_name: string; currency: string; model: string; conversion_threshold: number; test_size: number; random_seed: number};
    let config = $state<Config | null>(null), error = $state(''), message = $state(''), busy = $state(false);
    onMount(async () => { try { config = await api('/admin/configuration'); } catch(e) { error = (e as Error).message; } });
    async function save(event: SubmitEvent) { event.preventDefault(); busy = true; error = ''; message = ''; try { config = await api('/admin/configuration', { method: 'PUT', body: JSON.stringify(config) }); message = 'Configuration saved.'; } catch(e) { error = (e as Error).message; } finally { busy = false; } }
</script>
<svelte:head><title>System configuration | DecisionIntel</title></svelte:head>
<h1>System / model configuration</h1><p>Settings are persisted in the platform database.</p>
{#if error}<p role="alert">{error}</p>{/if}{#if message}<p role="status">{message}</p>{/if}
{#if config}<form onsubmit={save}>
<section class="panel"><h2>System settings</h2><div class="grid"><label>Organization name<input bind:value={config.organization_name} required maxlength="100" /></label><label>Report currency<select bind:value={config.currency}>{#each ['USD', 'INR', 'EUR', 'GBP'] as currency}<option>{currency}</option>{/each}</select></label><label>High probability threshold<input type="number" bind:value={config.conversion_threshold} min="0" max="1" step="0.01" required /></label></div><p>The threshold controls the high probability lead count in reports. Currency changes display formatting only.</p></section>
<section class="panel"><h2>Model parameters</h2><p>Saved for future training integration. This project does not currently include a training service; saving these parameters does not retrain models or change stored predictions.</p><div class="grid"><label>Preferred model<select bind:value={config.model}><option value="xgboost">XGBoost</option><option value="random_forest">Random forest</option><option value="logistic_regression">Logistic regression</option></select></label><label>Test set fraction<input type="number" bind:value={config.test_size} min="0.1" max="0.4" step="0.01" required /></label><label>Random seed<input type="number" bind:value={config.random_seed} min="0" max="2147483647" step="1" required /></label></div></section>
<div><button disabled={busy}>{busy ? 'Saving…' : 'Save configuration'}</button></div></form>{:else if !error}<p>Loading settings…</p>{/if}
