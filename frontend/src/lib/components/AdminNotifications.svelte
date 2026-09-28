<script lang="ts">
    import { onMount } from 'svelte';
    import { api, type User } from '$lib/api';
    import { managerNotifications } from '$lib/manager-demo';
    let user = $state<User | null>(null), readIds = $state<string[]>([]), filter = $state('all'), search = $state(''), error = $state(''), loaded = $state(false);
    let inventory = $state<{ users: number; datasets: number; rows: number } | null>(null);
    const items = $derived(managerNotifications.map(item => ({ ...item, read: item.read || readIds.includes(item.id) })));
    const unread = $derived(items.filter(item => !item.read).length);
    const visible = $derived(items.filter(item => (filter === 'all' || (filter === 'unread' ? !item.read : item.read)) && `${item.title} ${item.description}`.toLowerCase().includes(search.toLowerCase())));
    onMount(async () => {
        try {
            user = await api('/auth/me');
            const stored = JSON.parse(localStorage.getItem(`decisionintel:admin-notifications:${user!.id}`) || '[]');
            if (Array.isArray(stored)) readIds = stored.filter(id => typeof id === 'string');
            loaded = true;
            const [users, datasets] = await Promise.all([api('/admin/users'), api('/admin/datasets')]);
            inventory = { users: users.length, datasets: datasets.length, rows: datasets.reduce((sum: number, item: { row_count: number }) => sum + item.row_count, 0) };
        } catch (e) { error = (e as Error).message; }
    });
    function markRead(ids: string[]) {
        error = '';
        try { const next = [...new Set([...readIds, ...ids])]; localStorage.setItem(`decisionintel:admin-notifications:${user!.id}`, JSON.stringify(next)); readIds = next; }
        catch { error = 'Unable to save read status. Allow browser storage and try again.'; }
    }
    const links: Record<string, string> = { lead: '/admin/students', application: '/admin/students', reminder: '/admin/managers', prediction: '/admin/reports', budget: '/admin/reports' };
</script>
<svelte:head><title>Notifications | Administration</title></svelte:head>
<div class="notifications"><header><div><p class="eyebrow">ADMINISTRATION / UPDATES</p><h1>Notifications</h1><p>Admission updates and your current platform inventory.</p></div><button disabled={!loaded || !unread} onclick={() => markRead(items.map(item => item.id))}>Mark all as read</button></header>
    {#if error}<p role="alert">{error}</p>{/if}
    <div class="stats"><section><span>Unread updates</span><strong>{unread}</strong></section><section><span>Total updates</span><strong>{items.length}</strong></section><section><span>Stored datasets</span><strong>{inventory?.datasets ?? '—'}</strong></section><section><span>Registered accounts</span><strong>{inventory?.users ?? '—'}</strong></section></div>
    {#if inventory}<div class="inventory"><span>{inventory.rows} rows across {inventory.datasets} stored datasets</span><a href="/admin/datasets">View dataset inventory →</a></div>{/if}
    <div class="toolbar"><label>Search notifications<input type="search" bind:value={search} placeholder="Search updates" /></label><div><label for="notification-status">Read status</label><select id="notification-status" bind:value={filter}><option value="all">All updates</option><option value="unread">Unread</option><option value="read">Read</option></select></div></div>
    <p class="note">Updates from the supplied admission data. Read status is saved for your account in this browser.</p>
    {#each visible as item}<article class:unread={!item.read}><div class="icon" aria-hidden="true">{item.type.slice(0,1).toUpperCase()}</div><div class="body"><div class="item-heading"><h2>{item.title}</h2><span>{item.read ? 'Read' : 'Unread'}</span></div><p>{item.description}</p><div class="item-actions"><span class="time">Source time: {item.time}</span><a href={links[item.type]}>View related records</a>{#if !item.read}<button class="secondary" disabled={!loaded} aria-label={`Mark ${item.title} as read`} onclick={() => markRead([item.id])}>Mark as read</button>{/if}</div></div></article>{:else}<p class="empty">No notifications match these filters.</p>{/each}
</div>
<style>
    .notifications{max-width:1200px}header,.toolbar,.inventory,.item-heading,.item-actions{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}h1{font-size:30px;font-weight:700;margin:8px 0}h2{font-size:15px;font-weight:650}p{font-size:13px;line-height:1.7;color:#6F6979}.eyebrow{font-size:10px;color:#6A31C4;letter-spacing:.18em}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:24px 0}.stats section,article,.inventory{background:var(--color-card,#FFFFFF);border:1px solid #E9E4DC;border-radius:15px;padding:22px;min-width:0}.stats span,.inventory{font-size:12px;color:#6F6979}.stats strong{display:block;font-size:28px;color:#262230;margin-top:10px}.toolbar{align-items:end;margin-top:24px}.toolbar>label{flex:1}label{display:block;font-size:12px;color:#6F6979}input,select{width:100%;min-width:0;background:#FFFFFF;border:1px solid #DED6C9;border-radius:8px;padding:11px 13px;color:#262230;margin-top:8px}button{padding:10px 14px;background:#6A31C4;color:#FFFFFF;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer}button:disabled{opacity:.4;cursor:default}.secondary{background:#6A31C408;color:#4E1D93;border:1px solid #DED6C9}.note{font-size:11px;margin:18px 0}article{display:flex;gap:16px;margin-top:14px}article.unread{border-color:#6A31C44d;background:#6A31C409}.body{min-width:0;flex:1}.icon{width:36px;height:36px;display:grid;place-items:center;background:#6A31C417;border-radius:10px;color:#6A31C4;flex-shrink:0}.item-heading span{font-size:10px;color:#4E1D93}.body>p{margin:8px 0 14px}.time{font-size:11px;color:#6F6979}.item-actions{justify-content:flex-start}a{font-size:12px;color:#6A31C4}.empty{padding:30px;border:1px dashed #DED6C9;border-radius:12px}[role=alert]{color:#A32B44}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #6A31C4;outline-offset:3px}@media(max-width:650px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}article{padding:16px}.toolbar{align-items:stretch;flex-direction:column}}
</style>
