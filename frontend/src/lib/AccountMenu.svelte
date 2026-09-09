<script lang="ts">
    import type { User } from '$lib/api';
    let { user }: { user: User } = $props();
    const initials = $derived(user.name.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'U');
</script>
<a class="avatar" href={user.role === 'admin' ? '/admin/account' : '/dashboard/account'} aria-label="My account">{initials}</a>
<style>
    .avatar { display:flex; align-items:center; justify-content:center; flex-shrink:0; width:44px; height:44px; padding:0; border-radius:50%; background:var(--color-cta); color:var(--color-primary); font-size:15px; font-weight:700; border:2px solid #ffffff24; box-shadow:0 0 18px #f2a62b28; transition:transform .2s,box-shadow .2s; }
    .avatar:hover {transform:translateY(-2px);box-shadow:0 0 24px #a47be055}
    .avatar:focus-visible{outline:2px solid var(--color-accent);outline-offset:4px}
    @media(prefers-reduced-motion:reduce){.avatar{transition:none}.avatar:hover{transform:none}}
</style>
