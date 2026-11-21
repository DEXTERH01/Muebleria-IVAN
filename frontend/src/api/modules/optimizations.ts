import type { components } from '../generated/schema';
import { apiRequest } from '../client/http';

export type DeliveryOptimizationInput = components['schemas']['DeliveryOptimizationRequest'];
export type ProductionOptimizationInput = components['schemas']['ProductionOptimizationRequest'];

type OptimizationRunResponse = components['schemas']['OptimizationRunResponse'];
type OptimizationRun = components['schemas']['OptimizationRunData'];

export interface DeliveryOptimizationView {
  id: string;
  initialRoute: string[];
  recommendedRoute: string[];
  initialDistance: number;
  recommendedDistance: number;
  exploredNodes: number;
  improvement: number;
  durationMs: number;
  advisory: boolean;
}

export interface ProductionScoreView {
  total: number;
  delayDays: number;
  materialChanges: number;
  idleHours: number;
}

export interface ProductionOptimizationView {
  id: string;
  initialSequence: string[];
  recommendedSequence: string[];
  initialScore: ProductionScoreView;
  recommendedScore: ProductionScoreView;
  improvement: number;
  iterations: number;
  restarts: number;
  stopReason: string;
  randomSeed: number;
  durationMs: number;
  advisory: boolean;
}

function record(value: unknown, label: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`La API devolvió ${label} con un formato inesperado.`);
  }
  return value as Record<string, unknown>;
}

function numberField(source: Record<string, unknown>, key: string): number {
  const value = source[key];
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new Error(`La API no devolvió el valor numérico ${key}.`);
  }
  return value;
}

function stringField(source: Record<string, unknown>, key: string): string {
  const value = source[key];
  if (typeof value !== 'string') {
    throw new Error(`La API no devolvió el texto ${key}.`);
  }
  return value;
}

function stringArrayField(source: Record<string, unknown>, key: string): string[] {
  const value = source[key];
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string')) {
    throw new Error(`La API no devolvió la secuencia ${key}.`);
  }
  return value;
}

function productionScore(value: unknown): ProductionScoreView {
  const score = record(value, 'un puntaje de producción');
  return {
    total: numberField(score, 'total'),
    delayDays: numberField(score, 'delay_days'),
    materialChanges: numberField(score, 'material_changes'),
    idleHours: numberField(score, 'idle_hours'),
  };
}

function deliveryView(run: OptimizationRun): DeliveryOptimizationView {
  const baseline = record(run.baseline, 'la línea base de ruta');
  const result = record(run.result, 'la ruta sugerida');
  return {
    id: run.id,
    initialRoute: stringArrayField(baseline, 'route'),
    recommendedRoute: stringArrayField(result, 'route'),
    initialDistance: numberField(baseline, 'distance'),
    recommendedDistance: numberField(result, 'distance'),
    exploredNodes: numberField(result, 'exploredNodes'),
    improvement: run.improvement,
    durationMs: run.durationMs,
    advisory: run.advisory,
  };
}

function productionView(run: OptimizationRun): ProductionOptimizationView {
  const baseline = record(run.baseline, 'la línea base de producción');
  const result = record(run.result, 'la secuencia sugerida');
  if (run.randomSeed === null) {
    throw new Error('La API no devolvió la semilla de la optimización de producción.');
  }
  return {
    id: run.id,
    initialSequence: stringArrayField(baseline, 'sequence'),
    recommendedSequence: stringArrayField(result, 'sequence'),
    initialScore: productionScore(baseline.score),
    recommendedScore: productionScore(result.score),
    improvement: run.improvement,
    iterations: numberField(result, 'iterations'),
    restarts: numberField(result, 'restarts'),
    stopReason: stringField(result, 'stopReason'),
    randomSeed: run.randomSeed,
    durationMs: run.durationMs,
    advisory: run.advisory,
  };
}

export async function optimizeDelivery(
  input: DeliveryOptimizationInput,
): Promise<DeliveryOptimizationView> {
  const response = await apiRequest<OptimizationRunResponse>(
    '/api/v1/optimizations/delivery',
    { method: 'POST', body: JSON.stringify(input) },
  );
  if (response.data.algorithm !== 'astar') {
    throw new Error('La API respondió con un algoritmo distinto de A*.');
  }
  return deliveryView(response.data);
}

export async function optimizeProduction(
  input: ProductionOptimizationInput,
): Promise<ProductionOptimizationView> {
  const response = await apiRequest<OptimizationRunResponse>(
    '/api/v1/optimizations/production',
    { method: 'POST', body: JSON.stringify(input) },
  );
  if (response.data.algorithm !== 'hill_climbing') {
    throw new Error('La API respondió con un algoritmo distinto de Hill Climbing.');
  }
  return productionView(response.data);
}
