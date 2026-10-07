<script lang="ts">
    import { tick } from 'svelte';
    import { managerLeads } from '$lib/manager-demo';
    import { api, type User } from '$lib/api';
    import DataTable from '$lib/DataTable.svelte';
    import OutlineIcon from '$lib/components/OutlineIcon.svelte';

    let { view }: { view: 'students' | 'managers' } = $props();
    const MANAGER_ROLES = ['admission_manager', 'marketing_manager'];
    const ROLE_LABEL: Record<string, string> = { admission_manager: 'Admission Manager', marketing_manager: 'Marketing Manager' };

    let search = $state('');
    let status = $state('All statuses');
    let accounts = $state<User[]>([]);
    let loadError = $state('');
    let name = $state('');
    let email = $state('');
    let password = $state('');
    let confirm = $state('');
    let revealed = $state(false);
    let errors = $state<Record<string, string>>({});
    let notice = $state('');
    let failure = $state('');
    let busy = $state(false);
    let editor = $state<HTMLElement>();
    let firstInput = $state<HTMLInputElement>();

    async function loadAccounts() {
        if (view !== 'managers') return;
        try {
            accounts = await api('/admin/users');
            loadError = '';
        } catch (e) {
            loadError = (e as Error).message;
        }
    }
    $effect(() => {
        void view;
        void loadAccounts();
    });

    function assignmentsFor(person: string) {
        const leads = managerLeads.filter((item) => item.assigned_to === person);
        return {
            assigned_students: leads.length,
            programs: [...new Set(leads.map((item) => item.course_interested))].join(', ') || 'No assignments',
            students: leads.map((item) => item.student_name).join(', ') || 'No assignments'
        };
    }

    const managerAccounts = $derived(
        accounts
            .filter((account) => MANAGER_ROLES.includes(account.role))
            .filter((account) => `${account.name} ${account.email}`.toLowerCase().includes(search.trim().toLowerCase()))
    );

    const managerRows = $derived(
        managerAccounts.map((account) => ({
            Manager: account.name,
            Email: account.email,
            Role: ROLE_LABEL[account.role] ?? account.role,
            Status: account.active ? 'Active' : 'Inactive',
            ...assignmentsFor(account.name)
        }))
    );

    const students = $derived(
        managerLeads.filter(
            (item) =>
                (status === 'All statuses' || item.lead_status === status) &&
                [item.student_name, item.email, item.course_interested, item.assigned_to, item.location].some((value) =>
                    value.toLowerCase().includes(search.trim().toLowerCase())
                )
        )
    );

    const cards = $derived(
        view === 'students'
            ? [
                  { label: 'Student records', value: managerLeads.length },
                  { label: 'Applications', value: managerLeads.filter((item) => item.lead_status === 'Application').length },
                  { label: 'Admitted', value: managerLeads.filter((item) => item.lead_status === 'Admitted').length },
                  { label: 'Programs covered', value: new Set(managerLeads.map((item) => item.course_interested)).size }
              ]
            : [
                  { label: 'Manager accounts', value: accounts.filter((account) => MANAGER_ROLES.includes(account.role)).length },
                  { label: 'Active managers', value: accounts.filter((account) => MANAGER_ROLES.includes(account.role) && account.active).length },
                  { label: 'Assigned students', value: managerLeads.length },
                  { label: 'Programs covered', value: new Set(managerLeads.map((item) => item.course_interested)).size }
              ]
    );

    function validate() {
        const found: Record<string, string> = {};
        if (!name.trim()) found.name = 'Enter the manager name';
        if (!email.trim()) found.email = 'Enter an email address';
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) found.email = 'Enter a valid email address';
        if (!password) found.password = 'Create a password';
        else if (password.length < 12) found.password = 'Use at least 12 characters';
        if (!confirm) found.confirm = 'Re-enter the password';
        else if (confirm !== password) found.confirm = 'Passwords do not match';
        errors = found;
        return Object.keys(found).length === 0;
    }

    async function addManager(event: SubmitEvent) {
        event.preventDefault();
        if (busy) return;
        failure = '';
        notice = '';
        if (!validate()) return;
        busy = true;
        try {
            await api('/admin/users', {
                method: 'POST',
                body: JSON.stringify({
                    name: name.trim(),
                    email: email.trim().toLowerCase(),
                    password,
                    role: 'admission_manager',
                    active: true
                })
            });
            notice = `${name.trim()} can now sign in with ${email.trim().toLowerCase()}.`;
            name = '';
            email = '';
            password = '';
            confirm = '';
            errors = {};
            await loadAccounts();
        } catch (e) {
            failure = (e as Error).message;
        } finally {
            busy = false;
        }
    }

    async function openEditor() {
        await tick();
        editor?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        firstInput?.focus({ preventScroll: true });
    }
</script>

<svelte:head><title>{view === 'students' ? 'Students' : 'Managers'} | Administration</title></svelte:head>

<div class="directory">
    <header>
        <div>
            <p class="eyebrow">USER MANAGEMENT</p>
            <h1>{view === 'students' ? 'Students' : 'Managers'}</h1>
            <p>
                {view === 'students'
                    ? 'Student enquiries, program interests, and admission progress.'
                    : 'Manager sign-in accounts, student assignments, and program coverage.'}
            </p>
        </div>
        {#if view === 'managers'}
            <button class="button primary" type="button" onclick={openEditor}>
                <OutlineIcon name="users" size={18} /> Add manager
            </button>
        {:else}
            <a class="button" href="/admin/users">Manage user accounts</a>
        {/if}
    </header>

    <div class="stats">
        {#each cards as item}
            <section class="panel"><span>{item.label}</span><strong>{item.value}</strong></section>
        {/each}
    </div>

    {#if view === 'managers'}
        <section class="panel editor" id="add-manager" bind:this={editor}>
            <div class="editor-head">
                <span class="editor-icon"><OutlineIcon name="briefcase" size={20} strokeWidth={1.7} /></span>
                <div>
                    <h2>Add manager</h2>
                    <p>Managers cannot register themselves. Create the account here and share these credentials securely.</p>
                </div>
            </div>

            {#if notice}<p class="di-alert di-alert-success" role="status">{notice}</p>{/if}
            {#if failure}<p class="di-alert di-alert-error" role="alert">{failure}</p>{/if}

            <form onsubmit={addManager} novalidate>
                <div class="grid">
                    <div>
                        <label class="di-label" for="manager-name">Full name</label>
                        <input class="di-input" id="manager-name" bind:this={firstInput} bind:value={name} autocomplete="off" placeholder="Manager name" aria-invalid={!!errors.name} />
                        {#if errors.name}<span class="di-field-error">{errors.name}</span>{/if}
                    </div>
                    <div>
                        <label class="di-label" for="manager-email">Email address <span class="di-hint inline">(user ID)</span></label>
                        <input class="di-input" id="manager-email" type="email" bind:value={email} autocomplete="off" placeholder="manager@example.com" aria-invalid={!!errors.email} />
                        {#if errors.email}<span class="di-field-error">{errors.email}</span>{/if}
                    </div>
                    <div>
                        <label class="di-label" for="manager-password">Password</label>
                        <div class="password">
                            <input class="di-input" id="manager-password" type={revealed ? 'text' : 'password'} bind:value={password} autocomplete="new-password" placeholder="At least 12 characters" aria-invalid={!!errors.password} />
                            <button type="button" class="reveal" aria-label={revealed ? 'Hide password' : 'Show password'} aria-pressed={revealed} onclick={() => (revealed = !revealed)}>
                                <OutlineIcon name={revealed ? 'eye-off' : 'eye'} size={18} />
                            </button>
                        </div>
                        {#if errors.password}<span class="di-field-error">{errors.password}</span>{/if}
                    </div>
                    <div>
                        <label class="di-label" for="manager-confirm">Confirm password</label>
                        <input class="di-input" id="manager-confirm" type={revealed ? 'text' : 'password'} bind:value={confirm} autocomplete="new-password" placeholder="Re-enter the password" aria-invalid={!!errors.confirm} />
                        {#if errors.confirm}<span class="di-field-error">{errors.confirm}</span>{/if}
                    </div>
                </div>
                <div class="actions">
                    <button class="button primary" type="submit" disabled={busy}>
                        {busy ? 'Creating manager…' : 'Create manager'}
                    </button>
                    <a class="button ghost" href="/login">Preview the sign-in page</a>
                </div>
            </form>
        </section>
    {/if}

    <section class="panel">
        <div class="toolbar">
            <label>Search {view}<input type="search" bind:value={search} placeholder={view === 'students' ? 'Search name, contact, or program' : 'Search manager name or email'} /></label>
            {#if view === 'students'}
                <div class="field">
                    <label for="student-status">Admission status</label>
                    <select id="student-status" bind:value={status}>
                        <option>All statuses</option>
                        {#each [...new Set(managerLeads.map((item) => item.lead_status))] as value}<option>{value}</option>{/each}
                    </select>
                </div>
            {/if}
        </div>

        {#if loadError}<p class="di-alert di-alert-error" role="alert">{loadError}</p>{/if}

        {#if view === 'managers'}
            <p class="note">Manager accounts are created by administrators. Students register themselves from the public sign-up page.</p>
            <p class="note">Showing {managerRows.length} of {accounts.filter((account) => MANAGER_ROLES.includes(account.role)).length} manager accounts</p>
            <DataTable rows={managerRows} empty="No manager accounts yet. Use Add manager to create the first one." />
        {:else}
            <p class="note">Directory records from the supplied admission data. Sign-in accounts are managed separately under User Accounts.</p>
            <p class="note">Showing {students.length} of {managerLeads.length} records</p>
            <DataTable rows={students.map((item) => ({ Student: item.student_name, Email: item.email, Phone: item.phone, Program: item.course_interested, Intake: item.preferred_intake, Location: item.location, Qualification: item.qualification, 'Academic score (%)': item.academic_score, Status: item.lead_status, Manager: item.assigned_to, Source: item.lead_source, 'Enquiry date': item.enquiry_date }))} empty="No records match these filters." />
        {/if}
    </section>
</div>

<style>
    .directory { max-width:1300px; }
    header { display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap; align-items:center; }
    h1 { font-size:30px; font-weight:700; margin:8px 0; color:var(--di-text, #262230); }
    h2 { font-size:18px; font-weight:650; margin:0 0 4px; color:var(--di-text, #262230); }
    p { font-size:14px; color:var(--di-muted, #6F6979); line-height:1.7; }
    .eyebrow { font-size:10px; color:var(--di-accent, #6D28D9); letter-spacing:.18em; font-weight:700; text-transform:uppercase; }
    .stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin:24px 0; }
    .panel { min-width:0; padding:22px; border:1px solid var(--di-border, #E9E4DC); border-radius:16px; background-color:var(--di-surface, #fff); box-shadow:var(--di-shadow, 0 1px 2px rgba(38,34,48,.04)); }
    .panel + .panel { margin-top:22px; }
    .stats span { font-size:12px; color:var(--di-muted, #6F6979); }
    .stats strong { display:block; font-size:28px; margin-top:10px; color:var(--di-text, #262230); }
    .toolbar { display:flex; gap:16px; flex-wrap:wrap; align-items:end; }
    .toolbar label, .field { display:grid; gap:8px; font-size:12px; color:var(--di-muted, #6F6979); }
    .toolbar > label { flex:1; min-width:220px; }
    .toolbar input, .toolbar select { min-width:0; width:100%; background-color:var(--di-surface, #fff); border:1px solid var(--di-border-strong, #DED6C9); border-radius:12px; padding:11px 13px; color:var(--di-text, #262230); font:inherit; font-size:14px; }

    .editor { scroll-margin-top:20px; }
    .editor-head { display:flex; align-items:flex-start; gap:.75rem; margin-bottom:1.25rem; }
    .editor-head p { font-size:13px; margin:0; }
    .editor-icon { display:grid; place-items:center; width:2.5rem; height:2.5rem; flex:none; border-radius:12px; background-color:var(--di-accent-soft, #F3EBFC); border:1px solid var(--di-accent-line, #E7D6FA); color:var(--di-accent-ink, #5B21B6); }
    form { display:grid; gap:1.125rem; }
    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1.125rem; }
    .di-hint.inline { display:inline; font-weight:400; }
    .password { position:relative; }
    .password .di-input { padding-right:2.875rem; }
    .reveal { position:absolute; right:.5rem; top:50%; transform:translateY(-50%); display:grid; place-items:center; width:2rem; height:2rem; border:0; border-radius:8px; background:transparent; color:var(--di-muted, #6F6979); cursor:pointer; }
    .reveal:hover { color:var(--di-accent-ink, #5B21B6); background:var(--di-accent-soft, #F3EBFC); }
    .actions { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }

    button, .button { display:inline-flex; align-items:center; gap:.5rem; padding:10px 14px; border-radius:12px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit; }
    .button { text-decoration:none; }
    .primary { background-image:var(--di-accent-sheen); color:#fff; border:1px solid transparent; box-shadow:0 10px 22px -12px rgba(91,33,182,.85); }
    .primary:hover:not(:disabled) { background-image:var(--di-accent-sheen); filter:brightness(1.06); }
    .ghost { background-color:transparent; color:var(--di-muted, #6F6979); border:1px solid var(--di-border-strong, #DED6C9); }
    .ghost:hover { background-color:var(--di-accent-soft, #F3EBFC); color:var(--di-accent-ink, #5B21B6); }
    button:disabled { opacity:.5; cursor:not-allowed; }
    .note { font-size:11px; margin:16px 0 0; }

    @media (max-width:900px) { .grid { grid-template-columns:minmax(0,1fr); } }
    @media (max-width:700px) { .stats { grid-template-columns:repeat(2,minmax(0,1fr)); } .panel { padding:16px; } }
</style>
