<script lang="ts">
  import IVCurveGraph from './IVCurveGraph.svelte';

  let { 
    batchResults, 
    batchConfig,
    onSave = () => {} 
  } = $props<{
    batchResults?: any;
    batchConfig?: any;
    onSave?: () => void;
  }>();

  let selectedBatchIndex = $state<number | null>(null);
  let saving = $state(false);
  let savedSuccess = $state(false);

  let allBatchVoltages = $derived(batchResults?.batch_results ? batchResults.batch_results.flatMap((r: any) => r.iv_curve.voltage) : []);
  let allBatchCurrents = $derived(batchResults?.batch_results ? batchResults.batch_results.flatMap((r: any) => r.iv_curve.current) : []);
  let batchMaxV = $derived(Math.max(...allBatchVoltages, 1));
  let batchMaxI = $derived(Math.max(...allBatchCurrents, 1));

  let bestBatchIndex = $derived.by(() => {
    if (!batchResults?.batch_results || batchResults.batch_results.length === 0) return -1;
    let bestIdx = 0;
    let maxEff = -1;
    batchResults.batch_results.forEach((run: any, idx: number) => {
      const eff = run.metrics?.Aperture_Efficiency_pct ?? run.metrics?.Efficiency_pct ?? 0;
      if (eff > maxEff) {
        maxEff = eff;
        bestIdx = idx;
      }
    });
    return bestIdx;
  });

  let inspectedBatchIndex = $derived(selectedBatchIndex !== null ? selectedBatchIndex : bestBatchIndex);
  let inspectedBatchItem = $derived(batchResults?.batch_results?.[inspectedBatchIndex] ?? null);

  async function handleSaveClick() {
    saving = true;
    savedSuccess = false;
    try {
      await onSave();
      savedSuccess = true;
      setTimeout(() => { savedSuccess = false; }, 3000);
    } catch (err) {
      console.error('Failed to save batch results', err);
    } finally {
      saving = false;
    }
  }
</script>

<div class="bg-white p-6 rounded-lg shadow-md border border-gray-200 space-y-6">
  <div class="flex justify-between items-center border-b pb-4">
    <h2 class="text-xl font-semibold">Batch Sweep Results</h2>
    
    {#if batchResults && batchResults.batch_results}
      <button
        onclick={handleSaveClick}
        disabled={saving}
        class="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium px-4 py-2 rounded-lg transition flex items-center gap-2 shadow-sm"
      >
        {#if saving}
          <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-25" cx="12" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          Saving...
        {:else if savedSuccess}
          ✓ Saved Successfully!
        {:else}
          💾 Save to Database
        {/if}
      </button>
    {/if}
  </div>

  {#if batchResults && batchResults.batch_results}
    <div class="space-y-6">
      <div class="flex items-center space-x-3">
        <h3 class="font-medium text-gray-700">Overlaid I-V Curves ({batchResults.batch_results.length} runs)</h3>
        {#if bestBatchIndex !== -1}
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-300">
            ✨ Best: {(batchResults.batch_results[bestBatchIndex].metrics.Aperture_Efficiency_pct ?? batchResults.batch_results[bestBatchIndex].metrics.Efficiency_pct).toFixed(2)}%
          </span>
        {/if}
      </div>

      <IVCurveGraph 
        batchRuns={batchResults.batch_results} 
        voltages={allBatchVoltages}
        currents={allBatchCurrents}
        maxV={batchMaxV} 
        maxI={batchMaxI} 
        {bestBatchIndex} 
        {inspectedBatchIndex} 
        onSelectRun={(idx: number) => selectedBatchIndex = idx}
      />

      {#if inspectedBatchItem}
        <div class="p-4 bg-blue-50/60 border border-blue-200 rounded-lg space-y-3">
          <div class="flex justify-between items-center">
            <h3 class="text-sm font-bold text-blue-800">
              Inspection: Run {inspectedBatchItem.iteration + 1} ({batchConfig?.target_variable ?? 'Parameter'} = {inspectedBatchItem.parameter_value.toFixed(3)})
            </h3>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-2.5 text-sm">
            <div class="bg-white p-2.5 rounded border">
              <span class="text-[11px] text-gray-500 block">Pmp</span>
              <span class="font-bold">{inspectedBatchItem.metrics.Pmp?.toFixed(5) ?? 'N/A'} W</span>
            </div>
            <div class="bg-white p-2.5 rounded border">
              <span class="text-[11px] text-gray-500 block">Aperture Eff.</span>
              <span class="font-bold text-blue-600">{(inspectedBatchItem.metrics.Aperture_Efficiency_pct ?? inspectedBatchItem.metrics.Efficiency_pct).toFixed(3)}%</span>
            </div>
            <div class="bg-white p-2.5 rounded border">
              <span class="text-[11px] text-gray-500 block">Voc / Isc</span>
              <span class="font-bold">{inspectedBatchItem.metrics.v_oc.toFixed(2)}V / {inspectedBatchItem.metrics.i_sc.toFixed(2)}A</span>
            </div>
            <div class="bg-white p-2.5 rounded border">
              <span class="text-[11px] text-gray-500 block">Fill Factor</span>
              <span class="font-bold">{inspectedBatchItem.metrics.FF_pct.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      {/if}

      <!-- Table -->
      <div class="border rounded-lg overflow-hidden max-h-80 overflow-y-auto">
        <table class="w-full text-left border-collapse text-sm">
          <thead class="bg-gray-100 text-gray-600 uppercase text-xs sticky top-0">
            <tr>
              <th class="p-3">#</th>
              <th class="p-3">{batchConfig?.target_variable ?? 'Target'}</th>
              <th class="p-3">Aperture Eff.</th>
              <th class="p-3">Pmp (W)</th>
              <th class="p-3">Voc (V)</th>
              <th class="p-3">Isc (A)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            {#each batchResults.batch_results as item, idx}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
              <tr 
                onclick={() => selectedBatchIndex = idx}
                class="cursor-pointer transition hover:bg-blue-50/50 {idx === inspectedBatchIndex ? 'bg-blue-100/60 font-medium' : idx === bestBatchIndex ? 'bg-emerald-50/60' : ''}"
              >
                <td class="p-3 text-gray-500">#{item.iteration + 1}</td>
                <td class="p-3 font-medium">{item.parameter_value.toFixed(3)}</td>
                <td class="p-3 font-semibold text-blue-600">{(item.metrics.Aperture_Efficiency_pct ?? item.metrics.Efficiency_pct).toFixed(2)}%</td>
                <td class="p-3">{item.metrics.Pmp?.toFixed(3) ?? 'N/A'}</td>
                <td class="p-3">{item.metrics.v_oc.toFixed(3)}</td>
                <td class="p-3">{item.metrics.i_sc.toFixed(3)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else}
    <p class="text-gray-500 py-4">Configure your batch sweep options and run the batch simulation.</p>
  {/if}
</div>