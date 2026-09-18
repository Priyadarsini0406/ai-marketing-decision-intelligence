<script lang="ts">
  import { managerNotifications } from '$lib/manager-demo';

  let notifications = $state(managerNotifications);

  function markRead(id: string) {
    notifications = notifications.map((item) => item.id === id ? { ...item, read: true } : item);
  }

  function markAllRead() {
    notifications = notifications.map((item) => ({ ...item, read: true }));
  }
</script>

<svelte:head>
  <title>Notifications | DecisionIntel</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
    <div>
      <p class="text-xs uppercase tracking-[0.2em] text-accent font-semibold">Account</p>
      <h1 class="mt-2 text-3xl font-bold text-white">Notifications</h1>
    </div>
    <button class="rounded-xl border border-white/10 bg-card px-4 py-2 text-sm text-white" onclick={markAllRead}>Mark all as read</button>
  </div>

  <div class="space-y-3">
    {#each notifications as item}
      <div class={`rounded-2xl border p-4 ${item.read ? 'border-white/10 bg-card' : 'border-accent/25 bg-accent/5'}`}>
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-start gap-3">
            <div class="mt-1 flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-lg">
              {item.type === 'lead' ? '👤' : item.type === 'application' ? '📝' : item.type === 'prediction' ? '📈' : item.type === 'budget' ? '💸' : '🔔'}
            </div>
            <div>
              <p class="text-base font-semibold text-white">{item.title}</p>
              <p class="mt-1 text-sm text-text-secondary">{item.description}</p>
              <p class="mt-2 text-xs uppercase tracking-[0.16em] text-text-secondary">{item.time}</p>
            </div>
          </div>
          <button class="text-sm text-accent hover:underline" onclick={() => markRead(item.id)}>
            {item.read ? 'Read' : 'Mark as Read'}
          </button>
        </div>
      </div>
    {/each}
  </div>
</div>
