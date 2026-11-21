begin;

set local search_path = app, public, extensions;
select plan(39);

select has_schema('app', 'business schema exists');

select has_type('app', 'user_role', 'user_role enum exists');
select has_type('app', 'quote_status', 'quote_status enum exists');
select has_type('app', 'order_status', 'order_status enum exists');
select has_type('app', 'payment_status', 'payment_status enum exists');
select has_type('app', 'payment_method', 'payment_method enum exists');
select has_type('app', 'asset_access', 'asset_access enum exists');
select has_type('app', 'model_status', 'model_status enum exists');

select has_table('app', 'profiles', 'profiles table exists');
select has_table('app', 'customers', 'customers table exists');
select has_table('app', 'delivery_locations', 'delivery_locations table exists');
select has_table('app', 'products', 'products table exists');
select has_table('app', 'product_images', 'product_images table exists');
select has_table('app', 'materials', 'materials table exists');
select has_table('app', 'finishes', 'finishes table exists');
select has_table('app', 'accessories', 'accessories table exists');
select has_table('app', 'product_materials', 'product_materials table exists');
select has_table('app', 'product_finishes', 'product_finishes table exists');
select has_table('app', 'product_accessories', 'product_accessories table exists');
select has_table('app', 'pricing_rules', 'pricing_rules table exists');
select has_table('app', 'quotes', 'quotes table exists');
select has_table('app', 'quote_items', 'quote_items table exists');
select has_table('app', 'orders', 'orders table exists');
select has_table('app', 'order_items', 'order_items table exists');
select has_table('app', 'order_status_events', 'order_status_events table exists');
select has_table('app', 'production_jobs', 'production_jobs table exists');
select has_table('app', 'deliveries', 'deliveries table exists');
select has_table('app', 'media_assets', 'media_assets table exists');
select has_table('app', 'payments', 'payments table exists');
select has_table('app', 'customer_events', 'customer_events table exists');
select has_table('app', 'model_versions', 'model_versions table exists');
select has_table('app', 'predictions', 'predictions table exists');
select has_table('app', 'optimization_runs', 'optimization_runs table exists');
select has_table('app', 'audit_logs', 'audit_logs table exists');

select ok(
  (
    select count(*) = 7
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'app'
      and p.proname in (
        'set_updated_at', 'reject_mutation', 'handle_new_auth_user',
        'current_user_role', 'is_admin', 'is_staff', 'owns_customer'
      )
  ),
  'database helper functions exist'
);

select ok(
  (
    select count(*) = 26 and bool_and(c.relrowsecurity)
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'app' and c.relkind = 'r'
  ),
  'RLS is enabled on every business table'
);

select is(
  (select count(*) from app.products),
  6::bigint,
  'seed contains six products'
);

select is(
  (select count(*) from auth.users where email like '%.test'),
  4::bigint,
  'seed contains four fictitious auth identities'
);

select ok(
  not exists (
    select p.id
    from app.products p
    left join app.product_materials pm on pm.product_id = p.id and pm.is_default
    left join app.product_finishes pf on pf.product_id = p.id and pf.is_default
    group by p.id
    having count(distinct pm.material_id) <> 1 or count(distinct pf.finish_id) <> 1
  ),
  'every seeded product has one default material and finish'
);

select * from finish();
rollback;
