<script lang="ts">
    import { page } from '$app/state';
    import PlaceholderPage from '$lib/components/PlaceholderPage.svelte';
    const titles: Record<string, string> = { students: 'Students', managers: 'Managers', courses: 'Courses / Programs', institutions: 'Institutions', 'data-import': 'Data Import', activity: 'System Activity', 'audit-logs': 'Audit Logs', notifications: 'Notifications', profile: 'Profile', settings: 'Settings' };
    let title = $derived(titles[page.params.path ?? ''] ?? 'Administration');
</script>
<PlaceholderPage {title} />
