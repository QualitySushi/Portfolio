<script lang="ts">
  import type { Snippet } from 'svelte';

  let { 
    voltages = [], 
    currents = [], 
    maxV = 1, 
    maxI = 1, 
    batchRuns = null, 
    bestBatchIndex = -1, 
    inspectedBatchIndex = -1,
    onSelectRun = (idx: number) => {},
    header
} = $props<{
  voltages?: number[];
  currents?: number[];
  maxV?: number;
  maxI?: number;
  batchRuns?: any;
  bestBatchIndex?: number;
  inspectedBatchIndex?: number;
  onSelectRun?: (idx: number) => void;
  header?: Snippet;
}>();

  let zoomScale = $state(1);
  let panX = $state(0);
  let panY = $state(0);
  let isDragging = $state(false);
  let startX = $state(0);
  let startY = $state(0);

  function handleMouseDown(e: MouseEvent) {
    isDragging = true;
    startX = e.clientX - panX;
    startY = e.clientY - panY;
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isDragging) return;
    panX = e.clientX - startX;
    panY = e.clientY - startY;
  }

  function handleMouseUp() {
    isDragging = false;
  }

  function handleWheel(e: WheelEvent) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    zoomScale = Math.min(Math.max(zoomScale * zoomFactor, 1), 10);
    if (zoomScale === 1) {
      panX = 0;
      panY = 0;
    }
  }

  function resetZoom() {
    zoomScale = 1;
    panX = 0;
    panY = 0;
  }

  function getSvgPoints(vArr: number[], iArr: number[], width: number, height: number, mVolt: number, mCurr: number) {
    if (!vArr || !iArr || vArr.length === 0) return '';
    return vArr.map((v, i) => {
      const x = (v / mVolt) * width;
      const y = height - (iArr[i] / mCurr) * height;
      return `${x},${y}`;
    }).join(' ');
  }
</script>

<div class="p-4 bg-gray-50 rounded border space-y-3">
  <div class="flex justify-between items-center">
    {#if header}
      {@render header()}
    {:else}
      <h3 class="font-medium text-gray-700">Current - Voltage (I-V) Curve</h3>
    {/if}
    <div class="flex items-center space-x-2">
      <span class="text-xs text-gray-500">Zoom: {Math.round(zoomScale * 100)}% | Scroll to zoom, drag to pan</span>
      {#if zoomScale > 1}
        <button onclick={resetZoom} class="text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded text-gray-700 transition">Reset Zoom</button>
      {/if}
    </div>
  </div>

  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div 
    class="w-full h-72 bg-white border rounded p-2 relative overflow-hidden cursor-grab active:cursor-grabbing select-none"
    onmousedown={handleMouseDown}
    onmousemove={handleMouseMove}
    onmouseup={handleMouseUp}
    onmouseleave={handleMouseUp}
    onwheel={handleWheel}
  >
    <svg 
      viewBox="0 0 500 250" 
      class="w-full h-full overflow-visible transition-transform duration-75 ease-out"
      style="transform: scale({zoomScale}) translate({panX / zoomScale}px, {panY / zoomScale}px); transform-origin: top left;"
    >
      <line x1="0" y1="0" x2="500" y2="0" stroke="#e5e7eb" stroke-dasharray="4" />
      <line x1="0" y1="125" x2="500" y2="125" stroke="#e5e7eb" stroke-dasharray="4" />
      <line x1="0" y1="250" x2="500" y2="250" stroke="#e5e7eb" />
      <line x1="0" y1="0" x2="0" y2="250" stroke="#e5e7eb" />

      {#if batchRuns}
        <!-- Multi-curve batch rendering -->
        {#each batchRuns as run, idx}
          {#if idx !== bestBatchIndex}
            {@const colorOpacity = 0.2 + (idx / batchRuns.length) * 0.5}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <g onclick={() => onSelectRun(idx)} class="cursor-pointer">
              <polyline
                fill="none"
                stroke={idx === inspectedBatchIndex ? '#2563eb' : '#9ca3af'}
                stroke-opacity={idx === inspectedBatchIndex ? 1 : colorOpacity}
                stroke-width={idx === inspectedBatchIndex ? 2.5 : 1.5}
                points={getSvgPoints(run.iv_curve.voltage, run.iv_curve.current, 500, 250, maxV, maxI)}
              />
            </g>
          {/if}
        {/each}

        {#if bestBatchIndex !== -1}
          {@const bestRun = batchRuns[bestBatchIndex]}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <g onclick={() => onSelectRun(bestBatchIndex)} class="cursor-pointer">
            <polyline
              fill="none"
              stroke="#059669"
              stroke-width="3.5"
              class="drop-shadow-md"
              points={getSvgPoints(bestRun.iv_curve.voltage, bestRun.iv_curve.current, 500, 250, maxV, maxI)}
            />
          </g>
        {/if}
      {:else}
        <!-- Single curve rendering -->
        <polyline
          fill="none"
          stroke="#2563eb"
          stroke-width="3"
          points={getSvgPoints(voltages, currents, 500, 250, maxV, maxI)}
        />
      {/if}
    </svg>
  </div>
  <div class="flex justify-between text-xs text-gray-500 px-1">
    <span>0 V</span>
    <span>Max Voltage ({maxV.toFixed(2)}V)</span>
  </div>
</div>