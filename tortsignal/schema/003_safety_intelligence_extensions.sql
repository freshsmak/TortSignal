-- Safety Intelligence Graph Extensions
-- Enables multi-application use beyond TortSignal (plaintiff firms)
--
-- New markets enabled:
-- • Hospital procurement (device scorecards)
-- • Regulatory forecasting (pharma, investors, insurers)
-- • M&A diligence (PE, corporate dev)
-- • Competitive intelligence (pharma strategy)
-- • Defense-side litigation prep (manufacturers, counsel)
--
-- Run with: psql $DATABASE_URL < schema/003_safety_intelligence_extensions.sql

-- ============================================================================
-- PRODUCT-CENTRIC SIGNALS (not litigation-centric)
-- ============================================================================

-- Product signals: The core unit for Safety Intelligence Graph
-- Unlike tort_clusters (defendant+product+injury for litigation),
-- product_signals track safety patterns regardless of litigation viability
CREATE TABLE IF NOT EXISTS product_signals (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    injury_id UUID REFERENCES injuries(injury_id),
    signal_type TEXT NOT NULL, -- adverse_event, device_malfunction, quality_defect, therapeutic_failure

    -- Signal strength metrics
    first_detected_at TIMESTAMPTZ NOT NULL,
    last_updated_at TIMESTAMPTZ NOT NULL,
    report_count INT NOT NULL DEFAULT 0,
    death_count INT NOT NULL DEFAULT 0,
    serious_count INT NOT NULL DEFAULT 0,

    -- Trend analysis
    velocity_7d INT DEFAULT 0,
    velocity_30d INT DEFAULT 0,
    acceleration_ratio FLOAT DEFAULT 0,
    trend_direction TEXT, -- accelerating, stable, decelerating

    -- Geographic/demographic clustering
    geographic_concentration JSONB, -- {state: count, ...}
    age_distribution JSONB,         -- {age_range: count, ...}
    gender_distribution JSONB,

    -- Severity assessment
    severity_score FLOAT,
    severity_trend TEXT, -- worsening, stable, improving

    -- Subpopulation patterns (for clinical relevance)
    subpopulation_patterns JSONB, -- comorbidities, concomitant meds, etc.

    -- Device-specific fields
    lot_batch_clustering JSONB,    -- For contamination/quality detection
    failure_mode_taxonomy JSONB,   -- Device malfunction patterns

    -- Status
    status TEXT DEFAULT 'active',  -- active, resolved, monitoring

    UNIQUE(product_id, injury_id, signal_type)
);

CREATE INDEX ix_product_signals_product ON product_signals(product_id);
CREATE INDEX ix_product_signals_severity ON product_signals(severity_score DESC);
CREATE INDEX ix_product_signals_velocity ON product_signals(velocity_30d DESC);
CREATE INDEX ix_product_signals_updated ON product_signals(last_updated_at DESC);

-- Signal timeseries for trend visualization
CREATE TABLE IF NOT EXISTS product_signal_timeseries (
    signal_id UUID NOT NULL REFERENCES product_signals(signal_id) ON DELETE CASCADE,
    as_of_date DATE NOT NULL,
    report_count INT NOT NULL,
    death_count INT NOT NULL,
    serious_count INT NOT NULL,
    PRIMARY KEY (signal_id, as_of_date)
);

-- ============================================================================
-- REGULATORY ACTIONS (for forecasting & compliance)
-- ============================================================================

-- Track FDA/regulatory actions related to products
CREATE TABLE IF NOT EXISTS regulatory_actions (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),
    defendant_id UUID REFERENCES defendants(defendant_id),

    action_type TEXT NOT NULL, -- warning_letter, recall, label_change, black_box_warning,
                                -- safety_communication, market_withdrawal, 510k_clearance_revoked

    action_date DATE NOT NULL,
    announced_date DATE,

    severity TEXT, -- critical, major, minor
    scope TEXT,    -- class_i_recall, class_ii_recall, etc.

    title TEXT,
    description TEXT,
    affected_lots TEXT[],

    fda_url TEXT,
    doc_id UUID REFERENCES source_documents(doc_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_regulatory_actions_product ON regulatory_actions(product_id);
CREATE INDEX ix_regulatory_actions_defendant ON regulatory_actions(defendant_id);
CREATE INDEX ix_regulatory_actions_type ON regulatory_actions(action_type);
CREATE INDEX ix_regulatory_actions_date ON regulatory_actions(action_date DESC);

-- ============================================================================
-- LITERATURE EVIDENCE (PubMed, Semantic Scholar)
-- ============================================================================

-- Link products/injuries to published literature
CREATE TABLE IF NOT EXISTS literature_evidence (
    lit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- External IDs
    pubmed_id TEXT,
    doi TEXT,
    semantic_scholar_id TEXT,

    -- Bibliographic data
    title TEXT NOT NULL,
    authors TEXT[],
    journal TEXT,
    published_date DATE,

    -- Study characteristics
    study_type TEXT, -- rct, case_report, cohort, meta_analysis, mechanism, review
    evidence_level TEXT, -- 1a, 1b, 2a, 2b, 3, 4, 5 (Oxford CEBM)

    -- Content
    abstract TEXT,
    conclusions TEXT,

    -- Relevance scoring
    relevance_score FLOAT,
    cited_by_count INT,

    -- Links
    url TEXT,
    pdf_url TEXT,
    doc_id UUID REFERENCES source_documents(doc_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_literature_pubmed ON literature_evidence(pubmed_id);
CREATE INDEX ix_literature_doi ON literature_evidence(doi);
CREATE INDEX ix_literature_type ON literature_evidence(study_type);
CREATE INDEX ix_literature_published ON literature_evidence(published_date DESC);

-- Link literature to products/injuries/signals
CREATE TABLE IF NOT EXISTS literature_links (
    lit_id UUID NOT NULL REFERENCES literature_evidence(lit_id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(product_id),
    injury_id UUID REFERENCES injuries(injury_id),
    signal_id UUID REFERENCES product_signals(signal_id),

    relationship_type TEXT, -- supports, refutes, mechanism, risk_factor, case_report
    strength TEXT, -- strong, moderate, weak
    excerpt TEXT,

    PRIMARY KEY (lit_id, product_id, injury_id)
);

-- ============================================================================
-- HAZARD CLASSIFICATIONS (IARC, EPA, etc.)
-- ============================================================================

-- Authoritative hazard classifications for products
CREATE TABLE IF NOT EXISTS hazard_classifications (
    classification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id),

    authority TEXT NOT NULL, -- IARC, EPA, OSHA, FDA, WHO

    -- IARC carcinogenicity groups
    iarc_group TEXT, -- 1, 2A, 2B, 3, 4

    -- EPA toxicity
    epa_category TEXT,

    classification_text TEXT,
    classification_date DATE,
    monograph_url TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_hazard_class_product ON hazard_classifications(product_id);
CREATE INDEX ix_hazard_class_authority ON hazard_classifications(authority);
CREATE INDEX ix_hazard_class_iarc ON hazard_classifications(iarc_group);

-- ============================================================================
-- DEVICE SCORECARDS (for hospital procurement)
-- ============================================================================

-- Device reliability/safety scores for procurement decisions
CREATE TABLE IF NOT EXISTS device_scorecards (
    scorecard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    as_of_date DATE NOT NULL,

    -- Safety metrics
    malfunction_rate FLOAT,
    serious_injury_rate FLOAT,
    recall_count INT,

    -- Reliability metrics
    mean_time_to_failure INT, -- days
    revision_surgery_rate FLOAT,

    -- Comparison to alternatives
    peer_group TEXT,
    percentile_rank INT, -- 1-100, higher is better

    -- Overall score
    safety_score FLOAT, -- 0-100
    reliability_score FLOAT, -- 0-100
    overall_score FLOAT, -- 0-100

    -- Recommendations
    procurement_recommendation TEXT, -- preferred, acceptable, caution, avoid
    rationale TEXT,

    UNIQUE(product_id, as_of_date)
);

CREATE INDEX ix_device_scorecards_product ON device_scorecards(product_id);
CREATE INDEX ix_device_scorecards_overall ON device_scorecards(overall_score DESC);

-- ============================================================================
-- COMPETITIVE INTELLIGENCE (for pharma strategy)
-- ============================================================================

-- Track competitor product safety posture
CREATE TABLE IF NOT EXISTS competitive_safety_intel (
    intel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Market segment
    therapeutic_area TEXT, -- diabetes, oncology, cardio, etc.
    product_class TEXT,    -- SGLT2_inhibitors, GLP1_agonists, etc.

    -- Competitive landscape
    as_of_date DATE NOT NULL,
    market_leader_id UUID REFERENCES products(product_id),

    -- Safety comparison matrix (JSONB)
    -- {product_id: {sae_rate, death_rate, warning_count, ...}}
    safety_matrix JSONB,

    -- Market share vs safety correlation
    safety_displacement_opportunities JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_competitive_intel_area ON competitive_safety_intel(therapeutic_area);
CREATE INDEX ix_competitive_intel_date ON competitive_safety_intel(as_of_date DESC);

-- ============================================================================
-- REGULATORY RISK FORECASTS (for investors, PE, insurers)
-- ============================================================================

-- Predicted probability of regulatory action
CREATE TABLE IF NOT EXISTS regulatory_risk_forecasts (
    forecast_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    signal_id UUID REFERENCES product_signals(signal_id),

    forecast_date DATE NOT NULL,
    forecast_horizon_days INT NOT NULL, -- 90, 180, 365

    -- Predicted actions
    prob_warning_letter FLOAT,
    prob_safety_communication FLOAT,
    prob_label_change FLOAT,
    prob_black_box FLOAT,
    prob_recall FLOAT,
    prob_market_withdrawal FLOAT,

    -- Overall risk
    regulatory_risk_score FLOAT, -- 0-100
    risk_category TEXT, -- low, moderate, high, critical

    -- Supporting evidence
    precedent_cases JSONB, -- Similar historical patterns
    evidence_strength TEXT,
    confidence_interval JSONB,

    -- Model metadata
    model_version TEXT,
    features_used JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(product_id, forecast_date, forecast_horizon_days)
);

CREATE INDEX ix_reg_risk_product ON regulatory_risk_forecasts(product_id);
CREATE INDEX ix_reg_risk_score ON regulatory_risk_forecasts(regulatory_risk_score DESC);

-- ============================================================================
-- VIEWS: Multi-application dashboards
-- ============================================================================

-- TortSignal view (plaintiff firms)
CREATE OR REPLACE VIEW v_tortsignal_candidates AS
SELECT
    c.*,
    p.name as product_name,
    d.name as defendant_name,
    i.name as injury_name
FROM candidates c
LEFT JOIN products p ON c.product_id = p.product_id
LEFT JOIN defendants d ON c.defendant_id = d.defendant_id
LEFT JOIN injuries i ON c.injury_id = i.injury_id
WHERE c.status IN ('new', 'in_review', 'accepted');

-- Hospital procurement view (device safety scorecards)
CREATE OR REPLACE VIEW v_device_safety_scorecards AS
SELECT
    ds.*,
    p.name as product_name,
    d.name as manufacturer_name
FROM device_scorecards ds
JOIN products p ON ds.product_id = p.product_id
JOIN defendants d ON p.product_id = d.defendant_id -- assuming link exists
WHERE ds.as_of_date = (
    SELECT MAX(as_of_date) FROM device_scorecards WHERE product_id = ds.product_id
);

-- Regulatory risk view (investors, insurers)
CREATE OR REPLACE VIEW v_regulatory_risk_dashboard AS
SELECT
    rr.*,
    p.name as product_name,
    d.name as manufacturer_name,
    ps.velocity_30d,
    ps.severity_score
FROM regulatory_risk_forecasts rr
JOIN products p ON rr.product_id = p.product_id
JOIN defendants d ON p.product_id = d.defendant_id
LEFT JOIN product_signals ps ON rr.signal_id = ps.signal_id
WHERE rr.forecast_date = (
    SELECT MAX(forecast_date) FROM regulatory_risk_forecasts WHERE product_id = rr.product_id
);

COMMENT ON TABLE product_signals IS 'Product-centric safety signals, not litigation-centric. Core of Safety Intelligence Graph.';
COMMENT ON TABLE regulatory_actions IS 'FDA warnings, recalls, label changes. Enables regulatory forecasting.';
COMMENT ON TABLE literature_evidence IS 'PubMed, Semantic Scholar links. Evidence chains for causation.';
COMMENT ON TABLE hazard_classifications IS 'IARC, EPA, authoritative hazard classifications.';
COMMENT ON TABLE device_scorecards IS 'Hospital procurement safety scores.';
COMMENT ON TABLE competitive_safety_intel IS 'Pharma competitive intelligence on safety posture.';
COMMENT ON TABLE regulatory_risk_forecasts IS 'Predicted probability of regulatory actions.';
