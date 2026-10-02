<script lang="ts">
  import IVCurveGraph from './IVCurveGraph.svelte';

  let { results } = $props();

  let maxV = $derived(results?.iv_curve?.voltage ? Math.max(...results.iv_curve.voltage, 1) : 1);
  let maxI = $derived(results?.iv_curve?.current ? Math.max(...results.iv_curve.current, 1) : 1);
</script>

<div class="bg-white p-6 rounded-lg shadow-md border border-gray-200 space-y-6">
  <h2 class="text-xl font-semibold">Simulation Metrics</h2>

  {#if results}
    <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
      <div class="bg-gray-50 p-3 rounded border">
        <p class="text-xs text-gray-500">Isc (Short Circuit)</p>
        <p class="text-base font-bold text-gray-800">{results.metrics.i_sc.toFixed(5)} A</p>
      </div>
      <div class="bg-gray-50 p-3 rounded border">
        <p class="text-xs text-gray-500">Voc (Open Circuit)</p>
        <p class="text-base font-bold text-gray-800">{results.metrics.v_oc.toFixed(5)} V</p>
      </div>
      <div class="bg-gray-50 p-3 rounded border">
        <p class="text-xs text-gray-500">Pmp (Max Power)</p>
        <p class="text-base font-bold text-gray-800">{results.metrics.Pmp?.toFixed(5) ?? 'N/A'} W</p>
      </div>
      <div class="bg-gray-50 p-3 rounded border">
        <p class="text-xs text-gray-500">Imp (Max Current)</p>
        <p class="text-base font-bold text-gray-800">{results.metrics.Imp?.toFixed(5) ?? 'N/A'} A</p>
      </div>
      <div class="bg-gray-50 p-3 rounded border">
        <p class="text-xs text-gray-500">Vmp (Max Voltage)</p>
        <p class="text-base font-bold text-gray-800">{results.metrics.Vmp?.toFixed(5) ?? 'N/A'} V</p>
      </div>
      <div class="bg-gray-50 p-3 rounded border">
        <p class="text-xs text-gray-500">Fill Factor (FF)</p>
        <p class="text-base font-bold text-gray-800">{results.metrics.FF_pct.toFixed(2)}%</p>
      </div>
      <div class="bg-blue-50 p-3 rounded border border-blue-200">
        <p class="text-xs text-blue-600 font-medium">Aperture Efficiency</p>
        <p class="text-lg font-bold text-blue-700">{results.metrics.Aperture_Efficiency_pct?.toFixed(3) ?? results.metrics.Efficiency_pct.toFixed(3)}%</p>
      </div>
      <div class="bg-emerald-50 p-3 rounded border border-emerald-200 col-span-2">
        <p class="text-xs text-emerald-600 font-medium">Active Area Efficiency</p>
        <p class="text-lg font-bold text-emerald-700">{results.metrics.Active_Area_Efficiency_pct?.toFixed(3) ?? 'N/A'}%</p>
      </div>
    </div>

    <IVCurveGraph 
      voltages={results.iv_curve.voltage} 
      currents={results.iv_curve.current} 
      {maxV} 
      {maxI} 
    />
  {:else}
    <p class="text-gray-500">Adjust parameters and run a simulation to see output metrics and visualization.</p>
  {/if}
</div>