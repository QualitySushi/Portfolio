<script lang="ts">
  import SimulationForm from '../../lib/components/estimator/SimulationForm.svelte';
  import SingleResults from '../../lib/components/estimator/SingleResults.svelte';
  import BatchResults from '../../lib/components/estimator/BatchResults.svelte';
  import BatchHistoryView from '../../lib/components/estimator/BatchHistoryView.svelte';

  // Dynamic base URL supporting local dev and Vercel production deployment
  const API_BASE = import.meta.env.PUBLIC_API_URL 
    ? `${import.meta.env.PUBLIC_API_URL}/api/estimator` 
    : 'http://localhost:4000/api/estimator';

  let simulationMode = $state<'single' | 'batch' | 'history'>('single');
  let params = $state({
    module_width: 100.0,
    module_length: 300.0,
    margin_lr: 5.0,
    margin_ud: 5.0,
    P1_width: 0.2,
    Cell_width: 10.0,
    "P1-P2": 0.1,
    P2_width: 0.2,
    "P2-P3": 0.1,
    P3_width: 0.2,
    sheet_ohm: 15.0,
    carbon_ohm: 20.0,
    shunt: 1000.0,
    Intrinsic_series: 0.1,
    Jsc_norm: 25.0,
    dark_sat_norm: 1e-9,
    V_th: 0.02585,
    n_ideal: 1.5,
    rho_contact: 0.001,
    light_intensity: 1000.0,
    IV_points: 100
  });

  let batchConfig = $state({
    target_variable: 'Cell_width',
    step_size: 0.5,
    num_simulations: 10
  });

  let results = $state<any>(null);
  let batchResults = $state<any>(null);
  let historicalRunData = $state<any>(null);
  let loading = $state(false);
  let errorMessage = $state('');

  async function handleSelectHistoricalRun(runId: string) {
    loading = true;
    errorMessage = '';
    try {
      const res = await fetch(`${API_BASE}/batch-jobs/${runId}`);
      if (!res.ok) throw new Error(await res.text());
      historicalRunData = $state.snapshot(await res.json());
      batchResults = historicalRunData;
      simulationMode = 'batch';
    } catch (err: unknown) {
      errorMessage = err instanceof Error ? err.message : 'Failed to load historical run';
    } finally {
      loading = false;
    }
  }

  async function handleSaveBatchRun() {
    if (!batchResults) return;
    
    const payload = {
      target_variable: batchConfig.target_variable,
      ...batchResults
    };

    const res = await fetch(`${API_BASE}/batch-jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(await res.text());
    }
  }

  async function handleRun() {
    loading = true;
    errorMessage = '';
    
    if (simulationMode === 'single') {
      batchResults = null;
      try {
        const res = await fetch(`${API_BASE}/simulate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params)
        });
        if (!res.ok) throw new Error(await res.text());
        results = $state.snapshot(await res.json());
      } catch (err: unknown) {
        errorMessage = err instanceof Error ? err.message : 'Simulation failed';
      } finally {
        loading = false;
      }
    } else if (simulationMode === 'batch') {
      results = null;
      try {
        const payload = {
          base_params: params,
          target_variable: batchConfig.target_variable,
          step_size: Number(batchConfig.step_size),
          num_simulations: Number(batchConfig.num_simulations)
        };
        const res = await fetch(`${API_BASE}/batch-simulate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        batchResults = $state.snapshot(await res.json());
      } catch (err: unknown) {
        errorMessage = err instanceof Error ? err.message : 'Batch simulation failed';
      } finally {
        loading = false;
      }
    }
  }
</script>

<main class="max-w-7xl mx-auto px-4 py-8 text-gray-800">
  <div class="mb-6">
    <h1 class="text-3xl font-bold mb-2">Efficiency Estimator Playground</h1>
    <p class="text-gray-600">Simulate photovoltaic cells, run batch sweeps, and review historical runs.</p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
    <div class="lg:col-span-1">
      <SimulationForm 
        bind:params 
        bind:simulationMode 
        bind:batchConfig 
        {loading} 
        {errorMessage} 
        onRun={handleRun} 
      />
    </div>

    <div class="lg:col-span-2">
      {#if simulationMode === 'single'}
        <SingleResults {results} />
      {:else if simulationMode === 'batch'}
        <BatchResults 
          {batchResults} 
          {batchConfig} 
          onSave={handleSaveBatchRun} 
        />
      {:else if simulationMode === 'history'}
        <BatchHistoryView onSelectRun={handleSelectHistoricalRun} />
      {/if}
    </div>
  </div>
</main>