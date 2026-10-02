<script lang="ts">
  let { 
    params = $bindable(), 
    simulationMode = $bindable(), 
    batchConfig = $bindable(), 
    loading = false, 
    errorMessage = '', 
    onRun 
  } = $props();

  let validationError = $derived.by(() => {
    if (simulationMode === 'history') return ''; // No form validation needed in history view

    const deadWidth = params.P1_width + params["P1-P2"] + params.P2_width + params["P2-P3"] + params.P3_width;
    const cellPitch = params.Cell_width + deadWidth;
    const calculatedCells = Math.floor((params.module_width - 2 * params.margin_lr) / cellPitch);

    if (params.module_width <= 0 || params.module_length <= 0) return "Module width and length must be greater than zero.";
    if (params.margin_lr < 0 || params.margin_ud < 0) return "Margins cannot be negative.";
    if (params.Cell_width <= 0) return "Cell width must be greater than zero.";
    if (cellPitch <= 0) return "Total scribe/cell pitch must be greater than zero.";
    if (calculatedCells <= 0) return `Invalid geometry: Calculated cells is ${calculatedCells}.`;
    if (params.light_intensity <= 0) return "Light intensity must be greater than zero.";
    if (params.IV_points <= 1) return "IV points must be greater than 1.";
    if (simulationMode === 'batch' && batchConfig.num_simulations < 1) return "Number of simulations must be at least 1.";
    return '';
  });
</script>

<div class="bg-white p-6 rounded-lg shadow-md border border-gray-200 space-y-6 max-h-[125vh] overflow-y-auto">
  <div class="flex justify-between items-center">
    <h2 class="text-xl font-semibold">Module Parameters</h2>
    <div class="inline-flex rounded-lg border border-gray-200 bg-gray-100 p-1">
      <button 
        class="px-2.5 py-1 text-xs font-medium rounded-md transition {simulationMode === 'single' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'}"
        onclick={() => simulationMode = 'single'}
      >Single</button>
      <button 
        class="px-2.5 py-1 text-xs font-medium rounded-md transition {simulationMode === 'batch' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'}"
        onclick={() => simulationMode = 'batch'}
      >Batch</button>
      <button 
        class="px-2.5 py-1 text-xs font-medium rounded-md transition {simulationMode === 'history' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'}"
        onclick={() => simulationMode = 'history'}
      >History</button>
    </div>
  </div>

  {#if simulationMode === 'batch'}
    <div class="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <h3 class="text-sm font-bold text-blue-700 uppercase tracking-wider">Batch Sweep Options</h3>
      <div>
        <label for="target-var" class="block text-xs font-medium text-gray-700">Target Variable</label>
        <select id="target-var" bind:value={batchConfig.target_variable} class="w-full border rounded p-1.5 text-sm bg-white font-medium text-emerald-700">
          <option value="Cell_width">Cell Width</option>
          <option value="light_intensity">Light Intensity</option>
          <option value="sheet_ohm">Sheet Resistance</option>
          <option value="shunt">Shunt Resistance</option>
          <option value="Intrinsic_series">Intrinsic Series Resistance</option>
        </select>
      </div>
      <div>
        <label for="step-size" class="block text-xs font-medium text-gray-700">Step Size</label>
        <input id="step-size" type="number" step="0.1" bind:value={batchConfig.step_size} class="w-full border rounded p-1 text-sm bg-white" />
      </div>
      <div>
        <label for="num-sims" class="block text-xs font-medium text-gray-700">Number of Simulations</label>
        <input id="num-sims" type="number" min="1" max="100" bind:value={batchConfig.num_simulations} class="w-full border rounded p-1 text-sm bg-white" />
      </div>
    </div>
  {:else if simulationMode === 'history'}
    <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
      <p class="font-medium text-gray-800 mb-1">Archived Batch History</p>
      <p class="text-xs">Browse past batch sweep records stored in Supabase. Select a run from the history dashboard to inspect its overlayed I-V curves and performance peaks.</p>
    </div>
  {/if}

  {#if simulationMode !== 'history'}
    <!-- General Parameters -->
    <div class="space-y-3">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider">General</h3>
      <div>
        <label for="light-intensity" class="text-xs font-medium text-gray-700 block">Light Intensity (mW/cm²): {params.light_intensity}</label>
        <input id="light-intensity" type="range" min="100" max="1200" step="10" bind:value={params.light_intensity} class="w-full" />
      </div>
      <div>
        <label for="iv-points" class="block text-xs font-medium text-gray-700">IV Points</label>
        <input id="iv-points" type="number" bind:value={params.IV_points} class="w-full border rounded p-1 text-sm" />
      </div>
    </div>

    <!-- Module Dimensions -->
    <div class="space-y-3 pt-2 border-t border-gray-100">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider">Module Dimensions</h3>
      <div>
        <label for="mod-width" class="block text-xs font-medium text-gray-700">Module Width (mm)</label>
        <input id="mod-width" type="number" step="0.1" bind:value={params.module_width} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="mod-length" class="block text-xs font-medium text-gray-700">Module Length (mm)</label>
        <input id="mod-length" type="number" step="0.1" bind:value={params.module_length} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="margin-lr" class="block text-xs font-medium text-gray-700">Margin Left/Right (mm)</label>
        <input id="margin-lr" type="number" step="0.1" bind:value={params.margin_lr} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="margin-ud" class="block text-xs font-medium text-gray-700">Margin Up/Down (mm)</label>
        <input id="margin-ud" type="number" step="0.1" bind:value={params.margin_ud} class="w-full border rounded p-1 text-sm" />
      </div>
    </div>

    <!-- Scribes & Cell Geometry -->
    <div class="space-y-3 pt-2 border-t border-gray-100">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider">Scribe & Cell Geometry</h3>
      <div>
        <label for="cell-width" class="block text-xs font-medium text-gray-700">Cell Width (mm)</label>
        <input id="cell-width" type="number" step="0.1" bind:value={params.Cell_width} class="w-full border rounded p-1 text-sm bg-white" />
      </div>
      <div>
        <label for="p1-width" class="block text-xs font-medium text-gray-700">P1 Width (mm)</label>
        <input id="p1-width" type="number" step="0.01" bind:value={params.P1_width} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="p1-p2" class="block text-xs font-medium text-gray-700">P1-P2 Gap (mm)</label>
        <input id="p1-p2" type="number" step="0.01" bind:value={params["P1-P2"]} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="p2-width" class="block text-xs font-medium text-gray-700">P2 Width (mm)</label>
        <input id="p2-width" type="number" step="0.01" bind:value={params.P2_width} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="p2-p3" class="block text-xs font-medium text-gray-700">P2-P3 Gap (mm)</label>
        <input id="p2-p3" type="number" step="0.01" bind:value={params["P2-P3"]} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="p3-width" class="block text-xs font-medium text-gray-700">P3 Width (mm)</label>
        <input id="p3-width" type="number" step="0.01" bind:value={params.P3_width} class="w-full border rounded p-1 text-sm" />
      </div>
    </div>

    <!-- Resistances -->
    <div class="space-y-3 pt-2 border-t border-gray-100">
      <h3 class="text-sm font-bold text-gray-500 uppercase tracking-wider">Resistances & Contacts</h3>
      <div>
        <label for="sheet-ohm" class="block text-xs font-medium text-gray-700">Sheet Resistance (Ω/sq)</label>
        <input id="sheet-ohm" type="number" step="0.1" bind:value={params.sheet_ohm} class="w-full border rounded p-1 text-sm bg-white" />
      </div>
      <div>
        <label for="carbon-ohm" class="block text-xs font-medium text-gray-700">Carbon Resistance (Ω)</label>
        <input id="carbon-ohm" type="number" step="0.1" bind:value={params.carbon_ohm} class="w-full border rounded p-1 text-sm" />
      </div>
      <div>
        <label for="shunt" class="block text-xs font-medium text-gray-700">Shunt Resistance (Ω·cm²)</label>
        <input id="shunt" type="number" step="1" bind:value={params.shunt} class="w-full border rounded p-1 text-sm bg-white" />
      </div>
      <div>
        <label for="int-series" class="block text-xs font-medium text-gray-700">Intrinsic Series Resistance</label>
        <input id="int-series" type="number" step="0.01" bind:value={params.Intrinsic_series} class="w-full border rounded p-1 text-sm bg-white" />
      </div>
    </div>

    <button 
      onclick={onRun}
      class="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 transition sticky bottom-0 shadow-lg disabled:bg-gray-400 disabled:cursor-not-allowed"
      disabled={loading || !!validationError}
    >
      {loading ? 'Simulating...' : simulationMode === 'single' ? 'Run Simulation' : 'Run Batch Sweep'}
    </button>
  {/if}

  {#if validationError}
    <p class="text-amber-600 text-sm mt-2 font-medium">⚠️ {validationError}</p>
  {:else if errorMessage}
    <p class="text-red-500 text-sm mt-2">{errorMessage}</p>
  {/if}
</div>