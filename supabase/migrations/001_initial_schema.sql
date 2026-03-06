-- Persnally - Initial Database Schema
-- Run this in your Supabase SQL Editor

create extension if not exists "uuid-ossp";

-- ============================================================
-- USERS TABLE
-- ============================================================
create table public.users (
  id            uuid primary key references auth.users(id) on delete cascade,
  name          text not null default '',
  email         text unique not null,
  avatar_url    text default '',
  onboarded     boolean default false,
  created_at    timestamptz default now(),
  updated_at    timestamptz default now()
);

alter table public.users enable row level security;

create policy "Users can read own row"
  on public.users for select using (auth.uid() = id);

create policy "Users can update own row"
  on public.users for update using (auth.uid() = id);

create policy "Users can insert own row"
  on public.users for insert with check (auth.uid() = id);

-- Auto-create user row on auth signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, name, email, avatar_url)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name', ''),
    new.email,
    coalesce(new.raw_user_meta_data->>'avatar_url', '')
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================
-- CONNECTED ACCOUNTS
-- ============================================================
create table public.connected_accounts (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  provider        text not null default 'github',
  provider_uid    text not null,
  username        text not null,
  access_token    text not null,
  scopes          text[] default '{}',
  connected_at    timestamptz default now(),
  unique (user_id, provider)
);

alter table public.connected_accounts enable row level security;

create policy "Users can read own accounts"
  on public.connected_accounts for select using (auth.uid() = user_id);

create policy "Users can insert own accounts"
  on public.connected_accounts for insert with check (auth.uid() = user_id);

create policy "Users can update own accounts"
  on public.connected_accounts for update using (auth.uid() = user_id);

create policy "Users can delete own accounts"
  on public.connected_accounts for delete using (auth.uid() = user_id);

-- ============================================================
-- USER PREFERENCES
-- ============================================================
create table public.user_preferences (
  id                  uuid primary key default uuid_generate_v4(),
  user_id             uuid unique not null references public.users(id) on delete cascade,
  interests           text[] default '{}',
  experience_level    text default 'intermediate',
  location            text default '',
  timezone            text default 'UTC',
  content_style       text default 'technical_with_business_context',
  prioritize_local    boolean default true,
  opportunity_types   text[] default '{"hackathons","jobs","funding"}',
  send_frequency      text default 'daily',
  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);

alter table public.user_preferences enable row level security;

create policy "Users can manage own preferences"
  on public.user_preferences for all using (auth.uid() = user_id);

-- ============================================================
-- NEWSLETTERS
-- ============================================================
create table public.newsletters (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  subject         text not null,
  headline        text not null,
  items           jsonb not null default '[]',
  full_content    jsonb not null default '{}',
  html_snapshot   text,
  status          text default 'sent',
  quality_score   real,
  sent_at         timestamptz default now(),
  created_at      timestamptz default now()
);

alter table public.newsletters enable row level security;

create policy "Users can read own newsletters"
  on public.newsletters for select using (auth.uid() = user_id);

create index idx_newsletters_user_sent on public.newsletters (user_id, sent_at desc);

-- ============================================================
-- CONTENT HISTORY (dedup across sends)
-- ============================================================
create table public.content_history (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references public.users(id) on delete cascade,
  content_hash text not null,
  title       text,
  url         text,
  sent_date   timestamptz default now(),
  unique (user_id, content_hash)
);

alter table public.content_history enable row level security;

create policy "Users can read own content history"
  on public.content_history for select using (auth.uid() = user_id);

create index idx_content_history_user on public.content_history (user_id);

-- ============================================================
-- GENERATION JOBS (async tracking)
-- ============================================================
create table public.generation_jobs (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references public.users(id) on delete cascade,
  status      text default 'pending',
  started_at  timestamptz,
  completed_at timestamptz,
  newsletter_id uuid references public.newsletters(id),
  error       text,
  created_at  timestamptz default now()
);

alter table public.generation_jobs enable row level security;

create policy "Users can read own jobs"
  on public.generation_jobs for select using (auth.uid() = user_id);

-- ============================================================
-- SERVICE ROLE POLICIES (for backend API)
-- These allow the FastAPI backend (using service_role key) to
-- insert newsletters and manage generation jobs
-- ============================================================
create policy "Service can insert newsletters"
  on public.newsletters for insert with check (true);

create policy "Service can update newsletters"
  on public.newsletters for update using (true);

create policy "Service can manage jobs"
  on public.generation_jobs for all using (true);

create policy "Service can insert content history"
  on public.content_history for insert with check (true);
