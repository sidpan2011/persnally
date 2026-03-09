-- Persnally Career Intelligence - Phase 1 Migration
-- Adds skill analysis, career goals, opportunities, and tech trends

-- ============================================================
-- SKILL SNAPSHOTS - GitHub-derived skill analysis (daily)
-- ============================================================
create table public.skill_snapshots (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  snapshot_date   date not null default current_date,
  -- Core skill data
  skills          jsonb not null default '{}',
  -- Format: {"React": {"level": 0.85, "category": "framework", "repos": 5, "last_used": "2026-03-01"}}
  languages       jsonb not null default '{}',
  -- Format: {"TypeScript": {"percentage": 45, "repos": 12, "bytes": 234567}}
  frameworks      jsonb not null default '[]',
  -- Format: [{"name": "Next.js", "confidence": 0.9, "source": "package.json", "repos": ["repo1"]}]
  domains         jsonb not null default '{}',
  -- Format: {"frontend": 0.7, "ai_ml": 0.4, "devops": 0.2}
  -- Career assessment
  experience_level text default 'intermediate',
  career_stage    text default 'professional',
  specialization  text default '',
  -- AI-generated insights
  summary         text default '',
  strengths       jsonb default '[]',
  growth_areas    jsonb default '[]',
  -- Raw data for debugging
  raw_github_data jsonb default '{}',
  analysis_version int default 1,
  created_at      timestamptz default now(),
  unique (user_id, snapshot_date)
);

alter table public.skill_snapshots enable row level security;

create policy "Users can read own snapshots"
  on public.skill_snapshots for select using (auth.uid() = user_id);

create policy "Service can manage snapshots"
  on public.skill_snapshots for all using (true);

create index idx_skill_snapshots_user_date on public.skill_snapshots (user_id, snapshot_date desc);

-- ============================================================
-- SKILL GAPS - What to learn next
-- ============================================================
create table public.skill_gaps (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  skill_name      text not null,
  current_level   real default 0,
  market_demand   real default 0,
  gap_score       real default 0,
  reason          text,
  category        text default 'recommended',
  -- category: critical, recommended, emerging, complementary
  resources       jsonb default '[]',
  status          text default 'identified',
  -- status: identified, learning, achieved, dismissed
  snapshot_id     uuid references public.skill_snapshots(id) on delete cascade,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

alter table public.skill_gaps enable row level security;

create policy "Users can read own gaps"
  on public.skill_gaps for select using (auth.uid() = user_id);

create policy "Users can update own gaps"
  on public.skill_gaps for update using (auth.uid() = user_id);

create policy "Service can manage gaps"
  on public.skill_gaps for all using (true);

create index idx_skill_gaps_user on public.skill_gaps (user_id, status);

-- ============================================================
-- OPPORTUNITIES - Matched to user's actual stack
-- ============================================================
create table public.opportunities (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  title           text not null,
  description     text,
  category        text not null,
  -- category: hackathon, job, grant, conference, open_source
  source          text,
  source_url      text,
  match_score     real default 0,
  match_reasons   jsonb default '[]',
  deadline        timestamptz,
  status          text default 'new',
  -- status: new, saved, applied, dismissed
  metadata        jsonb default '{}',
  discovered_at   timestamptz default now(),
  updated_at      timestamptz default now()
);

alter table public.opportunities enable row level security;

create policy "Users can read own opportunities"
  on public.opportunities for select using (auth.uid() = user_id);

create policy "Users can update own opportunities"
  on public.opportunities for update using (auth.uid() = user_id);

create policy "Service can manage opportunities"
  on public.opportunities for all using (true);

create index idx_opportunities_user_status on public.opportunities (user_id, status, discovered_at desc);

-- ============================================================
-- CAREER GOALS - User-defined objectives
-- ============================================================
create table public.career_goals (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  goal_type       text not null,
  -- goal_type: learn_skill, get_job, build_project, grow_oss, switch_stack
  title           text not null,
  description     text,
  target_date     date,
  status          text default 'active',
  progress        real default 0,
  metadata        jsonb default '{}',
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

alter table public.career_goals enable row level security;

create policy "Users can manage own goals"
  on public.career_goals for all using (auth.uid() = user_id);

create index idx_career_goals_user on public.career_goals (user_id, status);

-- ============================================================
-- TECH TRENDS - Personalized radar
-- ============================================================
create table public.tech_trends (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  technology      text not null,
  category        text not null,
  -- category: adopt, trial, assess, hold
  momentum        text default 'stable',
  -- momentum: rising, stable, declining
  relevance_score real default 0,
  evidence        jsonb default '{}',
  snapshot_date   date not null default current_date,
  created_at      timestamptz default now()
);

alter table public.tech_trends enable row level security;

create policy "Users can read own trends"
  on public.tech_trends for select using (auth.uid() = user_id);

create policy "Service can manage trends"
  on public.tech_trends for all using (true);

create index idx_tech_trends_user_date on public.tech_trends (user_id, snapshot_date desc);

-- ============================================================
-- ADD CAREER FIELDS TO EXISTING PREFERENCES
-- ============================================================
alter table public.user_preferences
  add column if not exists career_goals text[] default '{}',
  add column if not exists target_roles text[] default '{}',
  add column if not exists remote_preference text default 'any';

-- ============================================================
-- ANALYSIS JOBS (reusable for skills/trends/opportunities)
-- ============================================================
create table public.analysis_jobs (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.users(id) on delete cascade,
  job_type        text not null,
  -- job_type: skill_analysis, trend_analysis, opportunity_scan, full_analysis
  status          text default 'pending',
  started_at      timestamptz,
  completed_at    timestamptz,
  result_summary  jsonb default '{}',
  error           text,
  created_at      timestamptz default now()
);

alter table public.analysis_jobs enable row level security;

create policy "Users can read own analysis jobs"
  on public.analysis_jobs for select using (auth.uid() = user_id);

create policy "Service can manage analysis jobs"
  on public.analysis_jobs for all using (true);

create index idx_analysis_jobs_user on public.analysis_jobs (user_id, job_type, created_at desc);
