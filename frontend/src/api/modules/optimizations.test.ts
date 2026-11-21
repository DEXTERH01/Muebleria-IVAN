import { beforeEach, describe, expect, it, vi } from 'vitest';

import { optimizeDelivery, optimizeProduction } from './optimizations';

describe('optimization API module', () => {
  beforeEach(() => vi.unstubAllGlobals());

  it('sends delivery inputs and maps the saved A* baseline and recommendation', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: {
      id: 'run-1', algorithm: 'astar',
      baseline: { route: ['Taller', 'A', 'B'], distance: 12 },
      result: { route: ['Taller', 'B', 'A'], distance: 8, exploredNodes: 6 },
      improvement: 33.3, durationMs: 2, randomSeed: null, advisory: true,
    } }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    vi.stubGlobal('fetch', fetchMock);

    const result = await optimizeDelivery({
      start: 'Taller', stops: ['A', 'B'], distances: { Taller: { Taller: 0 } },
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/v1/optimizations/delivery',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(result.initialDistance).toBe(12);
    expect(result.recommendedRoute).toEqual(['Taller', 'B', 'A']);
    expect(result.advisory).toBe(true);
  });

  it('maps production scores and deterministic run metadata from Hill Climbing', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: {
      id: 'run-2', algorithm: 'hill_climbing',
      baseline: { sequence: ['B', 'A'], score: {
        total: 12, delay_days: 1, material_changes: 1, idle_hours: 0,
      } },
      result: { sequence: ['A', 'B'], score: {
        total: 4, delay_days: 0, material_changes: 1, idle_hours: 0.5,
      }, iterations: 2, restarts: 5, stopReason: 'local_optimum' },
      improvement: 66.7, durationMs: 3, randomSeed: 2026, advisory: true,
    } }), { status: 200, headers: { 'Content-Type': 'application/json' } })));

    const result = await optimizeProduction({
      tasks: [], randomSeed: 2026, restarts: 5, maxIterations: 100,
    });

    expect(result.initialSequence).toEqual(['B', 'A']);
    expect(result.recommendedScore.delayDays).toBe(0);
    expect(result.randomSeed).toBe(2026);
  });
});
