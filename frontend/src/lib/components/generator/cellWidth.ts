export interface CellWidthInput {
  cellCount: number;
  panelSize: number;
  isP1: boolean;
  busBarWidth: number;
  p2BusSpacing: number;
  busBarSpacing: number;
  /** Border kept clear of scribes on every side of the panel. */
  edgeMargin?: number;
}

/**
 * Mirrors compute_cell_width() in path_generator.py. The backend is the source of truth; this exists so the form can
 * show the width live. Returns null when the configuration is invalid.
 */
export function computeCellWidth(i: CellWidthInput): number | null {
  if (!Number.isInteger(i.cellCount) || i.cellCount < 1) return null;

  const edgeMargin = i.edgeMargin ?? 0;
  if (edgeMargin < 0) return null;

  const busBarClearance = i.isP1 ? 0 : Math.max(i.p2BusSpacing, i.busBarSpacing) + i.busBarWidth;
  const edgeClearance = edgeMargin + busBarClearance;
  const available = i.panelSize - 2 * edgeClearance;
  if (available <= 0) return null;

  const width = Math.floor(available / i.cellCount / 0.001) * 0.001;
  const rounded = Math.round(width * 1e6) / 1e6;
  return rounded > 0 ? rounded : null;
}