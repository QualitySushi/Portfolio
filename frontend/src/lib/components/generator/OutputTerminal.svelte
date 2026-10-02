<script lang="ts">
  import { fade } from 'svelte/transition';

  interface Props {
    outputResult?: string;
    errorMessage?: string;
    loading?: boolean;
  }

  let { outputResult = '', errorMessage = '', loading = false }: Props = $props();

  let copied = $state(false);

  function copyToClipboard() {
    if (!outputResult) return;
    navigator.clipboard.writeText(outputResult);
    copied = true;
    setTimeout(() => { copied = false; }, 2000);
  }
</script>

<div class="flex flex-col bg-slate-900/70 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm h-full">
  <div class="flex justify-between items-center border-b border-slate-800 pb-2 mb-4">
    <h2 class="text-lg font-semibold text-slate-200">Execution Output</h2>
    {#if outputResult}
      <button 
        onclick={copyToClipboard}
        class="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-md text-indigo-300 transition cursor-pointer">
        {copied ? 'Copied to Clipboard!' : 'Copy Code'}
      </button>
    {/if}
  </div>

  {#if errorMessage}
    <div transition:fade class="bg-red-950/80 border border-red-800 text-red-200 p-4 rounded-lg mb-4 text-sm">
      <strong>Error:</strong> {errorMessage}
    </div>
  {/if}

  <div class="flex-1 bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-emerald-400 overflow-y-auto max-h-125 min-h-87.5 shadow-inner select-all">
    {#if loading}
      <div class="flex items-center justify-center h-full text-slate-500 animate-pulse">
        Processing request through microservice pipeline...
      </div>
    {:else if outputResult}
      <pre class="whitespace-pre-wrap">{outputResult}</pre>
    {:else}
      <div class="flex items-center justify-center h-full text-slate-600">
        Configure parameters on the left and click "Generate Output" to inspect results.
      </div>
    {/if}
  </div>
</div>