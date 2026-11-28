import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { performance } from 'node:perf_hooks';

const flags = new Map();
for (let index = 2; index < process.argv.length; index += 2) {
  if (!process.argv[index]?.startsWith('--') || !process.argv[index + 1]) {
    throw new Error('Usa --base-url URL --samples 50 --concurrency 3 --output archivo.json');
  }
  flags.set(process.argv[index].slice(2), process.argv[index + 1]);
}
const baseUrl = (flags.get('base-url') ?? 'http://127.0.0.1:8015').replace(/\/$/, '');
const samples = Number(flags.get('samples') ?? 50);
const concurrency = Number(flags.get('concurrency') ?? 3);
const output = flags.get('output');
if (!['http:', 'https:'].includes(new URL(baseUrl).protocol)
  || !Number.isInteger(samples) || samples < 2 || samples > 200
  || !Number.isInteger(concurrency) || concurrency < 2 || concurrency > 5 || !output) {
  throw new Error('Indica una URL HTTP(S), 2–200 muestras, concurrencia 2–5 y --output.');
}

async function readData(path) {
  const response = await fetch(`${baseUrl}${path}`, { signal: AbortSignal.timeout(60_000) });
  if (!response.ok) throw new Error(`No se pudo preparar ${path}: HTTP ${response.status}`);
  return (await response.json()).data;
}

const catalog = await readData('/api/v1/products?page=1&pageSize=1');
const first = catalog.items[0];
if (!first) throw new Error('La API necesita un producto activo para medir la estimación.');
const product = await readData(`/api/v1/products/${encodeURIComponent(first.slug)}`);
const limits = product.measurementLimits;
const estimate = { items: [{
  productId: product.id, quantity: 1, widthMm: limits.minWidthMm,
  heightMm: limits.minHeightMm, depthMm: limits.minDepthMm,
}] };
const operations = [
  { name: 'catalog', path: '/api/v1/products?page=1&pageSize=100', init: {} },
  { name: 'product', path: `/api/v1/products/${encodeURIComponent(first.slug)}`, init: {} },
  { name: 'estimate', path: '/api/v1/quotes/estimate', init: {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(estimate),
  } },
];

async function request(operation) {
  const started = performance.now();
  let status = null;
  try {
    const response = await fetch(`${baseUrl}${operation.path}`, {
      ...operation.init, signal: AbortSignal.timeout(30_000),
    });
    status = response.status;
    // Include body transfer, including non-JSON proxy errors, in the latency.
    await response.arrayBuffer();
    return { ms: performance.now() - started, status, ok: response.ok };
  } catch {
    return { ms: performance.now() - started, status, ok: false };
  }
}

async function measure(operation, workers) {
  const values = [];
  let next = 0;
  const started = performance.now();
  await Promise.all(Array.from({ length: workers }, async () => {
    while (next < samples) { next++; values.push(await request(operation)); }
  }));
  const elapsedMs = performance.now() - started;
  const successful = values.filter((value) => value.ok).map((value) => value.ms).sort((a, b) => a - b);
  const percentile = (fraction) => successful.length
    ? Number(successful[Math.ceil(successful.length * fraction) - 1].toFixed(3)) : null;
  const statuses = {};
  for (const value of values) {
    const key = value.status ?? 'network-error';
    statuses[key] = (statuses[key] ?? 0) + 1;
  }
  return {
    samples: values.length, concurrency: workers,
    errors: values.filter((value) => !value.ok).length, statuses,
    p50Ms: percentile(.50), p95Ms: percentile(.95),
    elapsedMs: Number(elapsedMs.toFixed(3)),
    requestsPerSecond: Number((values.length / (elapsedMs / 1000)).toFixed(3)),
  };
}

const report = {
  measuredAt: new Date().toISOString(), baseUrl,
  method: 'nearest rank over successful full-body responses; sequential then concurrent; first request separate',
  notes: 'Public read operations only. Includes client, network, API and database; no quotes or payments are created.',
  operations: {},
};
for (const operation of operations) {
  const firstRequest = await request(operation);
  report.operations[operation.name] = {
    method: operation.init.method ?? 'GET', path: operation.path,
    firstRequestMs: Number(firstRequest.ms.toFixed(3)), firstRequestStatus: firstRequest.status,
    sequential: await measure(operation, 1), concurrent: await measure(operation, concurrency),
  };
  console.log(`${operation.name}: ${JSON.stringify(report.operations[operation.name])}`);
}
await mkdir(dirname(output), { recursive: true });
await writeFile(output, `${JSON.stringify(report, null, 2)}\n`);
if (Object.values(report.operations).some((operation) => operation.sequential.errors || operation.concurrent.errors)) {
  process.exitCode = 1;
}
