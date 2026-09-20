<script lang="ts">
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    type Configuration = { organization_name: string; currency: string; model: string; conversion_threshold: number; test_size: number; random_seed: number };
    let config = $state<Configuration | null>(null), saved = $state<Configuration | null>(null), error = $state(''), notice = $state(''), busy = $state(false);
    onMount(async () => { try { config = await api('/admin/configuration'); saved = { ...config! }; } catch(e) { error = (e as Error).message; } });
    async function save(event: SubmitEvent) {
        event.preventDefault(); busy = true; error = ''; notice = '';
        try { config = await api('/admin/configuration', { method: 'PUT', body: JSON.stringify(config) }); saved = { ...config! }; notice = 'Platform settings saved.'; }
        catch(e) { error = (e as Error).message; } finally { busy = false; }
    }
</script>
<section class="platform-settings"><h2>Platform configuration</h2><p>Organization and reporting preferences shared across the platform. These settings are saved in the database.</p>
    {#if error}<p role="alert">{error}</p>{/if}{#if notice}<p role="status">{notice}</p>{/if}
    {#if config}<form onsubmit={save}><fieldset disabled={busy}><div class="fields"><label>Organization name<input required maxlength="100" bind:value={config.organization_name} /></label><div><label for="platform-currency">Report currency</label><select id="platform-currency" bind:value={config.currency}>{#each ['USD','INR','EUR','GBP'] as value}<option>{value}</option>{/each}</select></div><label>High probability threshold<input type="number" min="0" max="1" step="0.01" required bind:value={config.conversion_threshold} /></label></div><p>Currency controls report formatting; it does not convert monetary values. The threshold controls the high-probability lead count.</p><div class="actions"><button type="button" class="secondary" onclick={() => { config = { ...saved! }; notice = ''; }}>Discard changes</button><button>{busy ? 'Saving...' : 'Save platform settings'}</button><a href="/admin/configuration">Advanced model configuration →</a></div></fieldset></form>{:else if !error}<p role="status">Loading platform settings...</p>{/if}
</section>
<style>
    .platform-settings{max-width:1240px;margin:24px auto 0;background:var(--color-card,#1c1724);border:1px solid #ffffff16;border-radius:18px;padding:26px}h2{font-size:17px;font-weight:650}p{font-size:12px;color:#aaa0b7;line-height:1.7;margin:12px 0}.fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:22px 0}label{display:block;font-size:12px;color:#b9adc6}input,select{width:100%;min-width:0;background:#110d19;border:1px solid #ffffff24;border-radius:8px;padding:11px 13px;color:white;margin-top:8px}.actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:22px}button{padding:10px 14px;background:#a47be0;color:#160f20;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer}.secondary{background:#ffffff08;color:#cfb8e9;border:1px solid #ffffff20}fieldset:disabled{opacity:.5}a{color:#c7a4f0;font-size:12px}[role=alert]{color:#f2a5b4}[role=status]{color:#a6d5b9}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}@media(max-width:700px){.fields{grid-template-columns:minmax(0,1fr)}.platform-settings{padding:20px}}
</style>
