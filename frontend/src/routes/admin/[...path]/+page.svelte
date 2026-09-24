<script lang="ts">
    import { page } from '$app/state';
    import PlaceholderPage from '$lib/components/PlaceholderPage.svelte';
    import AdminDirectory from '$lib/components/AdminDirectory.svelte';
    import AdminEducation from '$lib/components/AdminEducation.svelte';
    import AdminDatasets from '$lib/components/AdminDatasets.svelte';
    import ManagerAccount from '$lib/components/ManagerAccount.svelte';
    import AdminNotifications from '$lib/components/AdminNotifications.svelte';
    import AdminPlatformSettings from '$lib/components/AdminPlatformSettings.svelte';
    import AdminActivity from '$lib/components/AdminActivity.svelte';
    const titles: Record<string, string> = { students: 'Students', managers: 'Managers', courses: 'Courses / Programs', institutions: 'Institutions', 'data-import': 'Data Import', activity: 'System Activity', 'audit-logs': 'Audit Logs', notifications: 'Notifications', profile: 'Profile', settings: 'Settings' };
    let title = $derived(titles[page.params.path ?? ''] ?? 'Administration');
</script>
{#if page.params.path === 'students' || page.params.path === 'managers'}
    {#key page.params.path}<AdminDirectory view={page.params.path} />{/key}
{:else if page.params.path === 'courses' || page.params.path === 'institutions'}
    {#key page.params.path}<AdminEducation view={page.params.path} />{/key}
{:else if page.params.path === 'data-import'}
    <AdminDatasets view="data-import" />
{:else if page.params.path === 'notifications'}
    <AdminNotifications />
{:else if page.params.path === 'activity' || page.params.path === 'audit-logs'}
    {#key page.params.path}<AdminActivity view={page.params.path} />{/key}
{:else if page.params.path === 'profile' || page.params.path === 'settings'}
    {#key page.params.path}<ManagerAccount view={page.params.path} audience="admin" />{/key}
    {#if page.params.path === 'settings'}<AdminPlatformSettings />{/if}
{:else}<PlaceholderPage {title} />{/if}
