begin;

set local search_path = app, public, extensions;
select plan(12);

select throws_ok(
  $$insert into app.customers (full_name) values ('Sin contacto')$$,
  '23514',
  null,
  'customer requires email or phone'
);

select throws_ok(
  $$
    insert into app.delivery_locations (customer_id, label, address, district, latitude)
    values ('20000000-0000-4000-8000-000000000001', 'Inválida', 'Dirección', 'Distrito', -12.0)
  $$,
  '23514',
  null,
  'delivery coordinates must be a complete pair'
);

select throws_ok(
  $$
    insert into app.products (
      slug, name, category, base_price_minor, min_production_days, max_production_days,
      min_width_mm, max_width_mm, min_height_mm, max_height_mm, min_depth_mm, max_depth_mm
    ) values ('precio-invalido', 'Inválido', 'Prueba', -1, 1, 2, 1, 2, 1, 2, 1, 2)
  $$,
  '23514',
  null,
  'negative product price is rejected'
);

select throws_ok(
  $$
    insert into app.products (
      slug, name, category, base_price_minor, min_production_days, max_production_days,
      min_width_mm, max_width_mm, min_height_mm, max_height_mm, min_depth_mm, max_depth_mm
    ) values ('medida-invalida', 'Inválido', 'Prueba', 100, 1, 2, 100, 50, 1, 2, 1, 2)
  $$,
  '23514',
  null,
  'invalid product measurement range is rejected'
);

select throws_ok(
  $$
    update app.product_materials
    set is_default = true
    where product_id = '40000000-0000-4000-8000-000000000001'
      and material_id = '30000000-0000-4000-8000-000000000002'
  $$,
  '23505',
  null,
  'a product cannot have two default materials'
);

select throws_ok(
  $$
    insert into app.quotes (
      code, contact_name, contact_email, subtotal_minor, adjustments_minor,
      total_minor, deposit_minor, expires_at
    ) values ('COT-TEST-TOTAL', 'Prueba', 'quote@example.test', 1000, 200, 1000, 0, now() + interval '1 day')
  $$,
  '23514',
  null,
  'quote total must equal subtotal plus adjustments'
);

select throws_ok(
  $$
    insert into app.quotes (
      code, contact_name, contact_email, subtotal_minor, total_minor, deposit_minor,
      created_at, expires_at
    ) values ('COT-TEST-DATE', 'Prueba', 'quote@example.test', 1000, 1000, 0, now(), now() - interval '1 day')
  $$,
  '23514',
  null,
  'quote expiration must follow creation'
);

select throws_ok(
  $$
    insert into app.quote_items (
      quote_id, product_id, quantity, width_mm, height_mm, depth_mm,
      product_name_snapshot, base_price_minor, calculation_breakdown, line_total_minor
    ) values (
      '60000000-0000-4000-8000-000000000003', '40000000-0000-4000-8000-000000000002',
      1, 0, 700, 500, 'Inválido', 100, '{}', 100
    )
  $$,
  '23514',
  null,
  'zero quote item measurement is rejected'
);

select throws_ok(
  $$
    update app.orders set paid_minor = total_minor + 1
    where id = '70000000-0000-4000-8000-000000000001'
  $$,
  '23514',
  null,
  'order cannot be overpaid'
);

select throws_ok(
  $$
    insert into app.payments (
      order_id, amount_minor, method, paid_at, idempotency_key
    ) values (
      '70000000-0000-4000-8000-000000000001', 0, 'cash', now(), 'test-zero-payment'
    )
  $$,
  '23514',
  null,
  'payment amount must be positive'
);

select throws_ok(
  $$
    insert into app.payments (
      order_id, amount_minor, method, paid_at, idempotency_key
    ) values (
      '70000000-0000-4000-8000-000000000001', 100, 'cash', now(), 'demo-payment-order-1-deposit'
    )
  $$,
  '23505',
  null,
  'duplicate payment idempotency key is rejected'
);

select throws_ok(
  $$
    update app.order_status_events set note = 'No permitido'
    where id = '72000000-0000-4000-8000-000000000001'
  $$,
  '55000',
  null,
  'order status history is append-only'
);

select * from finish();
rollback;
