begin;

set local search_path = app, public, extensions;
select plan(17);

insert into app.products (
  id, slug, name, category, base_price_minor, active,
  min_production_days, max_production_days,
  min_width_mm, max_width_mm, min_height_mm, max_height_mm, min_depth_mm, max_depth_mm
) values (
  '40000000-0000-4000-8000-000000000099', 'producto-inactivo-test', 'Producto inactivo',
  'Prueba', 100, false, 1, 2, 1, 2, 1, 2, 1, 2
);

select set_config(
  'request.jwt.claims',
  '{"sub":"10000000-0000-4000-8000-000000000003","role":"authenticated"}',
  true
);
set local role authenticated;

select is((select count(*) from app.profiles), 1::bigint, 'customer sees only own profile');
select is((select count(*) from app.quotes), 1::bigint, 'customer sees only own quote');
select is((select count(*) from app.orders), 1::bigint, 'customer sees only own order');
select is((select count(*) from app.payments), 1::bigint, 'customer sees only payments for own order');
select is((select count(*) from app.products), 6::bigint, 'customer sees active catalog only');
select throws_ok(
  $$update app.profiles set role = 'admin' where user_id = '10000000-0000-4000-8000-000000000003'$$,
  '42501',
  null,
  'customer cannot change own role'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"10000000-0000-4000-8000-000000000004","role":"authenticated"}',
  true
);
set local role authenticated;

select is((select count(*) from app.quotes), 1::bigint, 'second customer sees only second customer quote');
select is((select count(*) from app.payments), 2::bigint, 'second customer sees only second customer payments');

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"10000000-0000-4000-8000-000000000002","role":"authenticated"}',
  true
);
set local role authenticated;

select is((select count(*) from app.orders), 2::bigint, 'operator sees all orders');
select is((select count(*) from app.quotes), 3::bigint, 'operator sees all quotes');
select is((select count(*) from app.pricing_rules), 0::bigint, 'operator cannot read pricing rules');
select is((select count(*) from app.audit_logs), 0::bigint, 'operator cannot read audit logs');
select is(
  (
    with changed as (
      update app.products set base_price_minor = 1
      where id = '40000000-0000-4000-8000-000000000001'
      returning 1
    )
    select count(*) from changed
  ),
  0::bigint,
  'operator cannot change catalog prices'
);
select is(
  (
    with removed as (
      delete from app.customers
      where id = '20000000-0000-4000-8000-000000000001'
      returning 1
    )
    select count(*) from removed
  ),
  0::bigint,
  'operator cannot delete customers'
);

reset role;
select set_config(
  'request.jwt.claims',
  '{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated"}',
  true
);
set local role authenticated;

select is((select count(*) from app.profiles), 4::bigint, 'administrator sees all profiles');
select is((select count(*) from app.products), 7::bigint, 'administrator sees inactive catalog entries');

reset role;
select set_config('request.jwt.claims', '{"role":"anon"}', true);
set local role anon;

select is((select count(*) from app.products), 6::bigint, 'visitor sees only active catalog');

select * from finish();
rollback;
