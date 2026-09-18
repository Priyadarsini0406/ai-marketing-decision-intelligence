<script lang="ts">
    import { page } from '$app/state';
    import PlaceholderPage from '$lib/components/PlaceholderPage.svelte';
    const titles: Record<string, string> = { 'enquiries/new': 'New Enquiry', 'enquiries/status': 'Enquiry Status', application: 'Application Status', notifications: 'Notifications', settings: 'Settings' };
    let title = $derived(titles[page.params.path ?? ''] ?? 'Student Portal');
</script>
<PlaceholderPage {title} />
