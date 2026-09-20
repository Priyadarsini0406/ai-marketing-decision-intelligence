<script lang="ts">
    import { onMount } from 'svelte';
    import { api, signOut, type User } from '$lib/api';
    import { managerProfile, managerSettings } from '$lib/manager-demo';
    let { view, audience = 'manager' }: { view: 'profile' | 'settings'; audience?: 'manager' | 'admin' } = $props();
    let user = $state<User | null>(null);
    let profile = $state({ ...managerProfile });
    let savedProfile = $state({ ...managerProfile });
    let settings = $state({ ...managerSettings });
    let savedSettings = $state({ ...managerSettings });
    let editing = $state(false), busy = $state(false), loaded = $state(false);
    let notice = $state(''), error = $state('');
    const initials = $derived(savedProfile.name.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase());
    const dirty = $derived(JSON.stringify(settings) !== JSON.stringify(savedSettings));
    const options: { key: keyof typeof managerSettings; title: string; description: string }[] = [
        { key: 'emailNotifications', title: 'Email updates', description: 'Account and workspace updates delivered by email.' },
        { key: 'leadNotifications', title: 'Student lead updates', description: 'New enquiries and changes in student lead status.' },
        { key: 'predictionNotifications', title: 'Prediction updates', description: 'Admission prediction results and changes in lead potential.' },
        { key: 'marketingInsightNotifications', title: 'Marketing insights', description: 'Campaign performance, channel insights, and budget recommendations.' }
    ];
    const storageKey = () => `decisionintel:${audience}-account:${user!.id}`;
    onMount(async () => {
        try {
            user = await api('/auth/me');
            if (audience === 'admin' && user) { profile.name = user.name; profile.email = user.email; profile.role = 'Administrator'; }
            const stored = localStorage.getItem(storageKey());
            if (stored) {
                const parsed = JSON.parse(stored);
                for (const key of Object.keys(managerProfile) as (keyof typeof managerProfile)[]) {
                    if (key !== 'role' && typeof parsed.profile?.[key] === 'string') profile[key] = parsed.profile[key];
                }
                for (const { key } of options) if (typeof parsed.settings?.[key] === 'boolean') settings[key] = parsed.settings[key];
            }
            savedProfile = { ...profile }; savedSettings = { ...settings }; loaded = true;
        } catch (e) { error = `Unable to load account preferences. ${(e as Error).message}`; }
    });
    function persist(nextProfile: typeof managerProfile, nextSettings: typeof managerSettings) {
        error = ''; notice = '';
        try {
            localStorage.setItem(storageKey(), JSON.stringify({ profile: nextProfile, settings: nextSettings }));
            return true;
        } catch { error = 'Changes could not be saved. Allow browser storage and try again.'; return false; }
    }
    function saveProfile(event: SubmitEvent) {
        event.preventDefault();
        const clean = { ...profile, name: profile.name.trim(), email: profile.email.trim(), phone: profile.phone.trim(), institution: profile.institution.trim() };
        if (!clean.name || !clean.institution) { error = 'Enter a name and institution.'; return; }
        if (persist(clean, savedSettings)) { profile = clean; savedProfile = { ...clean }; editing = false; notice = 'Profile saved for this account in this browser.'; }
    }
    function cancel() { profile = { ...savedProfile }; editing = false; error = ''; notice = ''; }
    function saveSettings() {
        if (persist(savedProfile, settings)) { savedSettings = { ...settings }; notice = 'Preferences saved for this account in this browser.'; }
    }
    async function logout() {
        busy = true; error = '';
        try { await signOut(); window.location.assign('/login'); }
        catch (e) { error = (e as Error).message; busy = false; }
    }
</script>

<svelte:head><title>{view === 'profile' ? 'Profile' : 'Settings'} | DecisionIntel</title></svelte:head>
<div class="account-workspace">
    <div class="page-heading"><div><p class="eyebrow">YOUR WORKSPACE</p><h1>{view === 'profile' ? 'Profile' : 'Settings'}</h1><p class="subtitle">{view === 'profile' ? 'Your professional identity, contact details, and account access.' : 'Manage your workspace preferences and account access.'}</p></div><span class="workspace-badge">{audience === 'admin' ? 'Administration' : 'Admission & Marketing'}</span></div>
    {#if error}<p role="alert" class="message error">{error}</p>{/if}
    {#if notice}<p role="status" class="message success">{notice}</p>{/if}
    {#if !loaded && !error}<p role="status" class="subtitle">Loading your workspace...</p>{/if}
    {#if loaded && user}
        {#if view === 'profile'}
            <section class="identity-card">
                <div class="identity-banner"><span>DECISIONINTEL / PEOPLE</span><span class="status"><i></i> Workspace profile</span></div>
                <div class="identity-body"><div class="avatar" aria-hidden="true">{initials}</div><div class="identity-details"><h2>{savedProfile.name}</h2><p>{savedProfile.role} <span aria-hidden="true">·</span> {savedProfile.institution}</p><a href={`mailto:${savedProfile.email}`}>{savedProfile.email}</a></div><button class="button secondary" disabled={editing} onclick={() => { editing = true; notice = ''; }}>Edit profile</button></div>
            </section>
            <div class="content-grid">
                <section class="panel"><div class="section-heading"><span class="section-number">01</span><div><h2>Professional details</h2><p>Contact information used in your workspace profile.</p></div></div>
                    <form onsubmit={saveProfile}>
                        <div class="form-grid"><label>Full name<input bind:value={profile.name} readonly={!editing} required maxlength="100" autocomplete="name" /></label><label>Contact email<input type="email" bind:value={profile.email} readonly={!editing} required maxlength="254" autocomplete="email" /></label><label>Phone number<input type="tel" bind:value={profile.phone} readonly={!editing} maxlength="30" autocomplete="tel" /></label><label>Institution<input bind:value={profile.institution} readonly={!editing} required maxlength="150" autocomplete="organization" /></label></div>
                        <div class="detail-line"><span>Workspace role</span><strong>{audience === 'admin' ? 'Administrator' : managerProfile.role}</strong></div>
                        <div class="section-footer"><p>Profile edits are saved in this browser. Your sign-in email and account permissions stay managed by your administrator.</p>{#if editing}<div class="actions"><button class="button secondary" type="button" onclick={cancel}>Cancel</button><button class="button primary" type="submit">Save profile</button></div>{/if}</div>
                    </form>
                </section>
                <aside class="panel access-panel"><div class="section-heading"><span class="section-number">02</span><div><h2>Account access</h2><p>Your authenticated account.</p></div></div><dl><dt>Signed in as</dt><dd>{user.name}</dd><dt>Sign-in email</dt><dd>{user.email}</dd><dt>Permission level</dt><dd class="capitalize">{user.role.replaceAll('_', ' ')}</dd><dt>Account status</dt><dd><span class="status"><i></i>{user.active ? 'Active' : 'Inactive'}</span></dd></dl></aside>
            </div>
        {:else}
            <div class="settings-grid"><div class="space-y-6">
                <section class="panel"><div class="section-heading"><span class="section-number">01</span><div><h2>Notification preferences</h2><p>Choose the categories of updates that matter to you.</p></div></div>
                    <div class="preference-list">{#each options as option}<label class="preference"><span><strong>{option.title}</strong><span class="preference-description">{option.description}</span></span><span class="switch"><input type="checkbox" role="switch" aria-label={option.title} bind:checked={settings[option.key]} onchange={() => notice = ''} /><span class="switch-track" aria-hidden="true"></span></span></label>{/each}</div>
                    <div class="section-footer"><p>Preferences are saved for this account in this browser. Automated notification delivery is not connected.</p><div class="actions"><button class="button secondary" onclick={() => { settings = { ...managerSettings }; notice = ''; }}>Restore defaults</button><button class="button primary" disabled={!dirty} onclick={saveSettings}>Save preferences</button></div></div>
                </section>
                <section class="panel"><div class="section-heading"><span class="section-number">02</span><div><h2>Security &amp; access</h2><p>Manage access to your workspace.</p></div></div><div class="security-row"><div><h3>Password assistance</h3><p>Use the account recovery guide for administrator-assisted resets.</p></div><a href="/forgot-password" class="button secondary">Password help</a></div><div class="security-row"><div><h3>Current session</h3><p>Sign out of DecisionIntel on this device.</p></div><button class="button danger" disabled={busy} onclick={logout}>{busy ? 'Signing out...' : 'Sign out'}</button></div></section>
            </div><aside class="panel settings-summary"><div class="mini-avatar" aria-hidden="true">{initials}</div><h2>{savedProfile.name}</h2><p>{savedProfile.institution}</p><div class="summary-divider"></div><p class="eyebrow">PREFERENCE SUMMARY</p><strong class="summary-count">{options.filter(option => settings[option.key]).length}<span> / {options.length}</span></strong><p>Update categories selected</p>{#if dirty}<span class="unsaved">Unsaved changes</span>{:else}<span class="saved">Preferences up to date</span>{/if}</aside></div>
        {/if}
    {/if}
</div>

<style>
    .account-workspace{max-width:1240px;margin:auto;color:#eeeaf5}.page-heading{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:26px}.eyebrow{font-size:10px;font-weight:700;letter-spacing:.2em;color:#b59ad8}h1{font-size:32px;letter-spacing:-.035em;font-weight:700;margin:7px 0}.subtitle{font-size:14px;color:#a7a4b4;line-height:1.7}.workspace-badge{border:1px solid #ffffff16;border-radius:8px;padding:9px 13px;color:#beb5cc;font-size:11px;white-space:nowrap}.identity-card,.panel{border:1px solid #ffffff14;border-radius:18px;background:var(--color-card,#1d1726);min-width:0}.identity-card{overflow:hidden;margin-bottom:24px}.identity-banner{background:radial-gradient(ellipse at 90% 10%,#9766c950,transparent 65%),linear-gradient(110deg,#30213f,#211b35);height:106px;display:flex;align-items:flex-start;justify-content:space-between;padding:22px 28px;gap:12px}.identity-banner>span:first-child{font-size:10px;letter-spacing:.2em;color:#c6b4d9}.identity-body{display:flex;align-items:center;gap:22px;padding:0 28px 27px;flex-wrap:wrap}.avatar{width:88px;height:88px;border-radius:22px;background:linear-gradient(140deg,#c8a4ed,#7864b9);color:#21152d;display:grid;place-items:center;font-size:28px;font-weight:700;border:5px solid var(--color-card,#1d1726);margin-top:-22px;position:relative;flex-shrink:0}.identity-details{flex:1;min-width:0;padding-top:20px}.identity-details h2{font-size:23px;font-weight:700;letter-spacing:-.025em}.identity-details p{font-size:13px;color:#b7adc4;margin:5px 0}.identity-details a{font-size:12px;color:#b69acc;overflow-wrap:anywhere}.identity-body>.button{margin-top:20px}.content-grid{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px}.panel{padding:26px}.section-heading{display:flex;gap:13px;align-items:flex-start;margin-bottom:25px}.section-number{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:#a47be012;border:1px solid #a47be025;color:#b79ace;font-size:11px;flex-shrink:0}h2{font-size:16px;font-weight:650}.section-heading p,.security-row p{font-size:12px;color:#a7a4b4;line-height:1.6;margin-top:5px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px 18px}.form-grid label{display:grid;gap:9px;font-size:12px;color:#bfb6ca}input:not([type=checkbox]){width:100%;min-width:0;border:1px solid #ffffff1a;border-radius:9px;background:#100d1766;padding:12px 13px;font-size:13px;color:#f1eaf8}input[readonly]{color:#beb6ca;background:#ffffff03;border-color:#ffffff0b}.detail-line{display:flex;justify-content:space-between;gap:12px;font-size:12px;color:#a7a4b4;padding:23px 0}.detail-line strong{font-weight:500;color:#d1bfdc}.section-footer{border-top:1px solid #ffffff10;padding-top:20px}.section-footer p{font-size:11px;color:#91899e;line-height:1.7;max-width:550px}.actions{display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap;margin-top:20px}.button{display:inline-flex;justify-content:center;align-items:center;padding:10px 15px;font-size:12px;font-weight:600;border-radius:9px;cursor:pointer;white-space:nowrap}.secondary{border:1px solid #ffffff20;color:#d8cde5;background:#ffffff03}.primary{background:#b18adf;color:#1c102b;border:1px solid #c7a5ea}.danger{color:#efb1bd;border:1px solid #d778882f;background:#cf5d720a}.button:hover{filter:brightness(1.12)}.button:disabled{opacity:.45;cursor:default}.access-panel{align-self:start}dl{display:grid;gap:8px}dt{font-size:11px;color:#958b9f;margin-top:9px}dd{font-size:13px;overflow-wrap:anywhere}.status{display:inline-flex;align-items:center;gap:7px;font-size:11px;color:#b7dcca}.status i{height:6px;width:6px;background:#8acfb2;border-radius:50%}.settings-grid{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:24px}.preference{display:flex;align-items:center;justify-content:space-between;gap:22px;padding:19px 0;border-top:1px solid #ffffff0d;cursor:pointer}.preference strong{font-size:13px;font-weight:550}.preference-description{display:block;font-size:12px;line-height:1.6;color:#9d94aa;margin-top:5px}.switch{position:relative;flex-shrink:0;width:40px;height:23px}.switch input{position:absolute;inset:0;opacity:0;z-index:1;cursor:pointer;width:100%;height:100%}.switch-track{display:block;width:40px;height:23px;background:#47404f;border:1px solid #ffffff12;border-radius:20px;transition:background .15s}.switch-track:after{content:'';display:block;width:17px;height:17px;margin:2px;background:#e8dff2;border-radius:50%;transition:transform .15s}.switch input:checked+.switch-track{background:#9d77c8}.switch input:checked+.switch-track:after{transform:translateX(17px)}.switch input:focus-visible+.switch-track{outline:2px solid #c7a4f0;outline-offset:4px}.security-row{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px 0;border-top:1px solid #ffffff0d}.security-row h3{font-size:13px;font-weight:550}.settings-summary{align-self:start}.mini-avatar{width:46px;height:46px;display:grid;place-items:center;border-radius:13px;background:#a47be025;color:#c6a2ef;font-weight:700;margin-bottom:17px}.settings-summary>p{font-size:12px;line-height:1.6;color:#a7a4b4;margin-top:6px}.summary-divider{height:1px;background:#ffffff10;margin:25px 0}.summary-count{display:block;font-size:36px;font-weight:650;margin-top:14px}.summary-count span{font-size:18px;color:#81718f;font-weight:400}.saved,.unsaved{display:inline-block;font-size:10px;margin-top:16px;padding:6px 9px;border-radius:6px}.saved{background:#72c69a0d;color:#a1cbb4}.unsaved{background:#ffc36e0d;color:#e4c697}.message{padding:13px 16px;border-radius:10px;margin-bottom:20px;font-size:13px}.error{background:#f3718a10;color:#f8acbb}.success{background:#79c89b10;color:#add8c0}button:focus-visible,a:focus-visible,input:focus-visible{outline:2px solid #c7a4f0;outline-offset:3px}@media(max-width:1100px){.content-grid,.settings-grid{grid-template-columns:minmax(0,1fr)}.settings-summary{display:none}}@media(max-width:600px){.workspace-badge{display:none}.page-heading{margin-bottom:22px}h1{font-size:28px}.form-grid{grid-template-columns:minmax(0,1fr)}.panel{padding:20px}.identity-banner{padding:18px;height:94px}.identity-body{padding:0 18px 22px;gap:14px}.identity-details{flex-basis:65%}.identity-details h2{font-size:20px}.identity-body>.button{margin-top:0}.avatar{width:65px;height:65px;border-radius:18px;font-size:22px}.security-row{align-items:flex-start;flex-direction:column}.detail-line{flex-wrap:wrap}.identity-banner>span:first-child{font-size:8px}.identity-banner .status{font-size:9px}}
</style>
