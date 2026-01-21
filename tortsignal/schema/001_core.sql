-- TortSignal Core Schema
-- Version: 1.0
-- Run with: psql $DATABASE_URL < schema/001_core.sql

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- CANONICAL ENTITIES (Normalized vocabulary)
-- ============================================================================

-- Defendants (companies, manufacturers)
CREATE TABLE IF NOT EXISTS defendants (
    defendant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    parent_defendant_id UUID REFERENCES defendants(defendant_id),
    ticker TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_defendants_name ON defendants(name);
CREATE INDEX IF NOT EXISTS ix_defendants_ticker ON defendants(ticker);

-- Products (drugs, devices, chemicals, consumer products)
CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    product_type TEXT, -- drug, device, chemical, consumer, other
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_products_name ON products(name);
CREATE INDEX IF NOT EXISTS ix_products_type ON products(product_type);

-- Injuries (harm types, diagnoses)
CREATE TABLE IF NOT EXISTS injuries (
    injury_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    icd10_codes TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_injuries_name ON injuries(name);

-- Entity aliases (for fuzzy matching and synonyms)
CREATE TABLE IF NOT EXISTS entity_aliases (
    alias_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL, -- defendant, product, injury
    entity_id UUID NOT NULL,
    alias_text TEXT NOT NULL,
    source TEXT, -- manual, import, model
    confidence FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_entity_aliases_type_text ON entity_aliases(entity_type, alias_text);
CREATE INDEX IF NOT EXISTS ix_entity_aliases_entity ON entity_aliases(entity_type, entity_id);

-- ============================================================================
-- TORT CLUSTERS (The tradable unit)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tort_clusters (
    cluster_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    defendant_id UUID REFERENCES defendants(defendant_id),
    product_id UUID REFERENCES products(product_id),
    injury_id UUID REFERENCES injuries(injury_id),
    category TEXT, -- pharma, device, chemical, consumer, gov_contractor, public_health, other
    status TEXT NOT NULL DEFAULT 'active', -- active, archived, promoted
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_tort_clusters_entities 
    ON tort_clusters(defendant_id, product_id, injury_id);
CREATE INDEX IF NOT EXISTS ix_tort_clusters_category ON tort_clusters(category);
CREATE INDEX IF NOT EXISTS ix_tort_clusters_status ON tort_clusters(status);

-- Cluster scores (time series)
CREATE TABLE IF NOT EXISTS cluster_scores (
    cluster_score_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID NOT NULL REFERENCES tort_clusters(cluster_id) ON DELETE CASCADE,
    as_of_date DATE NOT NULL,
    score_total FLOAT NOT NULL,
    confidence FLOAT,
    stage TEXT, -- quiet, awareness, investigate, high_conviction
    score_components JSONB NOT NULL DEFAULT '{}'::jsonb,
    top_event_ids UUID[],
    UNIQUE(cluster_id, as_of_date)
);

CREATE INDEX IF NOT EXISTS ix_cluster_scores_cluster_date 
    ON cluster_scores(cluster_id, as_of_date DESC);

-- ============================================================================
-- SOURCE DOCUMENTS (Evidence backbone)
-- ============================================================================

CREATE TABLE IF NOT EXISTS source_documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL, -- court_case, faers_report, maude_report, pubmed_article, sec_filing, etc.
    source_uid TEXT NOT NULL, -- upstream stable ID
    title TEXT,
    published_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    url TEXT,
    raw_blob_uri TEXT,
    raw_hash_sha256 TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_payload_json JSONB -- convenience for vibecoding; move to object store later
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_source_documents_type_uid 
    ON source_documents(source_type, source_uid);
CREATE INDEX IF NOT EXISTS ix_source_documents_retrieved 
    ON source_documents(retrieved_at DESC);
CREATE INDEX IF NOT EXISTS ix_source_documents_type_published 
    ON source_documents(source_type, published_at DESC);

-- ============================================================================
-- SIGNAL EVENTS (Typed events derived from documents)
-- ============================================================================

CREATE TABLE IF NOT EXISTS signal_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID REFERENCES tort_clusters(cluster_id) ON DELETE SET NULL,
    doc_id UUID REFERENCES source_documents(doc_id) ON DELETE SET NULL,
    event_type TEXT NOT NULL, -- filing_new, filing_spike, adverse_trend, paper_published, meta_analysis, sec_language_delta, etc.
    event_time TIMESTAMPTZ NOT NULL,
    weight FLOAT NOT NULL DEFAULT 1.0,
    features_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    excerpt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_signal_events_cluster_time 
    ON signal_events(cluster_id, event_time DESC);
CREATE INDEX IF NOT EXISTS ix_signal_events_type 
    ON signal_events(event_type);
CREATE INDEX IF NOT EXISTS ix_signal_events_doc 
    ON signal_events(doc_id);

-- ============================================================================
-- COURT CASES (Minimal representation for momentum tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS court_cases (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_uid TEXT NOT NULL, -- upstream case/docket ID
    filed_at DATE,
    court TEXT,
    jurisdiction TEXT, -- federal, state
    state TEXT,
    judge TEXT,
    defendant_text TEXT,
    product_text TEXT,
    injury_text TEXT,
    plaintiff_firm TEXT,
    doc_id UUID REFERENCES source_documents(doc_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_court_cases_source_uid 
    ON court_cases(source_uid);
CREATE INDEX IF NOT EXISTS ix_court_cases_filed 
    ON court_cases(filed_at DESC);
CREATE INDEX IF NOT EXISTS ix_court_cases_jurisdiction 
    ON court_cases(jurisdiction, state);

-- Map cases to clusters (many-to-many)
CREATE TABLE IF NOT EXISTS case_cluster_map (
    case_id UUID NOT NULL REFERENCES court_cases(case_id) ON DELETE CASCADE,
    cluster_id UUID NOT NULL REFERENCES tort_clusters(cluster_id) ON DELETE CASCADE,
    match_method TEXT, -- rules, ner, hybrid
    match_confidence FLOAT,
    PRIMARY KEY (case_id, cluster_id)
);

-- ============================================================================
-- CANDIDATES (Step 0 discovery - before full entity resolution)
-- ============================================================================

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_key TEXT NOT NULL, -- normalized defendant|product (pair-key)
    defendant_text TEXT NOT NULL,
    product_text TEXT NOT NULL,
    injury_text TEXT NOT NULL, -- often 'mixed' in Step 0
    defendant_id UUID REFERENCES defendants(defendant_id),
    product_id UUID REFERENCES products(product_id),
    injury_id UUID REFERENCES injuries(injury_id),
    category TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    metrics_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    score_total FLOAT NOT NULL DEFAULT 0,
    score_components JSONB NOT NULL DEFAULT '{}'::jsonb,
    why_now TEXT,
    status TEXT NOT NULL DEFAULT 'new' -- new, in_review, accepted, rejected, promoted_to_cluster
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_candidates_key 
    ON candidates(candidate_key);
CREATE INDEX IF NOT EXISTS ix_candidates_score 
    ON candidates(score_total DESC);
CREATE INDEX IF NOT EXISTS ix_candidates_status 
    ON candidates(status);
CREATE INDEX IF NOT EXISTS ix_candidates_last_seen 
    ON candidates(last_seen_at DESC);

-- Evidence links from source docs to candidates
CREATE TABLE IF NOT EXISTS candidate_evidence (
    candidate_evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    doc_id UUID NOT NULL REFERENCES source_documents(doc_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- filing_new, adverse_trend, etc.
    snippet TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_candidate_evidence_candidate_doc 
    ON candidate_evidence(candidate_id, doc_id);

-- Daily rollups for momentum tracking
CREATE TABLE IF NOT EXISTS candidate_rollups (
    candidate_id UUID NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    as_of_date DATE NOT NULL,
    velocity_7d INT NOT NULL DEFAULT 0,
    velocity_28d INT NOT NULL DEFAULT 0,
    accel_ratio FLOAT NOT NULL DEFAULT 0,
    breadth_states INT NOT NULL DEFAULT 0,
    breadth_firms INT NOT NULL DEFAULT 0,
    PRIMARY KEY (candidate_id, as_of_date)
);

-- ============================================================================
-- USERS AND ORGS (Placeholder for future multi-tenancy)
-- ============================================================================

CREATE TABLE IF NOT EXISTS orgs (
    org_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES orgs(org_id),
    email TEXT UNIQUE,
    role TEXT DEFAULT 'member', -- admin, member
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- WATCHLISTS AND ALERTS (Placeholder for future features)
-- ============================================================================

CREATE TABLE IF NOT EXISTS watchlists (
    watchlist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES orgs(org_id),
    name TEXT NOT NULL,
    filters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alert_subscriptions (
    sub_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES orgs(org_id),
    watchlist_id UUID REFERENCES watchlists(watchlist_id),
    thresholds_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    channels_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- INGEST TRACKING (For pipeline observability)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ingest_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running', -- running, success, failed
    records_fetched INT,
    records_processed INT,
    records_errored INT,
    error_message TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_ingest_runs_connector_started 
    ON ingest_runs(connector, started_at DESC);

-- ============================================================================
-- HELPER VIEWS (Optional, for convenience)
-- ============================================================================

-- Top candidates view
CREATE OR REPLACE VIEW v_top_candidates AS
SELECT 
    c.candidate_id,
    c.candidate_key,
    c.defendant_text,
    c.product_text,
    c.injury_text,
    c.category,
    c.score_total,
    c.status,
    c.first_seen_at,
    c.last_seen_at,
    c.why_now,
    c.metrics_json->>'count_7d' AS count_7d,
    c.metrics_json->>'breadth_states' AS breadth_states,
    c.metrics_json->>'breadth_firms' AS breadth_firms
FROM candidates c
WHERE c.status NOT IN ('rejected')
ORDER BY c.score_total DESC;

-- Recent signal events view
CREATE OR REPLACE VIEW v_recent_signals AS
SELECT 
    e.event_id,
    e.event_type,
    e.event_time,
    e.weight,
    e.excerpt,
    c.candidate_key,
    c.defendant_text,
    c.product_text,
    d.source_type,
    d.title AS doc_title,
    d.url AS doc_url
FROM signal_events e
LEFT JOIN candidates c ON c.candidate_id = e.cluster_id::uuid -- Note: cluster_id may reference candidates in Step 0
LEFT JOIN source_documents d ON d.doc_id = e.doc_id
ORDER BY e.event_time DESC;

-- ============================================================================
-- GRANTS (Adjust as needed for your setup)
-- ============================================================================

-- Example: GRANT ALL ON ALL TABLES IN SCHEMA public TO tortsignal_app;
-- Example: GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tortsignal_app;
