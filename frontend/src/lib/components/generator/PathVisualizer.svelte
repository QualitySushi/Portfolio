<script lang="ts">
  let { outputResult }: { outputResult: any } = $props();

  let canvas: HTMLCanvasElement;

  interface PathNodePoint {
    x: number;
    y: number;
  }

  interface PathNode {
    pos: PathNodePoint;
    beam_state: boolean;
    approach_speed: number;
    line_type: 'isolation' | 'cell' | 'bus_bar';
  }

  // Viewport transformation states (Svelte 5 runes)
  let zoom = $state(1);
  let panX = $state(0);
  let panY = $state(0);
  let isDragging = $state(false);
  let startMouseX = $state(0);
  let startMouseY = $state(0);

  // Reset view when output changes
  $effect(() => {
    if (outputResult) {
      zoom = 1;
      panX = 0;
      panY = 0;
    }
  });

  $effect(() => {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGridBackground(ctx, canvas.width, canvas.height);

    if (!outputResult) {
      drawPlaceholder(ctx, canvas.width, canvas.height);
      return;
    }

    plotPathData(ctx, outputResult, canvas.width, canvas.height);
  });

  function handleMouseDown(e: MouseEvent) {
    if (e.button !== 0) return; // Only left click
    isDragging = true;
    startMouseX = e.clientX - panX;
    startMouseY = e.clientY - panY;
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isDragging) return;
    panX = e.clientX - startMouseX;
    panY = e.clientY - startMouseY;
    triggerRedraw();
  }

  function handleMouseUp() {
    isDragging = false;
  }

  function handleWheel(e: WheelEvent) {
    e.preventDefault();
    const zoomFactor = 1.1;
    if (e.deltaY < 0) {
      zoom *= zoomFactor;
    } else {
      zoom /= zoomFactor;
    }
    // Clamp zoom between 0.1x and 50x
    zoom = Math.max(0.1, Math.min(50, zoom));
    triggerRedraw();
  }

  function resetView() {
    zoom = 1;
    panX = 0;
    panY = 0;
    triggerRedraw();
  }

  function triggerRedraw() {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawGridBackground(ctx, canvas.width, canvas.height);
    if (!outputResult) {
      drawPlaceholder(ctx, canvas.width, canvas.height);
      return;
    }
    plotPathData(ctx, outputResult, canvas.width, canvas.height);
  }

  function drawGridBackground(ctx: CanvasRenderingContext2D, width: number, height: number) {
    ctx.fillStyle = '#020617';
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;

    const step = 40;
    for (let x = 0; x < width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
  }

  function drawPlaceholder(ctx: CanvasRenderingContext2D, width: number, height: number) {
    ctx.fillStyle = '#64748b';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Awaiting Path Generation Preview...', width / 2, height / 2);
  }

  function plotPathData(ctx: CanvasRenderingContext2D, data: any, width: number, height: number) {
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      data = data.output || data.data || data.result || data;
    }

    let nodes: PathNode[] = [];

    if (Array.isArray(data)) {
      nodes = data;
    } else if (typeof data === 'string') {
      if (data.trim() === '') return;
      try {
        const parsed = JSON.parse(data);
        if (Array.isArray(parsed)) {
          nodes = parsed;
        } else if (typeof parsed === 'object' && parsed !== null) {
          nodes = parsed.nodes || parsed.path_nodes || parsed.data || parsed.result || [];
        }
      } catch {
        plotGCodeString(ctx, data, width, height);
        return;
      }
    }

    if (nodes.length === 0) {
      drawPlaceholder(ctx, width, height);
      return;
    }

    // Find coordinate bounds
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const node of nodes) {
      if (node.pos) {
        minX = Math.min(minX, node.pos.x);
        maxX = Math.max(maxX, node.pos.x);
        minY = Math.min(minY, node.pos.y);
        maxY = Math.max(maxY, node.pos.y);
      }
    }

    if (minX === Infinity) { minX = 0; maxX = 100; }
    if (minY === Infinity) { minY = 0; maxY = 100; }

    const padding = 50;
    const drawWidth = width - padding * 2;
    const drawHeight = height - padding * 2;

    const rangeX = Math.max(maxX - minX, 10);
    const rangeY = Math.max(maxY - minY, 10);
    const baseScale = Math.min(drawWidth / rangeX, drawHeight / rangeY);
    const scale = baseScale * zoom;

    function toCanvasCoords(x: number, y: number) {
      return {
        x: padding + (x - minX) * scale + panX,
        y: height - (padding + (y - minY) * scale) + panY
      };
    }

    // Draw Coordinate Axes & Labels
    drawAxesAndLabels(ctx, minX, maxX, minY, maxY, toCanvasCoords, width, height);

    interface SegmentBatch {
      color: string;
      lineWidth: number;
      points: { x: number; y: number }[];
    }

    const batches: SegmentBatch[] = [];
    let currentBatch: SegmentBatch | null = null;
    let prevX = 0;
    let prevY = 0;

    for (const node of nodes) {
      if (!node.pos) continue;
      const targetPt = toCanvasCoords(node.pos.x, node.pos.y);
      const startPt = toCanvasCoords(prevX, prevY);

      let color = '#334155';
      let lw = 1;

      if (!node.beam_state) {
        color = '#334155';
        lw = 1;
      } else {
        lw = 2;
        switch (node.line_type) {
          case 'isolation': color = '#22c55e'; break; // Green
          case 'bus_bar': color = '#ef4444'; break;   // Red
          case 'cell':
          default: color = '#3b82f6'; break;          // Blue
        }
      }

      if (!currentBatch || currentBatch.color !== color || currentBatch.lineWidth !== lw) {
        currentBatch = { color, lineWidth: lw, points: [startPt, targetPt] };
        batches.push(currentBatch);
      } else {
        currentBatch.points.push(targetPt);
      }

      prevX = node.pos.x;
      prevY = node.pos.y;
    }

    for (const batch of batches) {
      if (batch.points.length < 2) continue;
      ctx.beginPath();
      ctx.strokeStyle = batch.color;
      ctx.lineWidth = batch.lineWidth;
      ctx.moveTo(batch.points[0].x, batch.points[0].y);
      for (let i = 1; i < batch.points.length; i++) {
        ctx.lineTo(batch.points[i].x, batch.points[i].y);
      }
      ctx.stroke();
    }
  }

  function plotGCodeString(ctx: CanvasRenderingContext2D, gcode: string, width: number, height: number) {
    const lines = gcode.split('\n');
    let currentX = 0;
    let currentY = 0;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const line of lines) {
      const trimmed = line.trim();
      const matchX = trimmed.match(/X([0-9.-]+)/);
      const matchY = trimmed.match(/Y([0-9.-]+)/);
      if (matchX) {
        const val = parseFloat(matchX[1]);
        minX = Math.min(minX, val);
        maxX = Math.max(maxX, val);
      }
      if (matchY) {
        const val = parseFloat(matchY[1]);
        minY = Math.min(minY, val);
        maxY = Math.max(maxY, val);
      }
    }

    if (minX === Infinity) { minX = 0; maxX = 100; }
    if (minY === Infinity) { minY = 0; maxY = 100; }

    const padding = 50;
    const baseScale = Math.min((width - padding * 2) / Math.max(maxX - minX, 10), (height - padding * 2) / Math.max(maxY - minY, 10));
    const scale = baseScale * zoom;

    function toCanvasCoords(x: number, y: number) {
      return {
        x: padding + (x - minX) * scale + panX,
        y: height - (padding + (y - minY) * scale) + panY
      };
    }

    drawAxesAndLabels(ctx, minX, maxX, minY, maxY, toCanvasCoords, width, height);

    let currentLineType: 'isolation' | 'cell' | 'bus_bar' = 'cell';
    let isCutting = false;
    let startPt = toCanvasCoords(currentX, currentY);

    interface SegmentBatch {
      color: string;
      lineWidth: number;
      points: { x: number; y: number }[];
    }

    const batches: SegmentBatch[] = [];
    let currentBatch: SegmentBatch | null = null;

    for (const line of lines) {
      const trimmed = line.trim();

      if (trimmed.includes('Path Type: ISOLATION')) {
        currentLineType = 'isolation';
        continue;
      } else if (trimmed.includes('Path Type: CELL')) {
        currentLineType = 'cell';
        continue;
      } else if (trimmed.includes('Path Type: BUS_BAR') || trimmed.includes('Path Type: P2')) {
        currentLineType = 'bus_bar';
        continue;
      }

      if (trimmed.startsWith('M3') || trimmed.startsWith('G1')) isCutting = true;
      if (trimmed.startsWith('M5') || trimmed.startsWith('G0')) isCutting = false;

      const matchX = trimmed.match(/X([0-9.-]+)/);
      const matchY = trimmed.match(/Y([0-9.-]+)/);

      if (matchX) currentX = parseFloat(matchX[1]);
      if (matchY) currentY = parseFloat(matchY[1]);

      if (trimmed.startsWith('G0') || trimmed.startsWith('G1')) {
        const pt = toCanvasCoords(currentX, currentY);

        let color = '#334155';
        let lw = 1;

        if (!isCutting) {
          color = '#334155';
          lw = 1;
        } else {
          lw = 2;
          switch (currentLineType) {
            case 'isolation': color = '#22c55e'; break;
            case 'bus_bar': color = '#ef4444'; break;
            case 'cell':
            default: color = '#3b82f6'; break;
          }
        }

        if (!currentBatch || currentBatch.color !== color || currentBatch.lineWidth !== lw) {
          currentBatch = { color, lineWidth: lw, points: [startPt, pt] };
          batches.push(currentBatch);
        } else {
          currentBatch.points.push(pt);
        }

        startPt = pt;
      }
    }

    for (const batch of batches) {
      if (batch.points.length < 2) continue;
      ctx.beginPath();
      ctx.strokeStyle = batch.color;
      ctx.lineWidth = batch.lineWidth;
      ctx.moveTo(batch.points[0].x, batch.points[0].y);
      for (let i = 1; i < batch.points.length; i++) {
        ctx.lineTo(batch.points[i].x, batch.points[i].y);
      }
      ctx.stroke();
    }
  }

  function drawAxesAndLabels(
    ctx: CanvasRenderingContext2D,
    minX: number,
    maxX: number,
    minY: number,
    maxY: number,
    toCanvasCoords: (x: number, y: number) => { x: number; y: number },
    width: number,
    height: number
  ) {
    ctx.save();
    ctx.strokeStyle = '#475569';
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px sans-serif';

    // Draw X Axis Line (at bottom or relative to min Y)
    const origin = toCanvasCoords(minX, minY);
    
    // Draw Ticks & Labels along X axis
    const stepsX = 5;
    const rangeX = maxX - minX;
    for (let i = 0; i <= stepsX; i++) {
      const val = minX + (rangeX * i) / stepsX;
      const pt = toCanvasCoords(val, minY);
      
      if (pt.x >= 20 && pt.x <= width - 20) {
        ctx.beginPath();
        ctx.moveTo(pt.x, height - 35);
        ctx.lineTo(pt.x, height - 40);
        ctx.stroke();

        ctx.textAlign = 'center';
        ctx.fillText(`${val.toFixed(1)}`, pt.x, height - 22);
      }
    }

    // Draw Ticks & Labels along Y axis
    const stepsY = 5;
    const rangeY = maxY - minY;
    for (let i = 0; i <= stepsY; i++) {
      const val = minY + (rangeY * i) / stepsY;
      const pt = toCanvasCoords(minX, val);

      if (pt.y >= 20 && pt.y <= height - 20) {
        ctx.beginPath();
        ctx.moveTo(35, pt.y);
        ctx.lineTo(40, pt.y);
        ctx.stroke();

        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${val.toFixed(1)}`, 30, pt.y);
      }
    }

    // Axis titles
    ctx.fillStyle = '#64748b';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('X Coordinate (units)', width / 2, height - 8);

    ctx.save();
    ctx.translate(12, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillText('Y Coordinate (units)', 0, 0);
    ctx.restore();

    ctx.restore();
  }
</script>

<div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-3 shadow-xl">
  <div class="flex justify-between items-center">
    <div class="flex items-center space-x-3">
      <h3 class="text-sm font-semibold text-slate-200">Live Path Visualizer</h3>
      <span class="text-xs text-slate-400 hidden sm:inline">(Scroll to zoom, drag to pan)</span>
    </div>
    
    <div class="flex items-center space-x-3 text-xs">
      <button 
        onclick={resetView}
        class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
      >
        Reset View ({Math.round(zoom * 100)}%)
      </button>
      <span class="flex items-center space-x-1 text-slate-400"><span class="w-2 h-2 rounded-full bg-green-500 inline-block"></span><span>Isolation</span></span>
      <span class="flex items-center space-x-1 text-slate-400"><span class="w-2 h-2 rounded-full bg-blue-500 inline-block"></span><span>Cells</span></span>
      <span class="flex items-center space-x-1 text-slate-400"><span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span><span>Bus Bars</span></span>
    </div>
  </div>
  
  <div class="relative w-full aspect-video bg-slate-950 border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center cursor-grab active:cursor-grabbing">
    <canvas 
      bind:this={canvas} 
      width={640} 
      height={360} 
      class="w-full h-full object-contain"
      onmousedown={handleMouseDown}
      onmousemove={handleMouseMove}
      onmouseup={handleMouseUp}
      onmouseleave={handleMouseUp}
      onwheel={handleWheel}
    ></canvas>
  </div>
</div>