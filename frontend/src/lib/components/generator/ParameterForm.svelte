<script lang="ts">
  import { fade } from 'svelte/transition';
  import { computeCellWidth } from './cellWidth';

  interface Props {
    loading?: boolean;
    onGenerate: (payload: any) => void;
  }

  let { loading = false, onGenerate }: Props = $props();

  // Realistic engineering defaults for a 300x300mm solar panel setup
  let userId = $state('user_demo_123');
  let fileType = $state('Gcode');
  let cellCount = $state(40);
  let cellLength = $state(300.0);
  let originX = $state(0.0);
  let originY = $state(0.0);
  let speed = $state(15000.0);
  let scribingSpeed = $state(140.0);
  
  // Isolation (P1) settings
  let isolationEnabled = $state(true);
  let isolationSpacing = $state(1.0);

  // Bus Bars / P2 settings
  let p2Enabled = $state(true);
  let busBarClearance = $state(1.0); // Gap between each bus bar and its adjacent end cell. Same at both ends.
  let busBarWidth = $state(4.0);
  let passGap = $state(0.05);
  let passCount = $state(2);
  let initialOffset = $state(0.0);

  // Global Workspace & Panel settings
  let rotation = $state(0.0);
  let panelMaxSize = $state(300.0);
  let edgeMargin = $state(0.0); // Border kept clear of scribes on every side of the panel.

  // The cell width is never entered by hand. It is derived from the cell count so the cells (and the bus bars in P2)
  // always fit on the panel. The backend recomputes it with the same formula and is the source of truth.
  const countValid = $derived(Number.isInteger(Number(cellCount)) && Number(cellCount) >= 1);

  const cellWidth = $derived(
    computeCellWidth({
      cellCount: Number(cellCount),
      panelSize: Number(panelMaxSize),
      isP1: !p2Enabled,
      busBarWidth: Number(busBarWidth) || 0,
      p2BusSpacing: Number(busBarClearance) || 0,
      busBarSpacing: Number(busBarClearance) || 0,
      edgeMargin: Number(edgeMargin) || 0
    })
  );

  // Scribe lines longer than the panel (minus the edge margin on both sides) would run into the border or off the panel.
  const maxCellLength = $derived(Number(panelMaxSize) - 2 * (Number(edgeMargin) || 0));
  const cellLengthValid = $derived(Number(cellLength) > 0 && Number(cellLength) <= maxCellLength);

  const canGenerate = $derived(!loading && cellWidth !== null && cellLengthValid);

  function handleSubmit() {
    if (cellWidth === null || !cellLengthValid) return;

    const payload = {
      user_id: userId ? userId : null,
      file_type: fileType,
      
      // Cell Parameters
      cell_count: Number(cellCount),
      cell_width: cellWidth, // Derived. The backend recomputes this value.
      cell_length: Number(cellLength),
      origin_x: Number(originX),
      origin_y: Number(originY),

      // Isolation Pass / P1 Settings
      isolation_line_enabled: isolationEnabled,
      isolation_spacing: isolationEnabled ? Number(isolationSpacing) : 1.0,

      // Bus Bars & P2 Settings (matching PathGenerator expectations)
      is_p1: !p2Enabled,
      // One clearance value is applied to both ends so the layout is symmetric. The backend still takes two fields.
      bus_bar_spacing: p2Enabled ? Number(busBarClearance) : 0.0,
      p2_bus_spacing: p2Enabled ? Number(busBarClearance) : 0.0,
      bus_bar_width: p2Enabled ? Number(busBarWidth) : 0.0,
      pass_gap: Number(passGap),
      pass_count: Number(passCount),
      initial_offset: Number(initialOffset),

      // Laser Speeds
      speed: Number(speed),             // translation_speed
      scribing_speed: Number(scribingSpeed),

      // Workspace & Rotation
      rotation: Number(rotation),
      panel_max_size: Number(panelMaxSize),
      edge_margin: Number(edgeMargin) || 0,
      debug_mode: true
    };

    // --- DETAILED PAYLOAD LOGGING ---
    console.group("🚀 [GCode Form Submission Payload]");
    console.log("Timestamp:", new Date().toISOString());
    console.log("Raw Payload Object:", payload);
    console.log("Formatted JSON String:\n", JSON.stringify(payload, null, 2));
    console.groupEnd();
    // ---------------------------------

    onGenerate(payload);
  }
</script>

<div class="bg-slate-900/70 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm space-y-5">
  <h2 class="text-lg font-semibold text-slate-200 border-b border-slate-800 pb-2">Configuration Parameters</h2>

  <div class="space-y-4 text-sm">
    <div>
      <label for="user-id-input" class="block text-slate-400 mb-1">User ID / Context</label>
      <input id="user-id-input" type="text" bind:value={userId} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
    </div>

    <div>
      <label for="file-type-select" class="block text-slate-400 mb-1">Output Format</label>
      <select id="file-type-select" bind:value={fileType} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500">
        <option value="Gcode">Gcode (.gcode)</option>
        <option value="TXT">Plain Text (.txt)</option>
        <option value="SVG">Scalable Vector Graphic (.svg)</option>
      </select>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label for="cell-count-input" class="block text-slate-400 mb-1">Cell Count</label>
        <input id="cell-count-input" type="number" min="1" step="1" bind:value={cellCount} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
      </div>
      <div>
        <label for="speed-input" class="block text-slate-400 mb-1">Translation Speed (mm/min)</label>
        <input id="speed-input" type="number" step="100" bind:value={speed} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label for="cell-width-input" class="block text-slate-400 mb-1">Cell Width (mm) <span class="text-slate-500">· auto</span></label>
        <input
          id="cell-width-input"
          type="text"
          readonly
          tabindex="-1"
          value={cellWidth === null ? '—' : cellWidth.toFixed(3)}
          class="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-400 cursor-not-allowed focus:outline-none"
        />
      </div>
      <div>
        <label for="cell-length-input" class="block text-slate-400 mb-1">Cell Length (mm)</label>
        <input id="cell-length-input" type="number" step="0.5" bind:value={cellLength} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
      </div>
    </div>

    {#if !cellLengthValid}
      <p class="text-xs text-red-400 -mt-2">Cell length must be greater than 0 and no more than {maxCellLength} mm (the panel minus the edge margins).</p>
    {/if}

    {#if cellWidth !== null}
      <p class="text-xs text-slate-500 -mt-2">
        {Number(cellCount)} cells × {cellWidth.toFixed(3)} mm = {(Number(cellCount) * cellWidth).toFixed(3)} mm of the {Number(panelMaxSize)} mm panel
      </p>
    {:else if !countValid}
      <p class="text-xs text-red-400 -mt-2">Enter a whole number of cells (1 or more).</p>
    {:else}
      <p class="text-xs text-red-400 -mt-2">The edge margin and bus bars don't fit on the panel. Reduce the edge margin, bus bar clearance or bus bar width.</p>
    {/if}

    <div>
      <label for="edge-margin-input" class="block text-slate-400 mb-1">Edge Margin (mm)</label>
      <input id="edge-margin-input" type="number" min="0" step="1" bind:value={edgeMargin} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
      <p class="text-xs text-slate-500 mt-1">Border kept clear of scribes on every side of the panel.</p>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label for="origin-x-input" class="block text-slate-400 mb-1">Origin X</label>
        <input id="origin-x-input" type="number" step="0.1" bind:value={originX} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
      </div>
      <div>
        <label for="origin-y-input" class="block text-slate-400 mb-1">Origin Y</label>
        <input id="origin-y-input" type="number" step="0.1" bind:value={originY} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
      </div>
    </div>

    <!-- Isolation Pass (P1) Section -->
    <div class="pt-2 border-t border-slate-800 space-y-3">
      <div class="flex items-center space-x-3">
        <input type="checkbox" id="isolation" bind:checked={isolationEnabled} class="w-4 h-4 accent-indigo-500 bg-slate-950 border-slate-700 rounded" />
        <label for="isolation" class="text-slate-300 cursor-pointer">Enable Isolation Pass</label>
      </div>

      {#if isolationEnabled}
        <div transition:fade={{ duration: 150 }}>
          <label for="isolation-spacing-input" class="block text-slate-400 mb-1">Isolation Spacing (mm)</label>
          <input id="isolation-spacing-input" type="number" step="0.1" bind:value={isolationSpacing} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
        </div>
      {/if}
    </div>

    <!-- Bus Bars / Cell Scribing (P2) Section -->
    <div class="pt-2 border-t border-slate-800 space-y-3">
      <div class="flex items-center space-x-3">
        <input type="checkbox" id="p2-enabled" bind:checked={p2Enabled} class="w-4 h-4 accent-indigo-500 bg-slate-950 border-slate-700 rounded" />
        <label for="p2-enabled" class="text-slate-300 cursor-pointer">Enable Bus Bars / Cell Scribing (P2)</label>
      </div>

      {#if p2Enabled}
        <div class="grid grid-cols-2 gap-3" transition:fade={{ duration: 150 }}>
          <div>
            <label for="bus-bar-spacing" class="block text-slate-400 mb-1">Bus Bar Clearance (mm)</label>
            <input id="bus-bar-spacing" type="number" min="0" step="0.5" bind:value={busBarClearance} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
          </div>
          <div>
            <label for="bus-bar-width" class="block text-slate-400 mb-1">Bus Bar Width (mm)</label>
            <input id="bus-bar-width" type="number" min="0" step="0.1" bind:value={busBarWidth} class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500" />
          </div>
        </div>
      {/if}
    </div>
  </div>

  <button 
    onclick={handleSubmit} 
    disabled={!canGenerate}
    class="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold py-2.5 rounded-lg transition shadow-lg shadow-indigo-600/20 cursor-pointer disabled:cursor-not-allowed">
    {loading ? 'Generating G-Code...' : 'Generate Output'}
  </button>
</div>