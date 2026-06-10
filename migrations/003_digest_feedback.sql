-- Stores upvote/downvote feedback from digest email links
create table if not exists digest_feedback (
  id uuid default gen_random_uuid() primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  item_id text not null,
  vote text not null check (vote in ('up', 'down')),
  topic text default '',
  voted_at timestamptz default now(),
  unique (user_id, item_id)
);

-- RLS: only service role writes (via API), users can read their own
alter table digest_feedback enable row level security;

create policy "Users can read own feedback"
  on digest_feedback for select
  using (auth.uid() = user_id);
