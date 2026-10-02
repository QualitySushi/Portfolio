<script lang="ts">
  import { onMount } from 'svelte';

  let { 
    backendUrl = import.meta.env.PUBLIC_API_URL 
      ? `${import.meta.env.PUBLIC_API_URL}/api/estimator` 
      : 'http://localhost:4000/api/estimator',
    onSelectRun = (runId: string) => {}
  } = $props<{
    backendUrl?: string;
    onSelectRun?: (runId: string) => void;
  }>();

  let batchJobs = $state<Array<{ id: string; created_at: string; target_variable: string; total_iterations: number }>>([]);
  let selectedBatchId = $state<string | null>(null);
  let batchDetails = $state<any | null>(null);
  let loadingList = $state(false);
  let loadingDetails = $state(false);
  let errorMessage = $state<string | null>(null);

  async function fetchBatchJobs() {
    loadingList = true;
    errorMessage = null;
    try {
      const res = await fetch(`${backendUrl}/batch-jobs?limit=15`);
      if (!res.ok) throw new Error('Failed to fetch batch job history.');
      batchJobs = await res.json();
    } catch (err: unknown) {
      errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
    } finally {
      loadingList = false;
    }
  }

  async function selectBatch(id: string) {
    selectedBatchId = id;
    onSelectRun(id);
    
    loadingDetails = true;
    errorMessage = null;
    try {
      const res = await fetch(`${backendUrl}/batch-jobs/${id}`);
      if (!res.ok) throw new Error('Failed to load batch job details.');
      batchDetails = await res.json();
    } catch (err: unknown) {
      errorMessage = err instanceof Error ? err.message : 'An unknown error occurred.';
    } finally {
      loadingDetails = false;
    }
  }

  onMount(() => {
    fetchBatchJobs();
  });
</script>

<div class="bg-white p-6 rounded-lg shadow-md border border-gray-200 space-y-4">
  <div class="flex justify-between items-center">
    <h2 class="text-xl font-semibold">Batch Job History</h2>
    <button 
      onclick={fetchBatchJobs}
      class="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded transition"
    >
      Refresh
    </button>
  </div>

  {#if errorMessage}
    <div class="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
      {errorMessage}
    </div>
  {/if}

  {#if loadingList}
    <p class="text-sm text-gray-500 py-4 text-center">Loading batch history...</p>
  {:else if batchJobs.length === 0}
    <p class="text-sm text-gray-500 py-4 text-center">No past batch jobs found.</p>
  {:else}
    <div class="border rounded-lg overflow-hidden max-h-96 overflow-y-auto">
      <ul class="divide-y divide-gray-200 text-sm">
        {#each batchJobs as job}
          <li>
            <button
              onclick={() => selectBatch(job.id)}
              class="w-full text-left p-3 hover:bg-blue-50/50 transition flex justify-between items-center {selectedBatchId === job.id ? 'bg-blue-100/60 font-medium' : ''}"
            >
              <div>
                <span class="font-semibold block text-gray-800">Target: {job.target_variable}</span>
                <span class="text-xs text-gray-500">ID: {job.id.slice(0, 8)}... • {new Date(job.created_at).toLocaleString()}</span>
              </div>
              <span class="text-xs bg-gray-100 px-2.5 py-1 rounded-full text-gray-600">
                {job.total_iterations} runs
              </span>
            </button>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>