begin;

create extension if not exists pgcrypto with schema extensions;
create extension if not exists citext with schema extensions;
create extension if not exists pgtap with schema extensions;

create schema if not exists app;
revoke all on schema app from public;

create type app.user_role as enum ('customer', 'operator', 'admin');
create type app.quote_status as enum (
  'draft', 'submitted', 'reviewing', 'approved', 'rejected', 'expired', 'converted'
);
create type app.order_status as enum (
  'confirmed', 'materials_pending', 'cutting', 'assembly', 'finishing',
  'ready', 'delivered', 'installed', 'cancelled'
);
create type app.payment_status as enum ('recorded', 'voided');
create type app.payment_method as enum ('cash', 'bank_transfer', 'card', 'other');
create type app.asset_access as enum ('public', 'private');
create type app.model_status as enum ('candidate', 'approved', 'active', 'retired');

create function app.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create function app.reject_mutation()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception '% is append-only', tg_table_name using errcode = '55000';
end;
$$;

create table app.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  phone text,
  role app.user_role not null default 'customer',
  active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint profiles_full_name_not_blank check (full_name is null or btrim(full_name) <> ''),
  constraint profiles_phone_not_blank check (phone is null or btrim(phone) <> '')
);

create table app.customers (
  id uuid primary key default gen_random_uuid(),
  profile_user_id uuid unique references app.profiles(user_id) on delete set null,
  full_name text not null,
  email extensions.citext,
  phone text,
  document_number text,
  address text,
  district text,
  notes text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint customers_full_name_not_blank check (btrim(full_name) <> ''),
  constraint customers_contact_required check (
    nullif(btrim(email::text), '') is not null or nullif(btrim(phone), '') is not null
  ),
  constraint customers_email_not_blank check (email is null or btrim(email::text) <> ''),
  constraint customers_phone_not_blank check (phone is null or btrim(phone) <> '')
);

create unique index customers_email_unique_idx
  on app.customers (lower(email::text)) where email is not null;

create table app.delivery_locations (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references app.customers(id) on delete restrict,
  label text not null,
  address text not null,
  district text not null,
  reference text,
  latitude numeric(9, 6),
  longitude numeric(9, 6),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint delivery_locations_label_not_blank check (btrim(label) <> ''),
  constraint delivery_locations_address_not_blank check (btrim(address) <> ''),
  constraint delivery_locations_district_not_blank check (btrim(district) <> ''),
  constraint delivery_locations_coordinates_pair check (
    (latitude is null and longitude is null) or (latitude is not null and longitude is not null)
  ),
  constraint delivery_locations_latitude_range check (latitude is null or latitude between -90 and 90),
  constraint delivery_locations_longitude_range check (longitude is null or longitude between -180 and 180)
);

create table app.products (
  id uuid primary key default gen_random_uuid(),
  slug extensions.citext not null unique,
  name text not null,
  description text not null default '',
  category text not null,
  base_price_minor bigint not null,
  active boolean not null default true,
  min_production_days integer not null,
  max_production_days integer not null,
  min_width_mm integer not null,
  max_width_mm integer not null,
  min_height_mm integer not null,
  max_height_mm integer not null,
  min_depth_mm integer not null,
  max_depth_mm integer not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint products_slug_not_blank check (btrim(slug::text) <> ''),
  constraint products_name_not_blank check (btrim(name) <> ''),
  constraint products_category_not_blank check (btrim(category) <> ''),
  constraint products_base_price_nonnegative check (base_price_minor >= 0),
  constraint products_production_days_valid check (
    min_production_days > 0 and max_production_days >= min_production_days
  ),
  constraint products_width_range_valid check (min_width_mm > 0 and max_width_mm >= min_width_mm),
  constraint products_height_range_valid check (min_height_mm > 0 and max_height_mm >= min_height_mm),
  constraint products_depth_range_valid check (min_depth_mm > 0 and max_depth_mm >= min_depth_mm)
);

create table app.product_images (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references app.products(id) on delete restrict,
  public_id text not null unique,
  secure_url text not null,
  alt_text text not null,
  position integer not null,
  width integer,
  height integer,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint product_images_public_id_not_blank check (btrim(public_id) <> ''),
  constraint product_images_secure_url_https check (secure_url ~ '^https://'),
  constraint product_images_alt_text_not_blank check (btrim(alt_text) <> ''),
  constraint product_images_position_nonnegative check (position >= 0),
  constraint product_images_dimensions_positive check (
    (width is null or width > 0) and (height is null or height > 0)
  ),
  constraint product_images_metadata_object check (jsonb_typeof(metadata) = 'object'),
  unique (product_id, position)
);

create table app.materials (
  id uuid primary key default gen_random_uuid(),
  code extensions.citext not null unique,
  name text not null,
  description text not null default '',
  price_adjustment_minor bigint not null default 0,
  price_adjustment_percent numeric(7, 4) not null default 0,
  active boolean not null default true,
  available boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint materials_code_not_blank check (btrim(code::text) <> ''),
  constraint materials_name_not_blank check (btrim(name) <> ''),
  constraint materials_adjustment_mode check (
    price_adjustment_minor = 0 or price_adjustment_percent = 0
  )
);

create table app.finishes (
  id uuid primary key default gen_random_uuid(),
  code extensions.citext not null unique,
  name text not null,
  description text not null default '',
  price_adjustment_minor bigint not null default 0,
  price_adjustment_percent numeric(7, 4) not null default 0,
  active boolean not null default true,
  available boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint finishes_code_not_blank check (btrim(code::text) <> ''),
  constraint finishes_name_not_blank check (btrim(name) <> ''),
  constraint finishes_adjustment_mode check (
    price_adjustment_minor = 0 or price_adjustment_percent = 0
  )
);

create table app.accessories (
  id uuid primary key default gen_random_uuid(),
  code extensions.citext not null unique,
  name text not null,
  description text not null default '',
  price_adjustment_minor bigint not null default 0,
  price_adjustment_percent numeric(7, 4) not null default 0,
  active boolean not null default true,
  available boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint accessories_code_not_blank check (btrim(code::text) <> ''),
  constraint accessories_name_not_blank check (btrim(name) <> ''),
  constraint accessories_adjustment_mode check (
    price_adjustment_minor = 0 or price_adjustment_percent = 0
  )
);

create table app.product_materials (
  product_id uuid not null references app.products(id) on delete restrict,
  material_id uuid not null references app.materials(id) on delete restrict,
  is_default boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (product_id, material_id)
);

create unique index product_materials_one_default_idx
  on app.product_materials (product_id) where is_default;

create table app.product_finishes (
  product_id uuid not null references app.products(id) on delete restrict,
  finish_id uuid not null references app.finishes(id) on delete restrict,
  is_default boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (product_id, finish_id)
);

create unique index product_finishes_one_default_idx
  on app.product_finishes (product_id) where is_default;

create table app.product_accessories (
  product_id uuid not null references app.products(id) on delete restrict,
  accessory_id uuid not null references app.accessories(id) on delete restrict,
  is_default boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  primary key (product_id, accessory_id)
);

create unique index product_accessories_one_default_idx
  on app.product_accessories (product_id) where is_default;

create table app.pricing_rules (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  version integer not null,
  priority integer not null default 100,
  valid_from timestamptz not null,
  valid_until timestamptz,
  conditions jsonb not null,
  operation jsonb not null,
  active boolean not null default true,
  created_by uuid references app.profiles(user_id) on delete restrict,
  created_at timestamptz not null default timezone('utc', now()),
  constraint pricing_rules_name_not_blank check (btrim(name) <> ''),
  constraint pricing_rules_version_positive check (version > 0),
  constraint pricing_rules_priority_nonnegative check (priority >= 0),
  constraint pricing_rules_dates_valid check (valid_until is null or valid_until > valid_from),
  constraint pricing_rules_conditions_object check (jsonb_typeof(conditions) = 'object'),
  constraint pricing_rules_operation_object check (jsonb_typeof(operation) = 'object'),
  unique (name, version)
);

create table app.quotes (
  id uuid primary key default gen_random_uuid(),
  code extensions.citext not null unique,
  customer_id uuid references app.customers(id) on delete restrict,
  owner_user_id uuid references app.profiles(user_id) on delete set null,
  contact_name text not null,
  contact_email extensions.citext,
  contact_phone text,
  status app.quote_status not null default 'draft',
  currency char(3) not null default 'PEN',
  subtotal_minor bigint not null default 0,
  adjustments_minor bigint not null default 0,
  total_minor bigint not null default 0,
  deposit_minor bigint not null default 0,
  expires_at timestamptz not null default (timezone('utc', now()) + interval '7 days'),
  version integer not null default 1,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint quotes_code_not_blank check (btrim(code::text) <> ''),
  constraint quotes_contact_name_not_blank check (btrim(contact_name) <> ''),
  constraint quotes_contact_required check (
    nullif(btrim(contact_email::text), '') is not null or nullif(btrim(contact_phone), '') is not null
  ),
  constraint quotes_currency_pen check (currency = 'PEN'),
  constraint quotes_subtotal_nonnegative check (subtotal_minor >= 0),
  constraint quotes_total_nonnegative check (total_minor >= 0),
  constraint quotes_deposit_valid check (deposit_minor >= 0 and deposit_minor <= total_minor),
  constraint quotes_total_matches check (total_minor = subtotal_minor + adjustments_minor),
  constraint quotes_version_positive check (version > 0),
  constraint quotes_expiration_after_creation check (expires_at > created_at)
);

create table app.quote_items (
  id uuid primary key default gen_random_uuid(),
  quote_id uuid not null references app.quotes(id) on delete cascade,
  product_id uuid not null references app.products(id) on delete restrict,
  quantity integer not null,
  width_mm integer not null,
  height_mm integer not null,
  depth_mm integer not null,
  material_id uuid references app.materials(id) on delete restrict,
  finish_id uuid references app.finishes(id) on delete restrict,
  accessories jsonb not null default '[]'::jsonb,
  configuration jsonb not null default '{}'::jsonb,
  product_name_snapshot text not null,
  base_price_minor bigint not null,
  calculation_breakdown jsonb not null,
  line_total_minor bigint not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint quote_items_quantity_positive check (quantity > 0),
  constraint quote_items_dimensions_positive check (width_mm > 0 and height_mm > 0 and depth_mm > 0),
  constraint quote_items_product_name_not_blank check (btrim(product_name_snapshot) <> ''),
  constraint quote_items_amounts_nonnegative check (base_price_minor >= 0 and line_total_minor >= 0),
  constraint quote_items_accessories_array check (jsonb_typeof(accessories) = 'array'),
  constraint quote_items_configuration_object check (jsonb_typeof(configuration) = 'object'),
  constraint quote_items_breakdown_object check (jsonb_typeof(calculation_breakdown) = 'object')
);

create table app.orders (
  id uuid primary key default gen_random_uuid(),
  code extensions.citext not null unique,
  quote_id uuid not null unique references app.quotes(id) on delete restrict,
  customer_id uuid not null references app.customers(id) on delete restrict,
  status app.order_status not null default 'confirmed',
  currency char(3) not null default 'PEN',
  total_minor bigint not null,
  deposit_required_minor bigint not null,
  paid_minor bigint not null default 0,
  balance_minor bigint generated always as (total_minor - paid_minor) stored,
  version integer not null default 1,
  promised_date date,
  delivered_at timestamptz,
  installed_at timestamptz,
  delivery_address_snapshot jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint orders_code_not_blank check (btrim(code::text) <> ''),
  constraint orders_currency_pen check (currency = 'PEN'),
  constraint orders_amounts_valid check (
    total_minor >= 0 and deposit_required_minor >= 0 and deposit_required_minor <= total_minor
    and paid_minor >= 0 and paid_minor <= total_minor
  ),
  constraint orders_version_positive check (version > 0),
  constraint orders_delivery_address_object check (jsonb_typeof(delivery_address_snapshot) = 'object'),
  constraint orders_installation_after_delivery check (
    installed_at is null or (delivered_at is not null and installed_at >= delivered_at)
  )
);

create table app.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references app.orders(id) on delete restrict,
  source_quote_item_id uuid references app.quote_items(id) on delete restrict,
  product_id uuid references app.products(id) on delete restrict,
  product_name_snapshot text not null,
  quantity integer not null,
  width_mm integer not null,
  height_mm integer not null,
  depth_mm integer not null,
  configuration_snapshot jsonb not null,
  unit_price_minor bigint not null,
  line_total_minor bigint not null,
  created_at timestamptz not null default timezone('utc', now()),
  constraint order_items_name_not_blank check (btrim(product_name_snapshot) <> ''),
  constraint order_items_quantity_positive check (quantity > 0),
  constraint order_items_dimensions_positive check (width_mm > 0 and height_mm > 0 and depth_mm > 0),
  constraint order_items_amounts_nonnegative check (unit_price_minor >= 0 and line_total_minor >= 0),
  constraint order_items_configuration_object check (jsonb_typeof(configuration_snapshot) = 'object')
);

create table app.order_status_events (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references app.orders(id) on delete restrict,
  previous_status app.order_status,
  new_status app.order_status not null,
  actor_user_id uuid references app.profiles(user_id) on delete set null,
  note text,
  occurred_at timestamptz not null default timezone('utc', now()),
  constraint order_status_events_transition check (
    previous_status is null or previous_status <> new_status
  )
);

create table app.production_jobs (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references app.orders(id) on delete restrict,
  stage app.order_status not null,
  priority integer not null default 100,
  complexity numeric(8, 3) not null default 1,
  estimated_hours numeric(10, 2) not null,
  actual_hours numeric(10, 2),
  planned_start_at timestamptz,
  planned_end_at timestamptz,
  actual_start_at timestamptz,
  actual_end_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint production_jobs_priority_nonnegative check (priority >= 0),
  constraint production_jobs_complexity_positive check (complexity > 0),
  constraint production_jobs_hours_valid check (estimated_hours >= 0 and (actual_hours is null or actual_hours >= 0)),
  constraint production_jobs_planned_dates_valid check (
    planned_end_at is null or (planned_start_at is not null and planned_end_at >= planned_start_at)
  ),
  constraint production_jobs_actual_dates_valid check (
    actual_end_at is null or (actual_start_at is not null and actual_end_at >= actual_start_at)
  )
);

create table app.deliveries (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references app.orders(id) on delete restrict,
  delivery_location_id uuid references app.delivery_locations(id) on delete restrict,
  window_start_at timestamptz not null,
  window_end_at timestamptz not null,
  sequence integer,
  estimated_distance_m integer,
  status text not null default 'scheduled',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint deliveries_window_valid check (window_end_at > window_start_at),
  constraint deliveries_sequence_positive check (sequence is null or sequence > 0),
  constraint deliveries_distance_nonnegative check (estimated_distance_m is null or estimated_distance_m >= 0),
  constraint deliveries_status_valid check (status in ('scheduled', 'in_transit', 'delivered', 'cancelled'))
);

create table app.media_assets (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  external_id text not null,
  media_type text not null,
  access app.asset_access not null,
  owner_user_id uuid references app.profiles(user_id) on delete set null,
  content_hash text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint media_assets_provider_not_blank check (btrim(provider) <> ''),
  constraint media_assets_external_id_not_blank check (btrim(external_id) <> ''),
  constraint media_assets_type_not_blank check (btrim(media_type) <> ''),
  constraint media_assets_metadata_object check (jsonb_typeof(metadata) = 'object'),
  unique (provider, external_id)
);

create table app.payments (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references app.orders(id) on delete restrict,
  amount_minor bigint not null,
  currency char(3) not null default 'PEN',
  method app.payment_method not null,
  reference text,
  paid_at timestamptz not null,
  status app.payment_status not null default 'recorded',
  actor_user_id uuid references app.profiles(user_id) on delete set null,
  voucher_asset_id uuid references app.media_assets(id) on delete restrict,
  idempotency_key text not null unique,
  reverses_payment_id uuid unique references app.payments(id) on delete restrict,
  created_at timestamptz not null default timezone('utc', now()),
  constraint payments_amount_positive check (amount_minor > 0),
  constraint payments_currency_pen check (currency = 'PEN'),
  constraint payments_idempotency_key_not_blank check (btrim(idempotency_key) <> ''),
  constraint payments_not_self_reversal check (reverses_payment_id is null or reverses_payment_id <> id)
);

create table app.customer_events (
  id uuid primary key default gen_random_uuid(),
  event_name text not null,
  customer_id uuid references app.customers(id) on delete restrict,
  anonymous_session_id uuid,
  occurred_at timestamptz not null default timezone('utc', now()),
  properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  constraint customer_events_name_not_blank check (btrim(event_name) <> ''),
  constraint customer_events_subject_required check (
    (customer_id is not null and anonymous_session_id is null)
    or (customer_id is null and anonymous_session_id is not null)
  ),
  constraint customer_events_properties_object check (jsonb_typeof(properties) = 'object')
);

create table app.model_versions (
  id uuid primary key default gen_random_uuid(),
  problem text not null,
  algorithm text not null,
  version integer not null,
  artifact_path text not null,
  artifact_hash text not null,
  parameters jsonb not null default '{}'::jsonb,
  metrics jsonb not null default '{}'::jsonb,
  status app.model_status not null default 'candidate',
  created_by uuid references app.profiles(user_id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint model_versions_problem_not_blank check (btrim(problem) <> ''),
  constraint model_versions_algorithm_not_blank check (btrim(algorithm) <> ''),
  constraint model_versions_version_positive check (version > 0),
  constraint model_versions_artifact_not_blank check (btrim(artifact_path) <> '' and btrim(artifact_hash) <> ''),
  constraint model_versions_parameters_object check (jsonb_typeof(parameters) = 'object'),
  constraint model_versions_metrics_object check (jsonb_typeof(metrics) = 'object'),
  unique (problem, algorithm, version)
);

create unique index model_versions_one_active_per_problem_idx
  on app.model_versions (problem) where status = 'active';

create table app.predictions (
  id uuid primary key default gen_random_uuid(),
  model_version_id uuid not null references app.model_versions(id) on delete restrict,
  entity_type text not null,
  entity_id uuid not null,
  input_summary jsonb not null,
  output jsonb not null,
  confidence numeric(6, 5),
  actual_outcome jsonb,
  predicted_at timestamptz not null default timezone('utc', now()),
  evaluated_at timestamptz,
  constraint predictions_entity_type_not_blank check (btrim(entity_type) <> ''),
  constraint predictions_input_object check (jsonb_typeof(input_summary) = 'object'),
  constraint predictions_output_object check (jsonb_typeof(output) = 'object'),
  constraint predictions_confidence_range check (confidence is null or confidence between 0 and 1),
  constraint predictions_actual_outcome_object check (
    actual_outcome is null or jsonb_typeof(actual_outcome) = 'object'
  ),
  constraint predictions_evaluated_after_prediction check (
    evaluated_at is null or evaluated_at >= predicted_at
  )
);

create table app.optimization_runs (
  id uuid primary key default gen_random_uuid(),
  algorithm text not null,
  input jsonb not null,
  baseline jsonb not null,
  result jsonb not null,
  improvement numeric(12, 5) not null,
  random_seed bigint,
  duration_ms integer not null,
  requested_by uuid references app.profiles(user_id) on delete set null,
  accepted boolean,
  created_at timestamptz not null default timezone('utc', now()),
  constraint optimization_runs_algorithm_valid check (algorithm in ('astar', 'hill_climbing')),
  constraint optimization_runs_input_object check (jsonb_typeof(input) = 'object'),
  constraint optimization_runs_baseline_object check (jsonb_typeof(baseline) = 'object'),
  constraint optimization_runs_result_object check (jsonb_typeof(result) = 'object'),
  constraint optimization_runs_duration_nonnegative check (duration_ms >= 0)
);

create table app.audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid references app.profiles(user_id) on delete set null,
  action text not null,
  entity_type text not null,
  entity_id uuid,
  old_values jsonb,
  new_values jsonb,
  request_id uuid,
  ip_hash text,
  created_at timestamptz not null default timezone('utc', now()),
  constraint audit_logs_action_not_blank check (btrim(action) <> ''),
  constraint audit_logs_entity_type_not_blank check (btrim(entity_type) <> ''),
  constraint audit_logs_old_values_object check (old_values is null or jsonb_typeof(old_values) = 'object'),
  constraint audit_logs_new_values_object check (new_values is null or jsonb_typeof(new_values) = 'object')
);

create function app.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into app.profiles (user_id, full_name, phone, role)
  values (
    new.id,
    nullif(btrim(new.raw_user_meta_data ->> 'full_name'), ''),
    nullif(btrim(new.phone), ''),
    'customer'
  )
  on conflict (user_id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute function app.handle_new_auth_user();

create function app.current_user_role()
returns app.user_role
language sql
stable
security definer
set search_path = ''
as $$
  select p.role
  from app.profiles p
  where p.user_id = (select auth.uid()) and p.active;
$$;

create function app.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce((select app.current_user_role()) = 'admin', false);
$$;

create function app.is_staff()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce((select app.current_user_role()) in ('operator', 'admin'), false);
$$;

create function app.owns_customer(target_customer_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from app.customers c
    where c.id = target_customer_id and c.profile_user_id = (select auth.uid())
  );
$$;

create function app.can_read_order(target_order_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select (select app.is_staff()) or exists (
    select 1
    from app.orders o
    join app.customers c on c.id = o.customer_id
    where o.id = target_order_id and c.profile_user_id = (select auth.uid())
  );
$$;

create index delivery_locations_customer_id_idx on app.delivery_locations(customer_id);
create index product_images_product_id_idx on app.product_images(product_id);
create index product_materials_material_id_idx on app.product_materials(material_id);
create index product_finishes_finish_id_idx on app.product_finishes(finish_id);
create index product_accessories_accessory_id_idx on app.product_accessories(accessory_id);
create index pricing_rules_created_by_idx on app.pricing_rules(created_by);
create index pricing_rules_active_dates_idx on app.pricing_rules(active, valid_from, valid_until);
create index quotes_customer_id_idx on app.quotes(customer_id);
create index quotes_owner_user_id_idx on app.quotes(owner_user_id);
create index quotes_status_created_at_idx on app.quotes(status, created_at desc);
create index quotes_expires_at_idx on app.quotes(expires_at);
create index quote_items_quote_id_idx on app.quote_items(quote_id);
create index quote_items_product_id_idx on app.quote_items(product_id);
create index quote_items_material_id_idx on app.quote_items(material_id);
create index quote_items_finish_id_idx on app.quote_items(finish_id);
create index orders_customer_id_idx on app.orders(customer_id);
create index orders_status_created_at_idx on app.orders(status, created_at desc);
create index orders_open_idx on app.orders(created_at desc)
  where status not in ('installed', 'cancelled');
create index order_items_order_id_idx on app.order_items(order_id);
create index order_items_source_quote_item_id_idx on app.order_items(source_quote_item_id);
create index order_items_product_id_idx on app.order_items(product_id);
create index order_status_events_order_occurred_idx on app.order_status_events(order_id, occurred_at);
create index order_status_events_actor_idx on app.order_status_events(actor_user_id);
create index production_jobs_order_id_idx on app.production_jobs(order_id);
create index production_jobs_stage_planned_idx on app.production_jobs(stage, planned_start_at);
create index deliveries_order_id_idx on app.deliveries(order_id);
create index deliveries_location_id_idx on app.deliveries(delivery_location_id);
create index deliveries_status_window_idx on app.deliveries(status, window_start_at);
create index media_assets_owner_user_id_idx on app.media_assets(owner_user_id);
create index payments_order_paid_at_idx on app.payments(order_id, paid_at desc);
create index payments_actor_user_id_idx on app.payments(actor_user_id);
create index payments_voucher_asset_id_idx on app.payments(voucher_asset_id);
create index payments_status_paid_at_idx on app.payments(status, paid_at desc);
create index customer_events_customer_occurred_idx on app.customer_events(customer_id, occurred_at desc);
create index customer_events_session_idx on app.customer_events(anonymous_session_id);
create index model_versions_created_by_idx on app.model_versions(created_by);
create index predictions_model_version_id_idx on app.predictions(model_version_id);
create index predictions_entity_idx on app.predictions(entity_type, entity_id);
create index optimization_runs_requested_by_idx on app.optimization_runs(requested_by);
create index optimization_runs_algorithm_created_idx on app.optimization_runs(algorithm, created_at desc);
create index audit_logs_actor_user_id_idx on app.audit_logs(actor_user_id);
create index audit_logs_entity_idx on app.audit_logs(entity_type, entity_id, created_at desc);
create index audit_logs_request_id_idx on app.audit_logs(request_id);
create index products_active_idx on app.products(category, name) where active;

do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'profiles', 'customers', 'delivery_locations', 'products', 'product_images',
    'materials', 'finishes', 'accessories', 'pricing_rules', 'quotes', 'quote_items',
    'orders', 'production_jobs', 'deliveries', 'media_assets', 'model_versions'
  ]
  loop
    execute format(
      'create trigger %I before update on app.%I for each row execute function app.set_updated_at()',
      table_name || '_set_updated_at', table_name
    );
  end loop;
end;
$$;

create trigger order_status_events_append_only
before update or delete on app.order_status_events
for each row execute function app.reject_mutation();

create trigger order_items_immutable
before update or delete on app.order_items
for each row execute function app.reject_mutation();

create trigger audit_logs_append_only
before update or delete on app.audit_logs
for each row execute function app.reject_mutation();

create trigger payments_no_delete
before delete on app.payments
for each row execute function app.reject_mutation();

alter table app.profiles enable row level security;
alter table app.customers enable row level security;
alter table app.delivery_locations enable row level security;
alter table app.products enable row level security;
alter table app.product_images enable row level security;
alter table app.materials enable row level security;
alter table app.finishes enable row level security;
alter table app.accessories enable row level security;
alter table app.product_materials enable row level security;
alter table app.product_finishes enable row level security;
alter table app.product_accessories enable row level security;
alter table app.pricing_rules enable row level security;
alter table app.quotes enable row level security;
alter table app.quote_items enable row level security;
alter table app.orders enable row level security;
alter table app.order_items enable row level security;
alter table app.order_status_events enable row level security;
alter table app.production_jobs enable row level security;
alter table app.deliveries enable row level security;
alter table app.media_assets enable row level security;
alter table app.payments enable row level security;
alter table app.customer_events enable row level security;
alter table app.model_versions enable row level security;
alter table app.predictions enable row level security;
alter table app.optimization_runs enable row level security;
alter table app.audit_logs enable row level security;

create policy profiles_select on app.profiles for select to authenticated
  using (user_id = (select auth.uid()) or (select app.is_admin()));
create policy profiles_update_own on app.profiles for update to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

create policy customers_select on app.customers for select to authenticated
  using (profile_user_id = (select auth.uid()) or (select app.is_staff()));
create policy customers_admin_manage on app.customers for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy delivery_locations_select on app.delivery_locations for select to authenticated
  using ((select app.owns_customer(customer_id)) or (select app.is_staff()));
create policy delivery_locations_admin_manage on app.delivery_locations for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy products_public_select on app.products for select to anon, authenticated
  using (active);
create policy products_admin_manage on app.products for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy product_images_public_select on app.product_images for select to anon, authenticated
  using (exists (select 1 from app.products p where p.id = product_id and p.active));
create policy product_images_admin_manage on app.product_images for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy materials_public_select on app.materials for select to anon, authenticated
  using (active and available);
create policy materials_admin_manage on app.materials for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));
create policy finishes_public_select on app.finishes for select to anon, authenticated
  using (active and available);
create policy finishes_admin_manage on app.finishes for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));
create policy accessories_public_select on app.accessories for select to anon, authenticated
  using (active and available);
create policy accessories_admin_manage on app.accessories for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy product_materials_public_select on app.product_materials for select to anon, authenticated
  using (exists (select 1 from app.products p where p.id = product_id and p.active));
create policy product_materials_admin_manage on app.product_materials for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));
create policy product_finishes_public_select on app.product_finishes for select to anon, authenticated
  using (exists (select 1 from app.products p where p.id = product_id and p.active));
create policy product_finishes_admin_manage on app.product_finishes for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));
create policy product_accessories_public_select on app.product_accessories for select to anon, authenticated
  using (exists (select 1 from app.products p where p.id = product_id and p.active));
create policy product_accessories_admin_manage on app.product_accessories for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy pricing_rules_admin_all on app.pricing_rules for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy quotes_select on app.quotes for select to authenticated
  using (
    owner_user_id = (select auth.uid())
    or (customer_id is not null and (select app.owns_customer(customer_id)))
    or (select app.is_staff())
  );
create policy quotes_admin_manage on app.quotes for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));
create policy quote_items_select on app.quote_items for select to authenticated
  using (exists (
    select 1 from app.quotes q
    where q.id = quote_id and (
      q.owner_user_id = (select auth.uid())
      or (q.customer_id is not null and (select app.owns_customer(q.customer_id)))
      or (select app.is_staff())
    )
  ));
create policy quote_items_admin_manage on app.quote_items for all to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy orders_select on app.orders for select to authenticated
  using ((select app.can_read_order(id)));
create policy orders_staff_update on app.orders for update to authenticated
  using ((select app.is_staff())) with check ((select app.is_staff()));
create policy order_items_select on app.order_items for select to authenticated
  using ((select app.can_read_order(order_id)));
create policy order_status_events_select on app.order_status_events for select to authenticated
  using ((select app.can_read_order(order_id)));
create policy order_status_events_staff_insert on app.order_status_events for insert to authenticated
  with check ((select app.is_staff()));
create policy production_jobs_select on app.production_jobs for select to authenticated
  using ((select app.can_read_order(order_id)));
create policy production_jobs_staff_manage on app.production_jobs for all to authenticated
  using ((select app.is_staff())) with check ((select app.is_staff()));
create policy deliveries_select on app.deliveries for select to authenticated
  using ((select app.can_read_order(order_id)));
create policy deliveries_staff_manage on app.deliveries for all to authenticated
  using ((select app.is_staff())) with check ((select app.is_staff()));

create policy media_assets_select on app.media_assets for select to authenticated
  using (access = 'public' or owner_user_id = (select auth.uid()) or (select app.is_staff()));
create policy media_assets_anon_public_select on app.media_assets for select to anon
  using (access = 'public');
create policy media_assets_staff_manage on app.media_assets for all to authenticated
  using ((select app.is_staff())) with check ((select app.is_staff()));
create policy payments_select on app.payments for select to authenticated
  using ((select app.can_read_order(order_id)));
create policy payments_staff_insert on app.payments for insert to authenticated
  with check ((select app.is_staff()));
create policy payments_admin_update on app.payments for update to authenticated
  using ((select app.is_admin())) with check ((select app.is_admin()));

create policy customer_events_staff_select on app.customer_events for select to authenticated
  using ((select app.is_staff()));
create policy model_versions_staff_select on app.model_versions for select to authenticated
  using ((select app.is_staff()));
create policy predictions_staff_select on app.predictions for select to authenticated
  using ((select app.is_staff()));
create policy optimization_runs_staff_select on app.optimization_runs for select to authenticated
  using ((select app.is_staff()));
create policy audit_logs_admin_select on app.audit_logs for select to authenticated
  using ((select app.is_admin()));

grant usage on schema app to anon, authenticated, service_role;
grant usage on type app.user_role, app.quote_status, app.order_status,
  app.payment_status, app.payment_method, app.asset_access, app.model_status
  to anon, authenticated, service_role;
revoke execute on all functions in schema app from public;
grant execute on function app.current_user_role() to authenticated, service_role;
grant execute on function app.is_admin() to authenticated, service_role;
grant execute on function app.is_staff() to authenticated, service_role;
grant execute on function app.owns_customer(uuid) to authenticated, service_role;
grant execute on function app.can_read_order(uuid) to authenticated, service_role;

grant select on app.products, app.product_images, app.materials, app.finishes, app.accessories,
  app.product_materials, app.product_finishes, app.product_accessories, app.media_assets to anon;
grant select on all tables in schema app to authenticated;
grant insert, update, delete on app.customers, app.delivery_locations, app.products,
  app.product_images, app.materials, app.finishes, app.accessories, app.product_materials,
  app.product_finishes, app.product_accessories, app.pricing_rules, app.quotes, app.quote_items,
  app.order_status_events, app.production_jobs, app.deliveries, app.media_assets,
  app.payments to authenticated;
grant update (full_name, phone) on app.profiles to authenticated;
grant update (status, version, updated_at) on app.orders to authenticated;
grant all on all tables in schema app to service_role;
grant all on all sequences in schema app to service_role;
grant execute on all functions in schema app to service_role;

commit;
