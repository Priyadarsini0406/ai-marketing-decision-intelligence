<script lang="ts">
    import { onMount } from 'svelte';
    import { fly } from 'svelte/transition';
    import { api, type User } from '$lib/api';
    import OutlineIcon from '$lib/components/OutlineIcon.svelte';

    let user = $state<User | null>(null);
    onMount(async () => { try { user = await api('/auth/me'); } catch { window.location.assign('/login'); } });

    type Enquiry = { program: string; date: string; status: string; updated: string };

    const enquiries: Enquiry[] = [
        { program: 'MCA', date: '12 Sep 2026', status: 'Application Started', updated: 'Today' },
        { program: 'MBA', date: '05 Sep 2026', status: 'Counselling', updated: 'Yesterday' }
    ];
    const stages = [
        { label: 'Enquiry Submitted', done: true },
        { label: 'Counselling Completed', done: true },
        { label: 'Application In Progress', done: true },
        { label: 'Admission', done: false }
    ];
    const currentStage = 2;
    const programme = 'MCA · 2027 Intake';
    const applicationStatus = 'Application in progress';
    const upcoming = { title: 'Counselling Session', when: '18 September 2026 · 11:00 AM', state: 'Confirmed' };

    const activity = [
        { text: 'Application details updated', when: 'Today' },
        { text: 'Counselling session scheduled', when: 'This week' },
        { text: 'MCA enquiry submitted', when: 'This week' }
    ];

    const quickActions = [
        { label: 'Submit Enquiry', hint: 'Start a new admission enquiry', href: '/student/enquiries/new', icon: 'new-enquiry' },
        { label: 'My Enquiries', hint: 'Review and track every enquiry', href: '/student/enquiries', icon: 'enquiries' },
        { label: 'Application Status', hint: 'Check your admission stage', href: '/student/application', icon: 'application' },
        { label: 'Enquiry Status', hint: 'Follow up a submitted enquiry', href: '/student/enquiries/status', icon: 'enquiry-status' },
        { label: 'My Profile', hint: 'Keep your contact details current', href: '/student/profile', icon: 'profile' }
    ];

    const tones: Record<string, string> = { 'Application Started': 'accent', Counselling: 'amber', 'Under Review': 'neutral', 'Admission Confirmed': 'green' };
    const nextActions: Record<string, string> = {
        'Application Started': 'Complete your application',
        Counselling: 'Attend counselling session',
        'Under Review': 'Await review update',
        'Admission Confirmed': 'Complete admission formalities'
    };
    const toneOf = (status: string) => tones[status] ?? 'neutral';
    const actionFor = (status: string) => nextActions[status] ?? 'Await update from admissions';

    let firstName = $derived(user?.name.split(' ')[0] ?? '');
    const activeEnquiries = enquiries.filter(item => item.status !== 'Admission Confirmed').length;
</script>

<svelte:head><title>Student Dashboard | DecisionIntel</title></svelte:head>

{#if user}
<div class="page" in:fly={{ y: 12, duration: 400 }}>

    <header class="hero">
        <div class="hero-text">
            <h1>Welcome back, {firstName}</h1>
            <p>Explore opportunities and connect with us for your admission journey.</p>
        </div>
        <a class="btn btn-primary" href="/student/enquiries/new">
            <OutlineIcon name="new-enquiry" size={17} />
            Start New Enquiry
        </a>
    </header>

    <div class="split">
        <section class="card profile">
            <div class="card-head">
                <h2>Profile Summary</h2>
                <a class="link" href="/student/profile">View profile</a>
            </div>

            <div class="profile-id">
                <span class="profile-avatar">{user.name.charAt(0).toUpperCase()}</span>
                <div class="profile-names">
                    <p class="profile-name">{user.name}</p>
                    <p class="profile-email"><OutlineIcon name="mail" size={14} />{user.email}</p>
                </div>
            </div>

            <dl class="facts">
                <div class="fact">
                    <dt><OutlineIcon name="cap" size={15} />Interested program</dt>
                    <dd>{programme}</dd>
                </div>
                <div class="fact">
                    <dt><OutlineIcon name="application" size={15} />Application status</dt>
                    <dd><span class="badge accent">{applicationStatus}</span></dd>
                </div>
            </dl>

            <div class="counters">
                <div class="counter">
                    <p class="counter-value">{String(enquiries.length).padStart(2, '0')}</p>
                    <p class="counter-label">Total enquiries</p>
                </div>
                <div class="counter">
                    <p class="counter-value">{String(activeEnquiries).padStart(2, '0')}</p>
                    <p class="counter-label">Active enquiries</p>
                </div>
            </div>
        </section>

        <section class="card quick">
            <div class="card-head">
                <h2>Quick Actions</h2>
                <p class="card-hint">Jump straight to what you need</p>
            </div>
            <ul class="quick-list">
                {#each quickActions as action}
                    <li>
                        <a class="quick-link" href={action.href}>
                            <span class="quick-icon"><OutlineIcon name={action.icon} size={18} /></span>
                            <span class="quick-text">
                                <span class="quick-label">{action.label}</span>
                                <span class="quick-hint">{action.hint}</span>
                            </span>
                            <OutlineIcon name="chevron-right" size={16} />
                        </a>
                    </li>
                {/each}
            </ul>
        </section>
    </div>

    <div class="split split-journey">
        <section class="card">
            <div class="card-head">
                <div>
                    <h2>Admission Journey</h2>
                    <p class="card-hint">Your current admission progress</p>
                </div>
                <span class="badge accent">{applicationStatus}</span>
            </div>
            <ol class="journey">
                {#each stages as stage, index}
                    <li class="step" class:done={stage.done} class:current={index === currentStage}>
                        <span class="step-dot">
                            {#if stage.done}<OutlineIcon name="check" size={14} strokeWidth={2} />{:else}{index + 1}{/if}
                        </span>
                        <p class="step-label">{stage.label}</p>
                    </li>
                {/each}
            </ol>
        </section>

        <div class="stack">
            <section class="card">
                <p class="eyebrow"><OutlineIcon name="flag" size={14} />Next action</p>
                <h2 class="stack-title">{upcoming.title}</h2>
                <p class="stack-meta"><OutlineIcon name="calendar" size={14} />{upcoming.when}</p>
                <p class="confirmed">{upcoming.state}</p>
                <a class="link inline" href="/student/enquiries/status">View details</a>
            </section>

            <section class="card">
                <div class="card-head"><h2>Recent Activity</h2></div>
                <ul class="activity">
                    {#each activity as item}
                        <li>
                            <span class="activity-dot"></span>
                            <span class="activity-text">
                                <span class="activity-line">{item.text}</span>
                                <span class="activity-when">{item.when}</span>
                            </span>
                        </li>
                    {/each}
                </ul>
            </section>
        </div>
    </div>

    <section class="card">
        <div class="card-head">
            <div>
                <h2>My Enquiries</h2>
                <p class="card-hint">Enquiries you have submitted so far</p>
            </div>
            <a class="link" href="/student/enquiries">View all enquiries</a>
        </div>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Course / Program</th>
                        <th>Enquiry Date</th>
                        <th>Status</th>
                        <th>Next Action</th>
                        <th><span class="sr-only">Open</span></th>
                    </tr>
                </thead>
                <tbody>
                    {#each enquiries as enquiry}
                        <tr>
                            <td class="cell-strong">{enquiry.program}</td>
                            <td>{enquiry.date}</td>
                            <td><span class="badge {toneOf(enquiry.status)}">{enquiry.status}</span></td>
                            <td>{actionFor(enquiry.status)}</td>
                            <td class="cell-action"><a class="link" href="/student/enquiries/status" aria-label="View {enquiry.program} enquiry">View</a></td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </section>

</div>
{/if}

<style>
    .page { display: flex; flex-direction: column; gap: 1.5rem; padding-bottom: 2.5rem; }

    .hero { display: flex; flex-direction: column; gap: 1.25rem; }
    @media (min-width: 768px) { .hero { flex-direction: row; align-items: center; justify-content: space-between; } }
    .hero-text h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -.01em; color: var(--st-text); }
    .hero-text p { margin-top: .4rem; font-size: .95rem; color: var(--st-text-muted); }

    .btn { display: inline-flex; align-items: center; justify-content: center; gap: .5rem; padding: .7rem 1.15rem; border-radius: var(--st-radius-sm); font-size: .875rem; font-weight: 600; border: 1px solid transparent; }
    .btn-primary { background-image: var(--st-accent-sheen); color: #FFFFFF; box-shadow: inset 0 1px 0 rgba(255, 255, 255, .3), 0 12px 24px -14px rgba(91, 33, 182, .95); }
    .btn-primary:hover { border-color: var(--st-accent-ink); box-shadow: inset 0 1px 0 rgba(255, 255, 255, .38), 0 16px 28px -14px rgba(91, 33, 182, 1); }

    .card { background-color: var(--st-surface); border: 1px solid var(--st-border); border-radius: var(--st-radius); padding: 1.4rem; box-shadow: var(--st-shadow); }
    .card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1.1rem; }
    .card-head h2 { font-size: 1.0625rem; font-weight: 650; color: var(--st-text); }
    .card-hint { margin-top: .2rem; font-size: .8125rem; color: var(--st-text-muted); }

    .split { display: grid; gap: 1.5rem; }
    @media (min-width: 1024px) { .split { grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr); } }
    .split-journey { align-items: start; }
    @media (min-width: 1024px) { .split-journey { grid-template-columns: minmax(0, 1.9fr) minmax(0, 1fr); } }

    .profile-id { display: flex; align-items: center; gap: .85rem; padding-bottom: 1.1rem; border-bottom: 1px solid var(--st-border); }
    .profile-avatar { width: 2.75rem; height: 2.75rem; border-radius: 999px; background-color: var(--st-accent-soft); border: 1px solid var(--st-accent-line); color: var(--st-accent-ink); display: grid; place-items: center; font-weight: 700; }
    .profile-names { min-width: 0; }
    .profile-name { font-size: .95rem; font-weight: 650; color: var(--st-text); overflow-wrap: anywhere; }
    .profile-email { margin-top: .2rem; display: flex; align-items: center; gap: .35rem; font-size: .8125rem; color: var(--st-text-muted); overflow-wrap: anywhere; }

    .facts { margin-top: 1.1rem; display: grid; gap: .85rem; }
    .fact dt { display: flex; align-items: center; gap: .4rem; font-size: .75rem; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: var(--st-text-muted); }
    .fact dd { margin-top: .35rem; font-size: .9rem; color: var(--st-text); }

    .counters { margin-top: 1.25rem; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }
    .counter { background-color: var(--st-surface-muted); border: 1px solid var(--st-border); border-radius: var(--st-radius-sm); padding: .8rem .9rem; }
    .counter-value { font-size: 1.375rem; font-weight: 700; color: var(--st-text); }
    .counter-label { margin-top: .15rem; font-size: .75rem; color: var(--st-text-muted); }

    .quick-list { list-style: none; margin: 0; padding: 0; display: grid; gap: .5rem; }
    @media (min-width: 640px) { .quick-list { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
    .quick-link { display: flex; align-items: center; gap: .75rem; padding: .75rem .85rem; border: 1px solid var(--st-border); border-radius: var(--st-radius-sm); background-color: var(--st-surface); color: var(--st-text-muted); }
    .quick-link:hover { background-color: var(--st-accent-soft); border-color: var(--st-accent-line); box-shadow: 0 12px 24px -18px var(--st-accent-glow); color: var(--st-text); }
    .quick-icon { width: 2.25rem; height: 2.25rem; flex: none; border-radius: 10px; background-color: var(--st-accent-soft); color: var(--st-accent); display: grid; place-items: center; }
    .quick-link:hover .quick-icon { background-color: var(--st-surface); box-shadow: inset 0 0 0 1px var(--st-accent-line); }
    .quick-text { min-width: 0; flex: 1; }
    .quick-label { display: block; font-size: .875rem; font-weight: 600; color: var(--st-text); }
    .quick-hint { display: block; margin-top: .1rem; font-size: .75rem; color: var(--st-text-muted); }

    .journey { list-style: none; margin: 0; padding: 0; display: grid; gap: .75rem; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    @media (min-width: 640px) { .journey { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
    .step { position: relative; padding: .95rem .8rem; text-align: center; border: 1px solid var(--st-border); border-radius: var(--st-radius-sm); background-color: var(--st-surface-muted); }
    .step-dot { width: 1.9rem; height: 1.9rem; margin: 0 auto .55rem; border-radius: 999px; display: grid; place-items: center; font-size: .8rem; font-weight: 600; background-color: var(--st-surface); border: 1px solid var(--st-border-strong); color: var(--st-text-muted); }
    .step.done .step-dot { background-image: var(--st-accent-sheen); border-color: var(--st-accent); color: #FFFFFF; }
    .step.current { background-color: var(--st-accent-soft); border-color: var(--st-accent-line); box-shadow: inset 0 0 0 1px var(--st-accent-line); }
    .step.current .step-dot { border-color: var(--st-accent); color: var(--st-accent-ink); }
    .step-label { font-size: .8125rem; line-height: 1.35; color: var(--st-text-muted); }
    .step.done .step-label, .step.current .step-label { color: var(--st-text); font-weight: 600; }

    .stack { display: grid; gap: 1.5rem; }
    .eyebrow { display: flex; align-items: center; gap: .4rem; font-size: .7rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--st-accent); }
    .stack-title { margin-top: .6rem; font-size: 1.0625rem; font-weight: 650; color: var(--st-text); }
    .stack-meta { margin-top: .4rem; display: flex; align-items: center; gap: .4rem; font-size: .8125rem; color: var(--st-text-muted); }
    .confirmed { margin-top: .6rem; display: inline-block; font-size: .75rem; font-weight: 600; color: var(--st-green-ink); background-color: var(--st-green-soft); border: 1px solid #E7F2EC; border-radius: 999px; padding: .15rem .6rem; }

    .activity { list-style: none; margin: 0; padding: 0; display: grid; gap: .9rem; }
    .activity li { display: flex; gap: .7rem; align-items: flex-start; }
    .activity-dot { width: .5rem; height: .5rem; margin-top: .4rem; flex: none; border-radius: 999px; background-color: var(--st-accent); }
    .activity-line { display: block; font-size: .875rem; color: var(--st-text); }
    .activity-when { display: block; margin-top: .1rem; font-size: .75rem; color: var(--st-text-muted); }

    .badge { display: inline-block; font-size: .75rem; font-weight: 600; padding: .2rem .6rem; border-radius: 999px; border: 1px solid transparent; white-space: nowrap; }
    .badge.accent { background-color: var(--st-accent-soft); border-color: var(--st-accent-line); color: var(--st-accent-ink); }
    .badge.amber { background-color: var(--st-amber-soft); border-color: #F3EBFC; color: var(--st-amber-ink); }
    .badge.green { background-color: var(--st-green-soft); border-color: #E7F2EC; color: var(--st-green-ink); }
    .badge.neutral { background-color: var(--st-surface-muted); border-color: var(--st-border); color: var(--st-text-muted); }

    .link { font-size: .8125rem; font-weight: 600; color: var(--st-accent); white-space: nowrap; }
    .link:hover { color: var(--st-accent-ink); text-decoration: underline; text-underline-offset: 3px; }
    .link.inline { display: inline-block; margin-top: .9rem; }

    .table-wrap { overflow-x: auto; }
    table { width: 100%; min-width: 640px; font-size: .875rem; }
    thead th { text-align: left; padding: 0 .9rem .65rem; font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--st-text-muted); border-bottom: 1px solid var(--st-border); }
    thead th:first-child { padding-left: 0; }
    thead th:last-child { padding-right: 0; text-align: right; }
    tbody td { padding: .85rem .9rem; color: var(--st-text-muted); border-bottom: 1px solid var(--st-border); }
    tbody td:first-child { padding-left: 0; }
    tbody td:last-child { padding-right: 0; text-align: right; }
    tbody tr:last-child td { border-bottom: none; }
    .cell-strong { font-weight: 600; color: var(--st-text); }
    .cell-action a { font-size: .8125rem; font-weight: 600; color: var(--st-accent); }
    .cell-action a:hover { color: var(--st-accent-ink); text-decoration: underline; text-underline-offset: 3px; }
    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
</style>
