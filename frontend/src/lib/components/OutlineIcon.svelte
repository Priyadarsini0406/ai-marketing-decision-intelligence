<script lang="ts">
    let { name, size = 20, strokeWidth = 1.6 }: { name: string; size?: number; strokeWidth?: number } = $props();
</script>

<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width={strokeWidth} stroke-linecap="round" stroke-linejoin="round" class="st-icon" aria-hidden="true" focusable="false">
    {#if name === 'dashboard'}
        <rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" />
        <rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" />
    {:else if name === 'enquiries'}
        <path d="M20 15a2 2 0 0 1-2 2H8l-4 4V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z" /><path d="M8.5 9h7M8.5 12.5h4.5" />
    {:else if name === 'new-enquiry'}
        <rect x="3" y="3" width="18" height="18" rx="4" /><path d="M12 8.5v7M8.5 12h7" />
    {:else if name === 'enquiry-status'}
        <circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3.25 2" />
    {:else if name === 'application'}
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" />
        <path d="M9 13.5h6M9 17h4" />
    {:else if name === 'profile'}
        <circle cx="12" cy="8" r="4" /><path d="M4.5 20.5c0-3.6 3.4-5.5 7.5-5.5s7.5 1.9 7.5 5.5" />
    {:else if name === 'notifications'}
        <path d="M18 9.5a6 6 0 1 0-12 0c0 4.5-2 5.5-2 5.5h16s-2-1-2-5.5" /><path d="M10.5 19.5a2 2 0 0 0 3 0" />
    {:else if name === 'settings'}
        <path d="M4 7h9M18.5 7H20M4 17h3.5M13 17h7" /><circle cx="15.25" cy="7" r="2.25" /><circle cx="9.75" cy="17" r="2.25" />
    {:else if name === 'logout'}
        <path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4" /><path d="M10 16.5 13.5 12 10 7.5" /><path d="M13.5 12H4" />
    {:else if name === 'menu'}
        <path d="M4 7h16M4 12h16M4 17h16" />
    {:else if name === 'cap'}
        <path d="M22 9 12 4 2 9l10 5z" /><path d="M6.5 11.5V16c0 1.5 2.7 3 5.5 3s5.5-1.5 5.5-3v-4.5" /><path d="M22 9v5" />
    {:else if name === 'mail'}
        <rect x="3" y="5" width="18" height="14" rx="2.5" /><path d="m3.8 7.2 8.2 5.8 8.2-5.8" />
    {:else if name === 'calendar'}
        <rect x="3" y="5" width="18" height="16" rx="2.5" /><path d="M8 3v4M16 3v4M3 10.5h18" />
    {:else if name === 'flag'}
        <path d="M5.5 21V3.5" /><path d="M5.5 4.5h11l-1.75 3.75L16.5 12h-11" />
    {:else if name === 'check'}
        <path d="m5 12.5 4.5 4.5L19 7.5" />
    {:else if name === 'arrow-right'}
        <path d="M4.5 12h13" /><path d="m12.5 6 6 6-6 6" />
    {:else if name === 'chevron-right'}
        <path d="m9.5 5 7 7-7 7" />
    {:else if name === 'chevron-down'}
        <path d="m5 9.5 7 7 7-7" />
    {:else if name === 'lock'}
        <rect x="4.5" y="10" width="15" height="10.5" rx="2.5" /><path d="M8 10V7.5a4 4 0 0 1 8 0V10" />
    {:else if name === 'eye'}
        <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12" />
        <circle cx="12" cy="12" r="3" />
    {:else if name === 'eye-off'}
        <path d="M9.9 5.8A9.6 9.6 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-2.7 3.6M6.4 7.6A16.6 16.6 0 0 0 2.5 12S6 18.5 12 18.5c1.3 0 2.4-.3 3.5-.7" />
        <path d="M10 10a3 3 0 0 0 4 4" /><path d="m3.5 3 17 14" />
    {:else if name === 'user'}
        <circle cx="12" cy="8" r="3.75" /><path d="M4.5 20.5c0-3.6 3.4-5.5 7.5-5.5s7.5 1.9 7.5 5.5" />
    {:else if name === 'users'}
        <circle cx="9.5" cy="8.5" r="3.25" /><path d="M3 20c0-3.2 2.9-4.9 6.5-4.9 1 0 2 .1 2.8.4" />
        <path d="M16 5.6a3.25 3.25 0 0 1 0 5.8" /><path d="M17.5 15.3c2 .6 3.5 2.1 3.5 4.7" />
    {:else if name === 'phone'}
        <path d="M7.5 3.5h9a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2h-9a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" />
        <path d="M10.5 17.5h3" />
    {:else if name === 'home'}
        <path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z" /><path d="M9.5 21v-6h5v6" />
    {:else if name === 'map-pin'}
        <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11" /><circle cx="12" cy="10" r="2.75" />
    {:else if name === 'building'}
        <path d="M4 21V5.5a1.5 1.5 0 0 1 1.5-1.5h7A1.5 1.5 0 0 1 14 5.5V21" /><path d="M14 10h4.5A1.5 1.5 0 0 1 20 11.5V21" />
        <path d="M2.5 21h19" /><path d="M7 8h4M7 12h4M7 16h4M17 14h.5M17 18h.5" />
    {:else if name === 'book'}
        <path d="M4 5.5A2 2 0 0 1 6 3.5h13v15H6a2 2 0 0 0-2 2z" /><path d="M4 18.5A2 2 0 0 1 6 16.5h13" />
    {:else if name === 'graduation'}
        <path d="M12 4 2 8.5 12 13l10-4.5z" /><path d="M6.5 11v4.5c0 1.4 2.5 2.5 5.5 2.5s5.5-1.1 5.5-2.5V11" />
    {:else if name === 'shield'}
        <path d="M12 3 5 5.8v5.4c0 4.3 2.9 8.1 7 9.8 4.1-1.7 7-5.5 7-9.8V5.8z" /><path d="m9.2 11.8 2 2 3.6-3.8" />
    {:else if name === 'briefcase'}
        <rect x="3" y="7.5" width="18" height="12.5" rx="2.5" /><path d="M8.5 7.5V6a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v1.5" />
        <path d="M3 12.5h18" />
    {:else if name === 'award'}
        <circle cx="12" cy="9" r="5.5" /><path d="m8.5 13.5-1.5 7 5-2.5 5 2.5-1.5-7" />
    {:else if name === 'alert'}
        <circle cx="12" cy="12" r="9" /><path d="M12 7.5v5.5" /><path d="M12 16.3h.01" />
    {:else if name === 'sparkle'}
        <path d="M12 3.5 13.6 8 18 9.5 13.6 11 12 15.5 10.4 11 6 9.5 10.4 8z" /><path d="M18 15.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" />
    {:else if name === 'chart'}
        <path d="M4 20V4" /><path d="M4 20h16" /><path d="M8 20v-6M12.5 20V8.5M17 20v-9" />
    {:else if name === 'clipboard'}
        <rect x="5" y="4.5" width="14" height="16" rx="2.5" /><path d="M9 4.5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 4.5v1h-6z" />
        <path d="M9 11h6M9 15h4" />
    {:else if name === 'help'}
        <circle cx="12" cy="12" r="9" /><path d="M9.6 9.4a2.5 2.5 0 1 1 3.3 2.4c-.6.2-.9.8-.9 1.4v.4" /><path d="M12 16.7h.01" />
    {:else if name === 'log-in'}
        <path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4" /><path d="m15 8 4 4-4 4" /><path d="M19 12H9" />
    {:else if name === 'key'}
        <circle cx="8" cy="12" r="4" /><path d="M12 12h9" /><path d="M17 12v3.5M20 12v2.5" />
    {/if}
</svg>
