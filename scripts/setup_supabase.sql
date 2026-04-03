-- Sunside AI Content Autopilot — Supabase Schema
-- Run once: Copy into Supabase SQL Editor and execute

-- 1. Content Inventory
CREATE TABLE IF NOT EXISTS content_inventory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT UNIQUE NOT NULL,
  page_type TEXT CHECK (page_type IN ('blog', 'landing', 'service', 'legal', 'other')),
  title TEXT, meta_description TEXT, h1 TEXT,
  h2s JSONB DEFAULT '[]',
  word_count INT DEFAULT 0,
  internal_links JSONB DEFAULT '[]',
  primary_keyword TEXT, secondary_keywords JSONB DEFAULT '[]',
  category TEXT, author TEXT,
  published_at TIMESTAMPTZ,
  last_crawled_at TIMESTAMPTZ DEFAULT now(),
  status TEXT DEFAULT 'active' CHECK (status IN ('active','deleted','error','redirect')),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Keywords
CREATE TABLE IF NOT EXISTS keywords (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keyword TEXT NOT NULL,
  source TEXT CHECK (source IN ('gsc','autocomplete','manual','clustering','competitor')),
  impressions INT DEFAULT 0, clicks INT DEFAULT 0, ctr FLOAT DEFAULT 0,
  avg_position FLOAT, ranking_page TEXT, cluster_name TEXT,
  search_intent TEXT CHECK (search_intent IN ('informational','transactional','navigational','unknown')),
  competitor_positions JSONB DEFAULT '{}',
  search_volume INT, period_start DATE, period_end DATE,
  created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(keyword, source, period_start)
);

-- 3. Content Opportunities
CREATE TABLE IF NOT EXISTS content_opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN','IN_PROGRESS','COMPLETED','SKIPPED','PLANNED')),
  type TEXT CHECK (type IN ('keyword_gap','low_hanging_fruit','ctr_optimization','content_refresh','topic_cluster','seo_heist')),
  priority TEXT CHECK (priority IN ('HIGH','MEDIUM','LOW')),
  priority_score FLOAT DEFAULT 0,
  target_keyword TEXT NOT NULL, related_keywords JSONB DEFAULT '[]',
  action TEXT CHECK (action IN ('NEW_POST','UPDATE_META','REFRESH_CONTENT','CREATE_CLUSTER','DEPLOY_HEIST')),
  suggested_title TEXT, research_query TEXT, existing_url TEXT,
  current_position FLOAT, impressions INT DEFAULT 0, current_ctr FLOAT, search_volume INT,
  suggested_meta_title TEXT, suggested_meta_description TEXT,
  existing_content_to_link JSONB DEFAULT '[]', competitor_info JSONB DEFAULT '{}',
  week_of DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT now(), completed_at TIMESTAMPTZ
);

-- 4. Findings
CREATE TABLE IF NOT EXISTS findings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'RESEARCHED' CHECK (status IN ('RESEARCHED','USED','SKIPPED')),
  opportunity_id UUID REFERENCES content_opportunities(id) ON DELETE SET NULL,
  title TEXT NOT NULL, source_name TEXT, source_url TEXT,
  source_type TEXT CHECK (source_type IN ('rss','scholar','alert','scrape','manual')),
  key_insight TEXT, stats TEXT, relevance_score FLOAT DEFAULT 0,
  blog_angle TEXT, target_keyword TEXT, related_keywords JSONB DEFAULT '[]',
  raw_content TEXT,
  created_at TIMESTAMPTZ DEFAULT now(), used_at TIMESTAMPTZ
);

-- 5. Blog Posts
CREATE TABLE IF NOT EXISTS blog_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'DRAFTED' CHECK (status IN ('DRAFTED','QA_PASSED','QA_FAILED','REVIEW_HOLD','SCHEDULED','PUBLISHED')),
  finding_id UUID REFERENCES findings(id) ON DELETE SET NULL,
  opportunity_id UUID REFERENCES content_opportunities(id) ON DELETE SET NULL,
  title TEXT, slug TEXT UNIQUE, meta_description TEXT, content TEXT,
  category TEXT, image_filename TEXT,
  target_keyword TEXT, related_keywords JSONB DEFAULT '[]',
  internal_links_used JSONB DEFAULT '[]', sources_used JSONB DEFAULT '[]',
  word_count INT DEFAULT 0,
  qa_score FLOAT, qa_feedback JSONB,
  scheduled_at TIMESTAMPTZ, published_at TIMESTAMPTZ,
  github_commit_sha TEXT, blog_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. LinkedIn Posts
CREATE TABLE IF NOT EXISTS linkedin_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING','POSTED','FAILED','SKIPPED')),
  blog_post_id UUID REFERENCES blog_posts(id) ON DELETE CASCADE,
  post_text TEXT, image_path TEXT, linkedin_post_urn TEXT,
  posted_at TIMESTAMPTZ,
  impressions INT DEFAULT 0, clicks INT DEFAULT 0,
  likes INT DEFAULT 0, comments INT DEFAULT 0, shares INT DEFAULT 0,
  last_stats_update TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 7. Pipeline Config
CREATE TABLE IF NOT EXISTS pipeline_config (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO pipeline_config (key, value, description) VALUES
  ('qa_threshold', '7.5', 'Min QA-Score für Auto-Publish'),
  ('auto_publish', 'true', 'Auto-Publish wenn QA bestanden'),
  ('delay_hours', '2', 'Review-Fenster (Stunden)'),
  ('paused', 'false', 'Pipeline pausieren'),
  ('hold_topics', '[]', 'Themen mit Pflicht-Review'),
  ('max_posts_per_week', '5', 'Max Posts/Woche'),
  ('max_posts_per_day', '1', 'Max Posts/Tag'),
  ('linkedin_auto_post', 'true', 'LinkedIn auto-posten'),
  ('notification_channel', '"slack"', 'slack oder email'),
  ('keyword_min_impressions', '10', 'Min Impressions für Relevanz'),
  ('content_refresh_age_days', '180', 'Tage bis Content-Refresh')
ON CONFLICT (key) DO NOTHING;

-- 8. Agent Runs (Monitoring)
CREATE TABLE IF NOT EXISTS agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name TEXT NOT NULL,
  status TEXT CHECK (status IN ('started','completed','failed')),
  started_at TIMESTAMPTZ DEFAULT now(), completed_at TIMESTAMPTZ,
  duration_seconds INT, items_processed INT DEFAULT 0, items_created INT DEFAULT 0,
  error_message TEXT, metadata JSONB DEFAULT '{}'
);

-- Monitoring View
CREATE OR REPLACE VIEW v_pipeline_status AS
SELECT 'findings' as tbl, status, COUNT(*) as n FROM findings GROUP BY status
UNION ALL SELECT 'blog_posts', status, COUNT(*) FROM blog_posts GROUP BY status
UNION ALL SELECT 'linkedin_posts', status, COUNT(*) FROM linkedin_posts GROUP BY status
UNION ALL SELECT 'opportunities', status, COUNT(*) FROM content_opportunities GROUP BY status
ORDER BY tbl, status;
