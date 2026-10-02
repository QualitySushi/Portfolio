<script lang="ts">
  import { onMount } from 'svelte';

  let telemetryData = $state<{ total_events: number; recent_activity: any[] } | null>(null);
  let loading = $state(true);

  onMount(async () => {
    try {
      const res = await fetch('http://localhost:4000/api/analytics');
      const data = await res.json();
      telemetryData = data;
    } catch (err) {
      console.error('Failed to load telemetry analytics', err);
    } finally {
      loading = false;
    }
  });
</script>

<div class="max-w-6xl mx-auto px-4 py-12">
  <h1 class="text-3xl font-bold text-gray-900 mb-6">Portfolio Telemetry Dashboard</h1>

  {#if loading}
    <p class="text-gray-500">Loading engagement metrics...</p>
  {:else if telemetryData}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white p-6 rounded-xl border shadow-sm">
        <h3 class="text-sm font-medium text-gray-500">Total Tracked Events</h3>
        <p class="text-4xl font-extrabold text-blue-600 mt-2">{telemetryData.total_events}</p>
      </div>
    </div>

    <h2 class="text-xl font-bold text-gray-900 mb-4">Recent Visitor Activity</h2>
    <div class="bg-white rounded-xl border shadow-sm overflow-hidden">
      <table class="w-full text-left border-collapse text-sm">
        <thead class="bg-gray-50 border-b text-gray-700">
          <tr>
            <th class="p-3">Timestamp</th>
            <th class="p-3">Event Type</th>
            <th class="p-3">Path</th>
            <th class="p-3">Metadata</th>
          </tr>
        </thead>
        <tbody class="divide-y text-gray-600">
          {#each telemetryData.recent_activity as event}
            <tr class="hover:bg-gray-50">
              <td class="p-3 whitespace-nowrap">{new Date(event.created_at).toLocaleString()}</td>
              <td class="p-3 font-semibold text-gray-900">{event.event_type}</td>
              <td class="p-3">{event.path}</td>
              <td class="p-3 font-mono text-xs bg-gray-50 rounded">{JSON.stringify(event.metadata)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <p class="text-red-500">Failed to load analytics data from gateway.</p>
  {/if}
</div>