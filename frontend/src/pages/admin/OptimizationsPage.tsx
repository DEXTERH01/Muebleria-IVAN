import { useRef, useState, type FormEvent } from 'react';

import {
  optimizeDelivery,
  optimizeProduction,
  type DeliveryOptimizationView,
  type ProductionOptimizationInput,
  type ProductionOptimizationView,
  type ProductionScoreView,
} from '../../api/modules/optimizations';
import { AdminLayout } from '../../components/layout';
import { Button } from '../../components/ui';

type OptimizationTab = 'delivery' | 'production';

interface StopDraft {
  id: string;
  name: string;
}

interface LocationDraft extends StopDraft {
  fallback: string;
}

interface TaskDraft {
  rowId: string;
  taskId: string;
  material: string;
  durationHours: string;
  dueInHours: string;
  readyInHours: string;
}

const numberFormatter = new Intl.NumberFormat('es-PE', {
  maximumFractionDigits: 2,
});

function displayNumber(value: number): string {
  return numberFormatter.format(value);
}

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : 'No se pudo ejecutar la optimización.';
}

function pairKey(left: string, right: string): string {
  return [left, right].sort().join(':');
}

function locationPairs(locations: LocationDraft[]): Array<[LocationDraft, LocationDraft]> {
  const pairs: Array<[LocationDraft, LocationDraft]> = [];
  for (let left = 0; left < locations.length - 1; left += 1) {
    for (let right = left + 1; right < locations.length; right += 1) {
      pairs.push([locations[left], locations[right]]);
    }
  }
  return pairs;
}

function Sequence({ items, label }: { items: string[]; label: string }) {
  return <div className="optimization-sequence" aria-label={label}>
    {items.map((item, index) => <span key={`${item}-${index}`}>
      <b>{index + 1}</b>{item}{index < items.length - 1 && <i aria-hidden="true">→</i>}
    </span>)}
  </div>;
}

function ComparisonBars({
  baseline,
  recommended,
  unit,
}: {
  baseline: number;
  recommended: number;
  unit: string;
}) {
  const maximum = Math.max(baseline, recommended, 1);
  return <div className="comparison-bars" aria-label="Comparación con la línea base">
    <div>
      <span>Orden inicial <b>{displayNumber(baseline)} {unit}</b></span>
      <i><em style={{ width: `${Math.max(4, baseline / maximum * 100)}%` }} /></i>
    </div>
    <div className="recommended">
      <span>Sugerencia <b>{displayNumber(recommended)} {unit}</b></span>
      <i><em style={{ width: `${Math.max(4, recommended / maximum * 100)}%` }} /></i>
    </div>
  </div>;
}

function DeliveryResult({ result }: { result: DeliveryOptimizationView }) {
  return <article className="admin-card optimization-result" aria-live="polite">
    <header>
      <div>
        <span className="algorithm-chip">A* · ejecución guardada</span>
        <h2>Ruta sugerida</h2>
        <p>Comparación reproducible contra el orden de paradas ingresado.</p>
      </div>
      <strong>{displayNumber(result.improvement)}%<small>mejora calculada</small></strong>
    </header>
    <ComparisonBars
      baseline={result.initialDistance}
      recommended={result.recommendedDistance}
      unit="unid."
    />
    <div className="sequence-comparison">
      <section>
        <h3>Orden inicial</h3>
        <Sequence items={result.initialRoute} label="Orden inicial de entrega" />
      </section>
      <section className="recommended-sequence">
        <h3>Orden sugerido</h3>
        <Sequence items={result.recommendedRoute} label="Orden sugerido de entrega" />
      </section>
    </div>
    <dl className="optimization-metrics">
      <div><dt>Distancia inicial</dt><dd>{displayNumber(result.initialDistance)}</dd></div>
      <div><dt>Distancia sugerida</dt><dd>{displayNumber(result.recommendedDistance)}</dd></div>
      <div><dt>Nodos explorados</dt><dd>{result.exploredNodes}</dd></div>
      <div><dt>Tiempo de cálculo</dt><dd>{displayNumber(result.durationMs)} ms</dd></div>
    </dl>
    <p className="advisory-note"><span aria-hidden="true">i</span>
      Recomendación consultiva. La ejecución no modifica entregas ni reemplaza la planificación humana.
    </p>
  </article>;
}

function DeliveryPanel() {
  const stopCounter = useRef(3);
  const [start, setStart] = useState('');
  const [stops, setStops] = useState<StopDraft[]>([
    { id: 'stop-1', name: '' },
    { id: 'stop-2', name: '' },
  ]);
  const [distances, setDistances] = useState<Record<string, string>>({});
  const [result, setResult] = useState<DeliveryOptimizationView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const locations: LocationDraft[] = [
    { id: 'start', name: start, fallback: 'Origen' },
    ...stops.map((stop, index) => ({ ...stop, fallback: `Parada ${index + 1}` })),
  ];
  const pairs = locationPairs(locations);

  const addStop = () => {
    if (stops.length >= 12) return;
    const id = `stop-${stopCounter.current}`;
    stopCounter.current += 1;
    setStops((current) => [...current, { id, name: '' }]);
  };

  const removeStop = (id: string) => {
    if (stops.length === 1) return;
    setStops((current) => current.filter((stop) => stop.id !== id));
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    const namedLocations = locations.map((location) => ({
      ...location,
      name: location.name.trim(),
    }));
    if (namedLocations.some((location) => !location.name)) {
      setError('Completa el punto de partida y todas las paradas.');
      return;
    }
    const normalizedNames = namedLocations.map((location) => location.name.toLocaleLowerCase());
    if (new Set(normalizedNames).size !== normalizedNames.length) {
      setError('Cada ubicación debe tener un nombre distinto.');
      return;
    }

    const matrix: Record<string, Record<string, number>> = Object.fromEntries(
      namedLocations.map((location) => [location.name, { [location.name]: 0 }]),
    );
    for (const [left, right] of locationPairs(namedLocations)) {
      const raw = distances[pairKey(left.id, right.id)];
      const distance = Number(raw);
      if (raw === undefined || raw === '' || !Number.isFinite(distance) || distance < 0) {
        setError(`Ingresa una distancia válida entre ${left.name} y ${right.name}.`);
        return;
      }
      matrix[left.name][right.name] = distance;
      matrix[right.name][left.name] = distance;
    }

    setLoading(true);
    try {
      setResult(await optimizeDelivery({
        start: namedLocations[0].name,
        stops: namedLocations.slice(1).map((location) => location.name),
        distances: matrix,
      }));
    } catch (requestError) {
      setError(messageFrom(requestError));
    } finally {
      setLoading(false);
    }
  };

  return <div className="optimization-workspace" role="tabpanel" aria-label="Optimización de rutas">
    <form className="admin-card optimization-form" onSubmit={submit}>
      <div className="card-title">
        <div><h2>Datos de entrega</h2><p>A* usa una matriz simétrica de distancias.</p></div>
        <span className="algorithm-chip">A*</span>
      </div>
      <label className="optimization-field">Punto de partida
        <input
          value={start}
          onChange={(event) => setStart(event.target.value)}
          placeholder="Ej. Taller"
          maxLength={100}
          required
        />
      </label>
      <fieldset className="optimization-fieldset">
        <legend>Paradas</legend>
        {stops.map((stop, index) => <div className="repeatable-row" key={stop.id}>
          <label>Nombre de parada {index + 1}
            <input
              value={stop.name}
              onChange={(event) => setStops((current) => current.map((item) => (
                item.id === stop.id ? { ...item, name: event.target.value } : item
              )))}
              placeholder={`Parada ${index + 1}`}
              maxLength={100}
              required
            />
          </label>
          <button
            type="button"
            className="remove-row"
            onClick={() => removeStop(stop.id)}
            disabled={stops.length === 1}
            aria-label={`Eliminar parada ${index + 1}`}
          >×</button>
        </div>)}
        <button type="button" className="add-row" onClick={addStop} disabled={stops.length >= 12}>
          + Añadir parada
        </button>
      </fieldset>
      <fieldset className="optimization-fieldset distance-fields">
        <legend>Distancias entre ubicaciones</legend>
        <p>Usa la misma unidad en todos los pares. La matriz se completa en ambos sentidos.</p>
        <div>
          {pairs.map(([left, right]) => {
            const leftLabel = left.name.trim() || left.fallback;
            const rightLabel = right.name.trim() || right.fallback;
            const key = pairKey(left.id, right.id);
            return <label key={key}>Distancia entre {leftLabel} y {rightLabel}
              <input
                type="number"
                min="0"
                step="any"
                value={distances[key] ?? ''}
                onChange={(event) => setDistances((current) => ({
                  ...current,
                  [key]: event.target.value,
                }))}
                required
              />
            </label>;
          })}
        </div>
      </fieldset>
      {error && <p className="form-error" role="alert">{error}</p>}
      <Button type="submit" disabled={loading}>
        {loading ? 'Calculando ruta…' : 'Calcular ruta sugerida'}
      </Button>
    </form>
    {result ? <DeliveryResult result={result} /> : <OptimizationEmptyState kind="delivery" />}
  </div>;
}

function newTask(rowNumber: number): TaskDraft {
  return {
    rowId: `task-row-${rowNumber}`,
    taskId: '',
    material: '',
    durationHours: '',
    dueInHours: '',
    readyInHours: '0',
  };
}

function ScoreDetails({ score }: { score: ProductionScoreView }) {
  return <dl className="score-details">
    <div><dt>Puntaje objetivo</dt><dd>{displayNumber(score.total)}</dd></div>
    <div><dt>Retraso acumulado</dt><dd>{displayNumber(score.delayDays)} días</dd></div>
    <div><dt>Cambios de material</dt><dd>{score.materialChanges}</dd></div>
    <div><dt>Tiempo inactivo</dt><dd>{displayNumber(score.idleHours)} h</dd></div>
  </dl>;
}

function ProductionResult({ result }: { result: ProductionOptimizationView }) {
  const stopReason = result.stopReason === 'local_optimum'
    ? 'Óptimo local'
    : 'Máximo de iteraciones';
  return <article className="admin-card optimization-result" aria-live="polite">
    <header>
      <div>
        <span className="algorithm-chip">Hill Climbing · ejecución guardada</span>
        <h2>Secuencia sugerida</h2>
        <p>Un puntaje menor representa menos retraso, cambios de material y espera.</p>
      </div>
      <strong>{displayNumber(result.improvement)}%<small>mejora calculada</small></strong>
    </header>
    <ComparisonBars
      baseline={result.initialScore.total}
      recommended={result.recommendedScore.total}
      unit="pts."
    />
    <div className="sequence-comparison">
      <section>
        <h3>Secuencia inicial</h3>
        <Sequence items={result.initialSequence} label="Secuencia inicial de producción" />
        <ScoreDetails score={result.initialScore} />
      </section>
      <section className="recommended-sequence">
        <h3>Secuencia sugerida</h3>
        <Sequence items={result.recommendedSequence} label="Secuencia sugerida de producción" />
        <ScoreDetails score={result.recommendedScore} />
      </section>
    </div>
    <dl className="optimization-metrics">
      <div><dt>Iteraciones</dt><dd>{result.iterations}</dd></div>
      <div><dt>Reinicios</dt><dd>{result.restarts}</dd></div>
      <div><dt>Semilla</dt><dd>{result.randomSeed}</dd></div>
      <div><dt>Finalización</dt><dd>{stopReason}</dd></div>
      <div><dt>Tiempo de cálculo</dt><dd>{displayNumber(result.durationMs)} ms</dd></div>
    </dl>
    <p className="advisory-note"><span aria-hidden="true">i</span>
      Recomendación consultiva. La secuencia no cambia automáticamente el estado de ningún pedido.
    </p>
  </article>;
}

function ProductionPanel() {
  const taskCounter = useRef(3);
  const [tasks, setTasks] = useState<TaskDraft[]>([newTask(1), newTask(2)]);
  const [randomSeed, setRandomSeed] = useState(2026);
  const [restarts, setRestarts] = useState(5);
  const [maxIterations, setMaxIterations] = useState(100);
  const [delayWeight, setDelayWeight] = useState(10);
  const [materialWeight, setMaterialWeight] = useState(3);
  const [idleWeight, setIdleWeight] = useState(2);
  const [result, setResult] = useState<ProductionOptimizationView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const updateTask = (rowId: string, field: keyof TaskDraft, value: string) => {
    setTasks((current) => current.map((task) => (
      task.rowId === rowId ? { ...task, [field]: value } : task
    )));
  };

  const addTask = () => {
    if (tasks.length >= 20) return;
    setTasks((current) => [...current, newTask(taskCounter.current)]);
    taskCounter.current += 1;
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    const normalizedTasks = tasks.map((task) => ({
      taskId: task.taskId.trim(),
      material: task.material.trim(),
      durationHours: Number(task.durationHours),
      dueInHours: Number(task.dueInHours),
      readyInHours: Number(task.readyInHours),
    }));
    if (normalizedTasks.some((task) => !task.taskId || !task.material)) {
      setError('Cada trabajo debe indicar un código y un material.');
      return;
    }
    if (new Set(normalizedTasks.map((task) => task.taskId)).size !== normalizedTasks.length) {
      setError('Los códigos de trabajo no pueden repetirse.');
      return;
    }
    if (normalizedTasks.some((task) => (
      !Number.isFinite(task.durationHours)
      || task.durationHours <= 0
      || !Number.isFinite(task.dueInHours)
      || task.dueInHours < 0
      || !Number.isFinite(task.readyInHours)
      || task.readyInHours < 0
    ))) {
      setError('Revisa las horas de duración, entrega y disponibilidad.');
      return;
    }

    const input: ProductionOptimizationInput = {
      tasks: normalizedTasks,
      weights: {
        delayDays: delayWeight,
        materialChanges: materialWeight,
        idleHours: idleWeight,
      },
      randomSeed,
      restarts,
      maxIterations,
    };
    setLoading(true);
    try {
      setResult(await optimizeProduction(input));
    } catch (requestError) {
      setError(messageFrom(requestError));
    } finally {
      setLoading(false);
    }
  };

  return <div className="optimization-workspace" role="tabpanel" aria-label="Optimización de producción">
    <form className="admin-card optimization-form production-form" onSubmit={submit}>
      <div className="card-title">
        <div><h2>Trabajos del taller</h2><p>El orden ingresado funciona como línea base.</p></div>
        <span className="algorithm-chip">Hill Climbing</span>
      </div>
      <fieldset className="optimization-fieldset task-fields">
        <legend>Trabajos por ordenar</legend>
        {tasks.map((task, index) => <article key={task.rowId}>
          <header><b>Trabajo {index + 1}</b><button
            type="button"
            className="remove-row"
            onClick={() => setTasks((current) => current.filter((item) => item.rowId !== task.rowId))}
            disabled={tasks.length === 1}
            aria-label={`Eliminar trabajo ${index + 1}`}
          >×</button></header>
          <label>Código del trabajo
            <input
              value={task.taskId}
              onChange={(event) => updateTask(task.rowId, 'taskId', event.target.value)}
              maxLength={100}
              required
            />
          </label>
          <label>Material
            <input
              value={task.material}
              onChange={(event) => updateTask(task.rowId, 'material', event.target.value)}
              maxLength={100}
              required
            />
          </label>
          <label>Duración estimada (h)
            <input
              type="number"
              min="0.01"
              step="any"
              value={task.durationHours}
              onChange={(event) => updateTask(task.rowId, 'durationHours', event.target.value)}
              required
            />
          </label>
          <label>Entrega en (h)
            <input
              type="number"
              min="0"
              step="any"
              value={task.dueInHours}
              onChange={(event) => updateTask(task.rowId, 'dueInHours', event.target.value)}
              required
            />
          </label>
          <label>Disponible en (h)
            <input
              type="number"
              min="0"
              step="any"
              value={task.readyInHours}
              onChange={(event) => updateTask(task.rowId, 'readyInHours', event.target.value)}
              required
            />
          </label>
        </article>)}
        <button type="button" className="add-row" onClick={addTask} disabled={tasks.length >= 20}>
          + Añadir trabajo
        </button>
      </fieldset>
      <details className="algorithm-settings">
        <summary>Configuración del algoritmo</summary>
        <div>
          <label>Semilla aleatoria<input type="number" value={randomSeed} onChange={(event) => setRandomSeed(Number(event.target.value))} /></label>
          <label>Reinicios<input type="number" min="0" max="50" value={restarts} onChange={(event) => setRestarts(Number(event.target.value))} /></label>
          <label>Máximo de iteraciones<input type="number" min="1" max="10000" value={maxIterations} onChange={(event) => setMaxIterations(Number(event.target.value))} /></label>
          <label>Peso de retraso<input type="number" min="0" step="any" value={delayWeight} onChange={(event) => setDelayWeight(Number(event.target.value))} /></label>
          <label>Peso de cambio de material<input type="number" min="0" step="any" value={materialWeight} onChange={(event) => setMaterialWeight(Number(event.target.value))} /></label>
          <label>Peso de tiempo inactivo<input type="number" min="0" step="any" value={idleWeight} onChange={(event) => setIdleWeight(Number(event.target.value))} /></label>
        </div>
      </details>
      {error && <p className="form-error" role="alert">{error}</p>}
      <Button type="submit" disabled={loading}>
        {loading ? 'Calculando secuencia…' : 'Calcular secuencia sugerida'}
      </Button>
    </form>
    {result ? <ProductionResult result={result} /> : <OptimizationEmptyState kind="production" />}
  </div>;
}

function OptimizationEmptyState({ kind }: { kind: OptimizationTab }) {
  return <section className="admin-card optimization-empty">
    <span aria-hidden="true">{kind === 'delivery' ? '⌁' : '↕'}</span>
    <h2>{kind === 'delivery' ? 'Compara una ruta' : 'Compara una secuencia'}</h2>
    <p>{kind === 'delivery'
      ? 'Ingresa ubicaciones y distancias para contrastar el orden inicial con la ruta sugerida por A*.'
      : 'Ingresa trabajos reales del taller para contrastar su orden con la sugerencia de Hill Climbing.'}</p>
    <small>Los resultados aparecerán aquí y se guardarán como una ejecución consultiva.</small>
  </section>;
}

export function OptimizationsPage() {
  const [tab, setTab] = useState<OptimizationTab>('delivery');
  return <AdminLayout title="Optimizaciones" subtitle="ALGORITMOS DE BÚSQUEDA">
    <section className="optimization-intro">
      <div><span>DECISIÓN ASISTIDA</span><h2>Compara antes de reorganizar el taller.</h2></div>
      <p>A* y Hill Climbing generan recomendaciones reproducibles. Ninguna ejecución cambia pedidos, pagos, entregas o producción automáticamente.</p>
    </section>
    <div className="optimization-tabs" role="tablist" aria-label="Tipo de optimización">
      <button
        type="button"
        role="tab"
        aria-selected={tab === 'delivery'}
        className={tab === 'delivery' ? 'active' : ''}
        onClick={() => setTab('delivery')}
      ><span>A*</span><b>Rutas de entrega</b><small>Menor distancia</small></button>
      <button
        type="button"
        role="tab"
        aria-selected={tab === 'production'}
        className={tab === 'production' ? 'active' : ''}
        onClick={() => setTab('production')}
      ><span>HC</span><b>Secuencia de taller</b><small>Menor puntaje operativo</small></button>
    </div>
    {tab === 'delivery' ? <DeliveryPanel /> : <ProductionPanel />}
  </AdminLayout>;
}
