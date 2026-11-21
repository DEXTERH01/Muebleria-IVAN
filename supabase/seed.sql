-- Datos ficticios y deterministas para desarrollo local.
-- Estas filas de auth.users no tienen contraseña. Para cuentas capaces de iniciar
-- sesión, use Supabase Studio o Auth Admin y conserve los mismos roles en app.profiles.

begin;

insert into auth.users (id, email, raw_user_meta_data)
values
  ('10000000-0000-4000-8000-000000000001', 'admin@muebleria-ivan.test', '{"full_name":"Admin Demo"}'),
  ('10000000-0000-4000-8000-000000000002', 'operador@muebleria-ivan.test', '{"full_name":"Operador Demo"}'),
  ('10000000-0000-4000-8000-000000000003', 'cliente.ana@example.test', '{"full_name":"Ana Torres"}'),
  ('10000000-0000-4000-8000-000000000004', 'cliente.luis@example.test', '{"full_name":"Luis Ramos"}')
on conflict (id) do nothing;

update app.profiles
set role = 'admin', full_name = 'Admin Demo'
where user_id = '10000000-0000-4000-8000-000000000001';

update app.profiles
set role = 'operator', full_name = 'Operador Demo'
where user_id = '10000000-0000-4000-8000-000000000002';

update app.profiles
set full_name = case user_id
  when '10000000-0000-4000-8000-000000000003' then 'Ana Torres'
  when '10000000-0000-4000-8000-000000000004' then 'Luis Ramos'
end
where user_id in (
  '10000000-0000-4000-8000-000000000003',
  '10000000-0000-4000-8000-000000000004'
);

insert into app.customers (
  id, profile_user_id, full_name, email, phone, document_number, address, district, notes
)
values
  (
    '20000000-0000-4000-8000-000000000001',
    '10000000-0000-4000-8000-000000000003',
    'Ana Torres', 'cliente.ana@example.test', '999111222', 'DOC-DEMO-001',
    'Av. Los Cedros 120', 'Los Olivos', 'Cliente ficticia para pruebas'
  ),
  (
    '20000000-0000-4000-8000-000000000002',
    '10000000-0000-4000-8000-000000000004',
    'Luis Ramos', 'cliente.luis@example.test', '999333444', 'DOC-DEMO-002',
    'Jr. Las Flores 450', 'San Martín de Porres', 'Cliente ficticio para pruebas'
  )
on conflict (id) do nothing;

insert into app.delivery_locations (
  id, customer_id, label, address, district, reference, latitude, longitude
)
values
  (
    '21000000-0000-4000-8000-000000000001',
    '20000000-0000-4000-8000-000000000001',
    'Casa', 'Av. Los Cedros 120', 'Los Olivos', 'Frente al parque', -11.990500, -77.070100
  ),
  (
    '21000000-0000-4000-8000-000000000002',
    '20000000-0000-4000-8000-000000000002',
    'Departamento', 'Jr. Las Flores 450', 'San Martín de Porres', 'Piso 3', -12.006200, -77.083900
  )
on conflict (id) do nothing;

insert into app.materials (
  id, code, name, description, price_adjustment_minor, price_adjustment_percent
)
values
  ('30000000-0000-4000-8000-000000000001', 'MEL-18', 'Melamina 18 mm', 'Melamina estándar', 0, 0),
  ('30000000-0000-4000-8000-000000000002', 'MDF-18', 'MDF 18 mm', 'MDF para acabado pintado', 12000, 0),
  ('30000000-0000-4000-8000-000000000003', 'PLY-18', 'Triplay 18 mm', 'Tablero contrachapado', 0, 12.5000)
on conflict (id) do nothing;

insert into app.finishes (
  id, code, name, description, price_adjustment_minor, price_adjustment_percent
)
values
  ('31000000-0000-4000-8000-000000000001', 'NATURAL', 'Natural', 'Acabado natural mate', 0, 0),
  ('31000000-0000-4000-8000-000000000002', 'NOGAL', 'Nogal', 'Tono nogal cálido', 6500, 0),
  ('31000000-0000-4000-8000-000000000003', 'BLANCO', 'Blanco satinado', 'Pintura blanca satinada', 0, 8.0000)
on conflict (id) do nothing;

insert into app.accessories (
  id, code, name, description, price_adjustment_minor, price_adjustment_percent
)
values
  ('32000000-0000-4000-8000-000000000001', 'CORR-CIERRE', 'Correderas con cierre suave', 'Par de correderas telescópicas', 8500, 0),
  ('32000000-0000-4000-8000-000000000002', 'LED-CALIDA', 'Iluminación LED cálida', 'Tira LED y fuente', 12000, 0),
  ('32000000-0000-4000-8000-000000000003', 'PASACABLE', 'Pasacables', 'Pasacables circular', 2500, 0)
on conflict (id) do nothing;

insert into app.products (
  id, slug, name, description, category, base_price_minor,
  min_production_days, max_production_days,
  min_width_mm, max_width_mm, min_height_mm, max_height_mm, min_depth_mm, max_depth_mm
)
values
  (
    '40000000-0000-4000-8000-000000000001', 'ropero-andino', 'Ropero Andino',
    'Ropero de tres cuerpos personalizable.', 'Dormitorio', 145000, 10, 18,
    1200, 2600, 1800, 2600, 450, 750
  ),
  (
    '40000000-0000-4000-8000-000000000002', 'escritorio-lima', 'Escritorio Lima',
    'Escritorio compacto con cajonera.', 'Oficina', 78000, 7, 12,
    900, 2000, 700, 900, 450, 800
  ),
  (
    '40000000-0000-4000-8000-000000000003', 'centro-tv-nogal', 'Centro TV Nogal',
    'Mueble para televisión con almacenamiento.', 'Sala', 118000, 9, 16,
    1200, 2800, 450, 2200, 300, 650
  ),
  (
    '40000000-0000-4000-8000-000000000004', 'comoda-arena', 'Cómoda Arena',
    'Cómoda de seis cajones.', 'Dormitorio', 92000, 8, 14,
    800, 1800, 700, 1300, 350, 650
  ),
  (
    '40000000-0000-4000-8000-000000000005', 'mesa-comedor-ivan', 'Mesa Comedor Iván',
    'Mesa de comedor para cuatro a ocho personas.', 'Comedor', 132000, 10, 17,
    1200, 2600, 720, 820, 700, 1200
  ),
  (
    '40000000-0000-4000-8000-000000000006', 'biblioteca-modular', 'Biblioteca Modular',
    'Biblioteca configurable por módulos.', 'Sala', 105000, 9, 15,
    600, 2400, 1200, 2600, 250, 500
  )
on conflict (id) do nothing;

insert into app.product_images (
  id, product_id, public_id, secure_url, alt_text, position, width, height
)
values
  ('41000000-0000-4000-8000-000000000001', '40000000-0000-4000-8000-000000000001', 'demo/ropero-andino', 'https://res.cloudinary.com/demo/image/upload/ropero-andino.jpg', 'Ropero Andino de tres cuerpos', 0, 1200, 900),
  ('41000000-0000-4000-8000-000000000002', '40000000-0000-4000-8000-000000000002', 'demo/escritorio-lima', 'https://res.cloudinary.com/demo/image/upload/escritorio-lima.jpg', 'Escritorio Lima con cajonera', 0, 1200, 900),
  ('41000000-0000-4000-8000-000000000003', '40000000-0000-4000-8000-000000000003', 'demo/centro-tv-nogal', 'https://res.cloudinary.com/demo/image/upload/centro-tv-nogal.jpg', 'Centro TV en tono nogal', 0, 1200, 900),
  ('41000000-0000-4000-8000-000000000004', '40000000-0000-4000-8000-000000000004', 'demo/comoda-arena', 'https://res.cloudinary.com/demo/image/upload/comoda-arena.jpg', 'Cómoda Arena de seis cajones', 0, 1200, 900),
  ('41000000-0000-4000-8000-000000000005', '40000000-0000-4000-8000-000000000005', 'demo/mesa-comedor-ivan', 'https://res.cloudinary.com/demo/image/upload/mesa-comedor-ivan.jpg', 'Mesa Comedor Iván', 0, 1200, 900),
  ('41000000-0000-4000-8000-000000000006', '40000000-0000-4000-8000-000000000006', 'demo/biblioteca-modular', 'https://res.cloudinary.com/demo/image/upload/biblioteca-modular.jpg', 'Biblioteca modular para sala', 0, 1200, 900)
on conflict (id) do nothing;

insert into app.product_materials (product_id, material_id, is_default)
select p.id, m.id, m.code = 'MEL-18'
from app.products p
cross join app.materials m
where p.id::text like '40000000-0000-4000-8000-%'
on conflict (product_id, material_id) do nothing;

insert into app.product_finishes (product_id, finish_id, is_default)
select p.id, f.id, f.code = 'NATURAL'
from app.products p
cross join app.finishes f
where p.id::text like '40000000-0000-4000-8000-%'
on conflict (product_id, finish_id) do nothing;

insert into app.product_accessories (product_id, accessory_id, is_default)
select p.id, a.id, false
from app.products p
cross join app.accessories a
where p.id::text like '40000000-0000-4000-8000-%'
on conflict (product_id, accessory_id) do nothing;

insert into app.pricing_rules (
  id, name, version, priority, valid_from, conditions, operation, active, created_by
)
values (
  '50000000-0000-4000-8000-000000000001',
  'Ajuste por volumen', 1, 100, '2026-01-01T00:00:00Z',
  '{"field":"volumeMm3","operator":"greater_than","value":1000000000}',
  '{"type":"percentage","value":7.5}', true,
  '10000000-0000-4000-8000-000000000001'
)
on conflict (id) do nothing;

insert into app.quotes (
  id, code, customer_id, owner_user_id, contact_name, contact_email, contact_phone,
  status, subtotal_minor, adjustments_minor, total_minor, deposit_minor, expires_at, version
)
values
  (
    '60000000-0000-4000-8000-000000000001', 'COT-2026-0001',
    '20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000003',
    'Ana Torres', 'cliente.ana@example.test', '999111222', 'converted',
    120000, 0, 120000, 60000, '2026-12-01T00:00:00Z', 2
  ),
  (
    '60000000-0000-4000-8000-000000000002', 'COT-2026-0002',
    '20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000004',
    'Luis Ramos', 'cliente.luis@example.test', '999333444', 'converted',
    172000, 8000, 180000, 90000, '2026-12-01T00:00:00Z', 3
  ),
  (
    '60000000-0000-4000-8000-000000000003', 'COT-2026-0003',
    null, null, 'Visitante Demo', 'visitante@example.test', null, 'submitted',
    95000, 0, 95000, 47500, '2026-12-01T00:00:00Z', 1
  )
on conflict (id) do nothing;

insert into app.quote_items (
  id, quote_id, product_id, quantity, width_mm, height_mm, depth_mm,
  material_id, finish_id, accessories, configuration, product_name_snapshot,
  base_price_minor, calculation_breakdown, line_total_minor
)
values
  (
    '61000000-0000-4000-8000-000000000001', '60000000-0000-4000-8000-000000000001',
    '40000000-0000-4000-8000-000000000003', 1, 1800, 800, 450,
    '30000000-0000-4000-8000-000000000001', '31000000-0000-4000-8000-000000000002',
    '[{"code":"PASACABLE","quantity":1}]', '{"doors":2}', 'Centro TV Nogal',
    118000, '{"baseMinor":118000,"finishMinor":6500,"discountMinor":-4500}', 120000
  ),
  (
    '61000000-0000-4000-8000-000000000002', '60000000-0000-4000-8000-000000000002',
    '40000000-0000-4000-8000-000000000001', 1, 2000, 2200, 600,
    '30000000-0000-4000-8000-000000000002', '31000000-0000-4000-8000-000000000003',
    '[{"code":"LED-CALIDA","quantity":1}]', '{"doors":3,"drawers":2}', 'Ropero Andino',
    145000, '{"baseMinor":145000,"materialMinor":12000,"extrasMinor":23000}', 180000
  ),
  (
    '61000000-0000-4000-8000-000000000003', '60000000-0000-4000-8000-000000000003',
    '40000000-0000-4000-8000-000000000002', 1, 1400, 760, 600,
    '30000000-0000-4000-8000-000000000001', '31000000-0000-4000-8000-000000000001',
    '[{"code":"PASACABLE","quantity":1}]', '{"drawers":3}', 'Escritorio Lima',
    78000, '{"baseMinor":78000,"sizeMinor":14500,"accessoriesMinor":2500}', 95000
  )
on conflict (id) do nothing;

insert into app.orders (
  id, code, quote_id, customer_id, status, total_minor, deposit_required_minor,
  paid_minor, version, promised_date, delivery_address_snapshot
)
values
  (
    '70000000-0000-4000-8000-000000000001', 'PED-2026-0001',
    '60000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001',
    'cutting', 120000, 60000, 60000, 3, '2026-12-08',
    '{"address":"Av. Los Cedros 120","district":"Los Olivos","reference":"Frente al parque"}'
  ),
  (
    '70000000-0000-4000-8000-000000000002', 'PED-2026-0002',
    '60000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000002',
    'ready', 180000, 90000, 90000, 6, '2026-12-03',
    '{"address":"Jr. Las Flores 450","district":"San Martín de Porres","reference":"Piso 3"}'
  )
on conflict (id) do nothing;

insert into app.order_items (
  id, order_id, source_quote_item_id, product_id, product_name_snapshot, quantity,
  width_mm, height_mm, depth_mm, configuration_snapshot, unit_price_minor, line_total_minor
)
values
  (
    '71000000-0000-4000-8000-000000000001', '70000000-0000-4000-8000-000000000001',
    '61000000-0000-4000-8000-000000000001', '40000000-0000-4000-8000-000000000003',
    'Centro TV Nogal', 1, 1800, 800, 450,
    '{"material":"MEL-18","finish":"NOGAL","accessories":["PASACABLE"]}', 120000, 120000
  ),
  (
    '71000000-0000-4000-8000-000000000002', '70000000-0000-4000-8000-000000000002',
    '61000000-0000-4000-8000-000000000002', '40000000-0000-4000-8000-000000000001',
    'Ropero Andino', 1, 2000, 2200, 600,
    '{"material":"MDF-18","finish":"BLANCO","accessories":["LED-CALIDA"]}', 180000, 180000
  )
on conflict (id) do nothing;

insert into app.order_status_events (
  id, order_id, previous_status, new_status, actor_user_id, note, occurred_at
)
values
  ('72000000-0000-4000-8000-000000000001', '70000000-0000-4000-8000-000000000001', null, 'confirmed', '10000000-0000-4000-8000-000000000001', 'Pedido creado desde cotización', '2026-11-17T14:00:00Z'),
  ('72000000-0000-4000-8000-000000000002', '70000000-0000-4000-8000-000000000001', 'confirmed', 'materials_pending', '10000000-0000-4000-8000-000000000002', 'Material solicitado', '2026-11-18T14:00:00Z'),
  ('72000000-0000-4000-8000-000000000003', '70000000-0000-4000-8000-000000000001', 'materials_pending', 'cutting', '10000000-0000-4000-8000-000000000002', 'Inicio de corte', '2026-11-20T14:00:00Z'),
  ('72000000-0000-4000-8000-000000000004', '70000000-0000-4000-8000-000000000002', null, 'confirmed', '10000000-0000-4000-8000-000000000001', 'Pedido creado desde cotización', '2026-11-10T14:00:00Z'),
  ('72000000-0000-4000-8000-000000000005', '70000000-0000-4000-8000-000000000002', 'confirmed', 'assembly', '10000000-0000-4000-8000-000000000002', 'Armado iniciado', '2026-11-14T14:00:00Z'),
  ('72000000-0000-4000-8000-000000000006', '70000000-0000-4000-8000-000000000002', 'assembly', 'finishing', '10000000-0000-4000-8000-000000000002', 'Aplicación de acabado', '2026-11-18T14:00:00Z'),
  ('72000000-0000-4000-8000-000000000007', '70000000-0000-4000-8000-000000000002', 'finishing', 'ready', '10000000-0000-4000-8000-000000000002', 'Listo para entrega', '2026-11-21T14:00:00Z')
on conflict (id) do nothing;

insert into app.production_jobs (
  id, order_id, stage, priority, complexity, estimated_hours, actual_hours,
  planned_start_at, planned_end_at, actual_start_at, actual_end_at
)
values
  ('73000000-0000-4000-8000-000000000001', '70000000-0000-4000-8000-000000000001', 'cutting', 20, 1.400, 8, 3.5, '2026-11-20T13:00:00Z', '2026-11-21T18:00:00Z', '2026-11-20T14:00:00Z', null),
  ('73000000-0000-4000-8000-000000000002', '70000000-0000-4000-8000-000000000001', 'assembly', 30, 1.700, 12, null, '2026-11-22T13:00:00Z', '2026-11-24T18:00:00Z', null, null),
  ('73000000-0000-4000-8000-000000000003', '70000000-0000-4000-8000-000000000002', 'assembly', 10, 2.200, 18, 17.5, '2026-11-13T13:00:00Z', '2026-11-16T18:00:00Z', '2026-11-14T14:00:00Z', '2026-11-16T17:30:00Z'),
  ('73000000-0000-4000-8000-000000000004', '70000000-0000-4000-8000-000000000002', 'finishing', 10, 1.800, 14, 15, '2026-11-17T13:00:00Z', '2026-11-20T18:00:00Z', '2026-11-18T14:00:00Z', '2026-11-21T12:00:00Z'),
  ('73000000-0000-4000-8000-000000000005', '70000000-0000-4000-8000-000000000002', 'ready', 10, 1.000, 1, 0.5, '2026-11-21T12:00:00Z', '2026-11-21T18:00:00Z', '2026-11-21T12:00:00Z', '2026-11-21T12:30:00Z')
on conflict (id) do nothing;

insert into app.deliveries (
  id, order_id, delivery_location_id, window_start_at, window_end_at,
  sequence, estimated_distance_m, status
)
values (
  '74000000-0000-4000-8000-000000000001', '70000000-0000-4000-8000-000000000002',
  '21000000-0000-4000-8000-000000000002', '2026-12-03T14:00:00Z', '2026-12-03T18:00:00Z',
  1, 12800, 'scheduled'
)
on conflict (id) do nothing;

insert into app.media_assets (
  id, provider, external_id, media_type, access, owner_user_id, content_hash, metadata
)
values
  ('80000000-0000-4000-8000-000000000001', 'cloudinary', 'demo/catalogo-portada', 'image/jpeg', 'public', null, 'demo-public-hash', '{"purpose":"catalog"}'),
  ('80000000-0000-4000-8000-000000000002', 'cloudinary', 'demo/voucher-ana-001', 'image/jpeg', 'private', '10000000-0000-4000-8000-000000000003', 'demo-private-hash-ana', '{"purpose":"payment_voucher"}'),
  ('80000000-0000-4000-8000-000000000003', 'cloudinary', 'demo/voucher-luis-001', 'image/jpeg', 'private', '10000000-0000-4000-8000-000000000004', 'demo-private-hash-luis', '{"purpose":"payment_voucher"}')
on conflict (id) do nothing;

insert into app.payments (
  id, order_id, amount_minor, method, reference, paid_at, status, actor_user_id,
  voucher_asset_id, idempotency_key, reverses_payment_id
)
values
  (
    '81000000-0000-4000-8000-000000000001', '70000000-0000-4000-8000-000000000001',
    60000, 'bank_transfer', 'DEMO-ANA-001', '2026-11-17T15:00:00Z', 'recorded',
    '10000000-0000-4000-8000-000000000002', '80000000-0000-4000-8000-000000000002',
    'demo-payment-order-1-deposit', null
  ),
  (
    '81000000-0000-4000-8000-000000000002', '70000000-0000-4000-8000-000000000002',
    90000, 'bank_transfer', 'DEMO-LUIS-ERR', '2026-11-10T15:00:00Z', 'voided',
    '10000000-0000-4000-8000-000000000002', '80000000-0000-4000-8000-000000000003',
    'demo-payment-order-2-voided', null
  ),
  (
    '81000000-0000-4000-8000-000000000003', '70000000-0000-4000-8000-000000000002',
    90000, 'bank_transfer', 'DEMO-LUIS-001', '2026-11-10T15:10:00Z', 'recorded',
    '10000000-0000-4000-8000-000000000001', '80000000-0000-4000-8000-000000000003',
    'demo-payment-order-2-corrected', '81000000-0000-4000-8000-000000000002'
  )
on conflict (id) do nothing;

insert into app.customer_events (
  id, event_name, customer_id, occurred_at, properties
)
values
  ('90000000-0000-4000-8000-000000000001', 'catalog_product_viewed', '20000000-0000-4000-8000-000000000001', '2026-11-16T12:00:00Z', '{"productSlug":"centro-tv-nogal"}'),
  ('90000000-0000-4000-8000-000000000002', 'quote_submitted', '20000000-0000-4000-8000-000000000002', '2026-11-09T12:00:00Z', '{"quoteCode":"COT-2026-0002"}')
on conflict (id) do nothing;

insert into app.audit_logs (
  id, actor_user_id, action, entity_type, entity_id, new_values, request_id, ip_hash, created_at
)
values (
  '91000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000001', 'quote.converted', 'quote',
  '60000000-0000-4000-8000-000000000001', '{"orderCode":"PED-2026-0001"}',
  '92000000-0000-4000-8000-000000000001', 'demo-ip-hash', '2026-11-17T14:00:00Z'
)
on conflict (id) do nothing;

commit;
