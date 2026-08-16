-- Lantern v0.11 account profile migration
alter table public.users add column if not exists first_name text;
alter table public.users add column if not exists country text;
