<script lang="ts">
    import './student-theme.css';
    import DashboardLayout from '$lib/components/DashboardLayout.svelte';
    let { children } = $props();
</script>
<DashboardLayout role="student">{@render children()}</DashboardLayout>
