<script lang="ts">
  import { onMount } from 'svelte';

  let {
    backendUrl = import.meta.env.PUBLIC_API_URL 
      ? `${import.meta.env.PUBLIC_API_URL}/api/gcode` 
      : 'http://localhost:4000/api/gcode',
    userId = '',
    onSelectGeneration = (generation: Generation) => {}
  } = $props<{
    backendUrl?: string;
    userId?: string;
    onSelectGeneration?: (generation: Generation) => void;
  }>();

  type Generation = {
    id: string;
    user_id: string;
    file_type: string;
    output_data: string;
    created_at: string;
  };

  let generations = $state<Generation[]>([]);
  let selectedGenerationId = $state<string | null>(null);
  let selectedGeneration = $state<Generation | null>(null);

  let loading = $state(false);
  let errorMessage = $state<string | null>(null);

  async function fetchHistory() {
    if (!userId) {
      errorMessage = 'No user ID was provided.';
      generations = [];
      return;
    }

    loading = true;
    errorMessage = null;

    try {
      const res = await fetch(
        `${backendUrl}/history/${encodeURIComponent(userId)}`
      );

      if (!res.ok) {
        throw new Error('Failed to fetch generation history.');
      }

      const result = await res.json();

      if (result.status !== 'success') {
        throw new Error('The backend returned an unsuccessful response.');
      }

      generations = result.data ?? [];

      selectedGenerationId = null;
      selectedGeneration = null;
    } catch (err: unknown) {
      errorMessage =
        err instanceof Error
          ? err.message
          : 'An unknown error occurred.';
    } finally {
      loading = false;
    }
  }

  function selectGeneration(generation: Generation) {
    selectedGenerationId = generation.id;
    selectedGeneration = generation;
    onSelectGeneration(generation);
  }

  onMount(() => {
    fetchHistory();
  });
</script>

<div class="bg-slate-900 border border-slate-800 rounded-xl shadow-lg overflow-hidden">
  <!-- Header -->
  <div class="flex justify-between items-center px-5 py-4 border-b border-slate-800">
    <div>
      <h2 class="text-lg font-semibold text-slate-100">
        Generation History
      </h2>

      <p class="text-xs text-slate-500 mt-1">
        Previously saved G-Code generations
      </p>
    </div>

    <button
      onclick={fetchHistory}
      disabled={loading}
      class="px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-800 disabled:text-slate-600 border border-slate-700 rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
    >
      {loading ? 'Refreshing...' : 'Refresh'}
    </button>
  </div>

  <div class="p-5 space-y-4">

    <!-- Error -->
    {#if errorMessage}
      <div class="p-3 bg-red-950/40 border border-red-900/60 text-red-400 text-sm rounded-lg">
        {errorMessage}
      </div>
    {/if}

    <!-- Loading -->
    {#if loading}
      <div class="flex items-center justify-center py-8">
        <p class="text-sm text-slate-500">
          Loading generation history...
        </p>
      </div>

    <!-- Empty -->
    {:else if generations.length === 0}
      <div class="border border-dashed border-slate-800 rounded-lg py-8 text-center">
        <p class="text-sm text-slate-500">
          No past generations found.
        </p>

        <p class="text-xs text-slate-600 mt-1">
          Saved generations will appear here.
        </p>
      </div>

    <!-- History List -->
    {:else}
      <div class="border border-slate-800 rounded-lg overflow-hidden">
        <div class="px-4 py-2 bg-slate-950 border-b border-slate-800">
          <span class="text-xs font-medium uppercase tracking-wider text-slate-500">
            Saved Generations
          </span>
        </div>

        <div class="max-h-80 overflow-y-auto">
          <ul class="divide-y divide-slate-800">
            {#each generations as generation}
              <li>
                <button
                  onclick={() => selectGeneration(generation)}
                  class="w-full text-left px-4 py-3 transition-colors cursor-pointer
                    {selectedGenerationId === generation.id
                      ? 'bg-indigo-950/40 border-l-2 border-indigo-500'
                      : 'hover:bg-slate-800/60 border-l-2 border-transparent'}"
                >
                  <div class="flex justify-between items-center gap-4">
                    <div class="min-w-0">
                      <span class="font-medium block text-slate-200">
                        {generation.file_type}
                      </span>

                      <span class="text-xs text-slate-500 block mt-1">
                        ID: {generation.id.slice(0, 8)}...
                      </span>

                      <span class="text-xs text-slate-600 block mt-0.5">
                        {new Date(generation.created_at).toLocaleString()}
                      </span>
                    </div>

                    <span
                      class="text-xs px-2 py-1 rounded-md shrink-0
                        {selectedGenerationId === generation.id
                          ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                          : 'bg-slate-800 text-slate-500 border border-slate-700'}"
                    >
                      {selectedGenerationId === generation.id ? 'Selected' : 'View'}
                    </span>
                  </div>
                </button>
              </li>
            {/each}
          </ul>
        </div>
      </div>
    {/if}

    <!-- Selected Generation -->
    {#if selectedGeneration}
      <div class="border border-slate-800 rounded-lg overflow-hidden bg-slate-950">
        <div class="px-4 py-3 bg-slate-900 border-b border-slate-800">
          <div class="flex justify-between items-center gap-4">
            <div>
              <span class="text-xs uppercase tracking-wider text-slate-500 block">
                Selected Generation
              </span>

              <h3 class="font-semibold text-slate-200 mt-1">
                {selectedGeneration.file_type}
              </h3>
            </div>

            <span class="text-xs text-slate-500 shrink-0">
              {new Date(selectedGeneration.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        <pre class="p-4 text-xs leading-relaxed text-slate-400 overflow-auto max-h-96 whitespace-pre-wrap font-mono">{selectedGeneration.output_data}</pre>
      </div>
    {/if}

  </div>
</div>
