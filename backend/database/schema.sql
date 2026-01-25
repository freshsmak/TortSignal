-- EDE Database Schema
-- PostgreSQL 14+
-- Purpose: Store all signals, scores, and evidence for Epidemiological Discovery Engine

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SIGNALS TABLE
-- Core table storing all detected regulatory/epidemiological signals
-- ============================================================================

CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "HAZ-2026-001" or "EPI-2026-001"

    -- Core identifiers
    chemical VARCHAR(255) NOT NULL,
    cas_number VARCHAR(50),
    disease VARCHAR(255) NOT NULL,
    disease_code VARCHAR(50),  -- ICD-10, SEER code, MONDO, etc.

    -- Methodology
    methodology VARCHAR(50) NOT NULL CHECK (methodology IN ('HAZARD_FIRST', 'EPIDEMIOLOGY_FIRST')),

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'DETECTED' CHECK (status IN
        ('DETECTED', 'READY_TO_VALIDATE', 'IN_VALIDATION', 'VALIDATED', 'FIELD_TESTED', 'ARCHIVED')),

    -- Dates
    date_detected TIMESTAMP NOT NULL DEFAULT NOW(),
    date_updated TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Scores (cached for quick filtering)
    bradford_hill_score DECIMAL(5,2),  -- 0-100
    litigation_score DECIMAL(5,2),     -- 0-100+

    -- Market sizing (cached)
    market_size_min BIGINT,  -- dollars
    market_size_max BIGINT,
    addressable_plaintiffs_min INTEGER,
    addressable_plaintiffs_max INTEGER,

    -- Archive reason (if status = ARCHIVED)
    archive_reason TEXT,

    -- Metadata
    created_by VARCHAR(100) DEFAULT 'EDE_AUTOMATED',
    notes TEXT,

    -- Indexes
    CONSTRAINT check_scores CHECK (
        (bradford_hill_score IS NULL OR bradford_hill_score BETWEEN 0 AND 100) AND
        (litigation_score IS NULL OR litigation_score BETWEEN 0 AND 150)
    )
);

CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_scores ON signals(bradford_hill_score, litigation_score);
CREATE INDEX idx_signals_date_detected ON signals(date_detected DESC);
CREATE INDEX idx_signals_methodology ON signals(methodology);

-- ============================================================================
-- REGULATORY_ACTIONS TABLE
-- Tracks all regulatory signals (EU bans, IARC classifications, FDA actions)
-- ============================================================================

CREATE TABLE regulatory_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    -- Action details
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('BAN', 'RESTRICTION', 'WARNING', 'CLASSIFICATION')),
    agency VARCHAR(100) NOT NULL,  -- "EU ECHA", "IARC", "FDA", "NIOSH", "EPA"
    jurisdiction VARCHAR(100) NOT NULL,  -- "EU", "USA", "Israel", "Global"

    -- Dates
    action_date DATE NOT NULL,
    effective_date DATE,
    detected_date TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Details
    basis TEXT,  -- Reason for action (e.g., "Cannot rule out genotoxicity")
    document_url TEXT,
    document_number VARCHAR(100),  -- FDA Federal Register document number

    -- IARC specific
    iarc_group VARCHAR(10),  -- "Group 1", "Group 2A", "Group 2B"

    -- US status comparison
    us_status VARCHAR(50),  -- "ALLOWED", "RESTRICTED", "BANNED"
    regulatory_divergence BOOLEAN DEFAULT FALSE,  -- TRUE if EU banned but US allows

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_regulatory_signal ON regulatory_actions(signal_id);
CREATE INDEX idx_regulatory_date ON regulatory_actions(action_date DESC);
CREATE INDEX idx_regulatory_divergence ON regulatory_actions(regulatory_divergence) WHERE regulatory_divergence = TRUE;

-- ============================================================================
-- EXPOSURES TABLE
-- Maps chemicals to products and exposed populations
-- ============================================================================

CREATE TABLE exposures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    -- Product details
    product_name VARCHAR(255),
    manufacturer VARCHAR(255),
    product_category VARCHAR(100),  -- "Candy", "Cosmetics", "Pharmaceuticals", etc.

    -- Exposure details
    chemical_concentration VARCHAR(100),  -- "0.5-2% by weight", "10% solution"
    exposure_route VARCHAR(50),  -- "Oral", "Dermal", "Inhalation"

    -- Population
    exposed_population_estimate BIGINT,
    demographics JSONB,  -- {"age": "5-18", "gender": "All", "race": "All"}

    -- Intensity
    frequency VARCHAR(100),  -- "Daily", "3-7 times/week"
    duration VARCHAR(100),   -- "5-13 years (childhood)"
    exposure_intensity_score DECIMAL(3,1),  -- 0-10

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_exposures_signal ON exposures(signal_id);

-- ============================================================================
-- PREDICTIONS TABLE
-- Stores predicted outcomes based on mechanisms
-- ============================================================================

CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    -- Predicted disease
    predicted_disease VARCHAR(255) NOT NULL,
    predicted_disease_code VARCHAR(50),
    confidence_score DECIMAL(3,2),  -- 0-1 (e.g., 0.85 = 85% confident)

    -- Mechanisms
    mechanisms JSONB,  -- [{"pathway": "NLRP3 inflammasome", "evidence_count": 34}, ...]

    -- Evidence counts
    mechanistic_papers_count INTEGER,
    case_reports_count INTEGER,
    animal_studies_count INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_predictions_signal ON predictions(signal_id);

-- ============================================================================
-- EPIDEMIOLOGY_VALIDATIONS TABLE
-- Stores epidemiological validation data (SEER, CDC WONDER)
-- ============================================================================

CREATE TABLE epidemiology_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    -- Data source
    data_source VARCHAR(50) NOT NULL,  -- "SEER", "CDC_WONDER", "NHANES", "Literature"

    -- Trends
    disease VARCHAR(255) NOT NULL,
    demographics JSONB,  -- {"age": "15-40", "race": "Black", "gender": "Female"}

    baseline_rate DECIMAL(10,2),
    current_rate DECIMAL(10,2),
    percent_change DECIMAL(5,2),  -- e.g., 72.5 for 72.5% increase

    timeframe VARCHAR(50),  -- "1999-2015", "2009-2024"

    -- Temporal correlation
    exposure_period VARCHAR(50),  -- "1990-2010"
    disease_period VARCHAR(50),   -- "2010-2025"
    latency_years INTEGER,
    temporal_correlation_score DECIMAL(3,1),  -- 0-10

    validation_result VARCHAR(50) CHECK (validation_result IN ('STRONG', 'MODERATE', 'WEAK', 'NONE')),

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_epidemiology_signal ON epidemiology_validations(signal_id);

-- ============================================================================
-- BRADFORD_HILL_SCORES TABLE
-- Detailed breakdown of 9 Bradford Hill criteria
-- ============================================================================

CREATE TABLE bradford_hill_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    -- Individual criterion scores (0-10)
    strength_score DECIMAL(3,1) CHECK (strength_score BETWEEN 0 AND 10),
    consistency_score DECIMAL(3,1) CHECK (consistency_score BETWEEN 0 AND 10),
    specificity_score DECIMAL(3,1) CHECK (specificity_score BETWEEN 0 AND 10),
    temporality_score DECIMAL(3,1) CHECK (temporality_score BETWEEN 0 AND 10),
    biological_gradient_score DECIMAL(3,1) CHECK (biological_gradient_score BETWEEN 0 AND 10),
    plausibility_score DECIMAL(3,1) CHECK (plausibility_score BETWEEN 0 AND 10),
    coherence_score DECIMAL(3,1) CHECK (coherence_score BETWEEN 0 AND 10),
    experiment_score DECIMAL(3,1) CHECK (experiment_score BETWEEN 0 AND 10),
    analogy_score DECIMAL(3,1) CHECK (analogy_score BETWEEN 0 AND 10),

    -- Weighted scores
    strength_weighted DECIMAL(5,2),
    consistency_weighted DECIMAL(5,2),
    specificity_weighted DECIMAL(5,2),
    temporality_weighted DECIMAL(5,2),
    biological_gradient_weighted DECIMAL(5,2),
    plausibility_weighted DECIMAL(5,2),
    coherence_weighted DECIMAL(5,2),
    experiment_weighted DECIMAL(5,2),
    analogy_weighted DECIMAL(5,2),

    -- Composite
    composite_score DECIMAL(5,2) NOT NULL CHECK (composite_score BETWEEN 0 AND 100),
    interpretation VARCHAR(50) CHECK (interpretation IN
        ('VERY_STRONG', 'STRONG', 'MODERATE', 'WEAK', 'VERY_WEAK')),

    -- Evidence for each criterion (JSONB for flexibility)
    evidence JSONB,  -- {"strength": {"effect_size": 1.65, "source": "CDC"}, ...}

    scored_at TIMESTAMP DEFAULT NOW(),
    scored_by VARCHAR(100) DEFAULT 'EDE_AUTOMATED'
);

CREATE INDEX idx_bradford_hill_signal ON bradford_hill_scores(signal_id);
CREATE INDEX idx_bradford_hill_composite ON bradford_hill_scores(composite_score DESC);

-- ============================================================================
-- LITIGATION_SCORES TABLE
-- Detailed breakdown of 7 litigation viability factors
-- ============================================================================

CREATE TABLE litigation_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    -- Individual factor scores (0-10)
    causal_strength_score DECIMAL(3,1) CHECK (causal_strength_score BETWEEN 0 AND 10),
    population_size_score DECIMAL(3,1) CHECK (population_size_score BETWEEN 0 AND 10),
    defendant_solvency_score DECIMAL(3,1) CHECK (defendant_solvency_score BETWEEN 0 AND 10),
    preventability_score DECIMAL(3,1) CHECK (preventability_score BETWEEN 0 AND 10),
    social_justice_score DECIMAL(3,1) CHECK (social_justice_score BETWEEN 0 AND 10),
    severity_score DECIMAL(3,1) CHECK (severity_score BETWEEN 0 AND 10),
    novelty_score DECIMAL(3,1) CHECK (novelty_score BETWEEN 0 AND 10),

    -- Weighted scores
    causal_strength_weighted DECIMAL(5,2),
    population_size_weighted DECIMAL(5,2),
    defendant_solvency_weighted DECIMAL(5,2),
    preventability_weighted DECIMAL(5,2),
    social_justice_weighted DECIMAL(5,2),
    severity_weighted DECIMAL(5,2),
    novelty_weighted DECIMAL(5,2),

    -- Composite
    composite_score DECIMAL(5,2) NOT NULL CHECK (composite_score BETWEEN 0 AND 150),
    interpretation VARCHAR(50) CHECK (interpretation IN
        ('EXCEPTIONAL', 'STRONG', 'MARGINAL', 'WEAK')),

    -- Evidence
    evidence JSONB,  -- {"defendant_solvency": {"defendants": [...], "total_revenue": 111000000000}, ...}

    scored_at TIMESTAMP DEFAULT NOW(),
    scored_by VARCHAR(100) DEFAULT 'EDE_AUTOMATED'
);

CREATE INDEX idx_litigation_signal ON litigation_scores(signal_id);
CREATE INDEX idx_litigation_composite ON litigation_scores(composite_score DESC);

-- ============================================================================
-- DEFENDANTS TABLE
-- Tracks potential defendant companies
-- ============================================================================

CREATE TABLE defendants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    company_name VARCHAR(255) NOT NULL,
    ticker_symbol VARCHAR(10),

    -- Financials
    annual_revenue BIGINT,
    market_cap BIGINT,
    is_public BOOLEAN,

    -- Product relationship
    product_manufacturer BOOLEAN DEFAULT FALSE,
    chemical_manufacturer BOOLEAN DEFAULT FALSE,

    -- Insurance
    has_product_liability_insurance BOOLEAN,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_defendants_signal ON defendants(signal_id);

-- ============================================================================
-- PUBMED_PAPERS TABLE
-- Stores relevant PubMed papers for each signal
-- ============================================================================

CREATE TABLE pubmed_papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    pmid VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT,
    journal VARCHAR(255),
    publication_date DATE,

    -- Classification
    paper_type VARCHAR(50),  -- "MECHANISTIC", "EPIDEMIOLOGY", "CASE_REPORT", "REVIEW", "META_ANALYSIS"

    -- Relevance
    relevance_score DECIMAL(3,2),  -- 0-1

    -- Citations
    citation_count INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(signal_id, pmid)
);

CREATE INDEX idx_pubmed_signal ON pubmed_papers(signal_id);
CREATE INDEX idx_pubmed_type ON pubmed_papers(paper_type);

-- ============================================================================
-- LITIGATION_STATUS TABLE
-- Tracks pre-litigation confirmation (PACER searches, etc.)
-- ============================================================================

CREATE TABLE litigation_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    -- PACER search results
    pacer_cases_count INTEGER DEFAULT 0,
    pacer_last_searched TIMESTAMP,

    -- MDL status
    mdl_status VARCHAR(50) CHECK (mdl_status IN ('NONE', 'PETITION', 'FORMED')),
    mdl_number VARCHAR(20),

    -- Media coverage
    media_coverage_count INTEGER DEFAULT 0,
    media_last_searched TIMESTAMP,

    -- Academic publications
    recent_publications_count INTEGER DEFAULT 0,  -- Major studies last 2 years

    -- Overall novelty assessment
    is_pre_litigation BOOLEAN DEFAULT TRUE,

    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_litigation_signal ON litigation_status(signal_id);
CREATE INDEX idx_litigation_pre ON litigation_status(is_pre_litigation) WHERE is_pre_litigation = TRUE;

-- ============================================================================
-- USER_ACTIONS TABLE
-- Tracks user interactions with signals (watch list, validation, etc.)
-- ============================================================================

CREATE TABLE user_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    action_type VARCHAR(50) NOT NULL CHECK (action_type IN
        ('ADD_TO_WATCHLIST', 'REMOVE_FROM_WATCHLIST', 'START_VALIDATION',
         'ARCHIVE', 'DOWNLOAD_DOSSIER', 'ADD_NOTE')),

    action_data JSONB,  -- {"reason": "litigation_exists", "note": "Expert rejected"}

    performed_by VARCHAR(100) DEFAULT 'chase@auditlab.com',
    performed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_actions_signal ON user_actions(signal_id);
CREATE INDEX idx_user_actions_type ON user_actions(action_type);
CREATE INDEX idx_user_actions_date ON user_actions(performed_at DESC);

-- ============================================================================
-- DISCOVERY_DOSSIERS TABLE
-- Tracks generated PDF dossiers
-- ============================================================================

CREATE TABLE discovery_dossiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,

    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,

    generated_at TIMESTAMP DEFAULT NOW(),
    generated_by VARCHAR(100) DEFAULT 'EDE_AUTOMATED',

    version INTEGER DEFAULT 1
);

CREATE INDEX idx_dossiers_signal ON discovery_dossiers(signal_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update timestamp on signals table
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_updated = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_signals_modtime
    BEFORE UPDATE ON signals
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Portfolio view (validated discoveries only)
CREATE VIEW portfolio_discoveries AS
SELECT
    s.signal_id,
    s.chemical || ' → ' || s.disease AS name,
    s.status,
    s.bradford_hill_score,
    s.litigation_score,
    s.market_size_min,
    s.market_size_max,
    s.addressable_plaintiffs_min,
    s.addressable_plaintiffs_max,
    s.date_detected,
    bh.interpretation AS bradford_hill_interpretation,
    lit.interpretation AS litigation_interpretation,
    ls.is_pre_litigation
FROM signals s
LEFT JOIN bradford_hill_scores bh ON s.id = bh.signal_id
LEFT JOIN litigation_scores lit ON s.id = lit.signal_id
LEFT JOIN litigation_status ls ON s.id = ls.signal_id
WHERE s.status IN ('VALIDATED', 'FIELD_TESTED')
ORDER BY s.litigation_score DESC, s.bradford_hill_score DESC;

-- Signal pipeline view (for dashboard)
CREATE VIEW signal_pipeline AS
SELECT
    status,
    COUNT(*) as count,
    AVG(bradford_hill_score) as avg_bradford_hill,
    AVG(litigation_score) as avg_litigation
FROM signals
WHERE status != 'ARCHIVED'
GROUP BY status
ORDER BY
    CASE status
        WHEN 'DETECTED' THEN 1
        WHEN 'READY_TO_VALIDATE' THEN 2
        WHEN 'IN_VALIDATION' THEN 3
        WHEN 'VALIDATED' THEN 4
        WHEN 'FIELD_TESTED' THEN 5
    END;

-- ============================================================================
-- SEED DATA (Examples)
-- ============================================================================

-- Example signal: TiO2 → IBD (for testing)
INSERT INTO signals (signal_id, chemical, cas_number, disease, methodology, status, bradford_hill_score, litigation_score, market_size_min, market_size_max, addressable_plaintiffs_min, addressable_plaintiffs_max)
VALUES ('HAZ-2026-001', 'Titanium Dioxide', '13463-67-7', 'Inflammatory Bowel Disease', 'HAZARD_FIRST', 'VALIDATED', 94.0, 106.0, 15000000000, 40000000000, 15000, 25000);

-- Add regulatory action for TiO2
INSERT INTO regulatory_actions (signal_id, action_type, agency, jurisdiction, action_date, effective_date, basis, us_status, regulatory_divergence, iarc_group)
SELECT id, 'BAN', 'EU ECHA', 'EU', '2021-05-06', '2022-08-07', 'Cannot rule out genotoxicity after ingestion of TiO2 particles', 'ALLOWED', TRUE, NULL
FROM signals WHERE signal_id = 'HAZ-2026-001';

-- Add litigation status for TiO2
INSERT INTO litigation_status (signal_id, pacer_cases_count, mdl_status, media_coverage_count, is_pre_litigation)
SELECT id, 0, 'NONE', 0, TRUE
FROM signals WHERE signal_id = 'HAZ-2026-001';

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE signals IS 'Core table storing all detected regulatory and epidemiological signals';
COMMENT ON TABLE bradford_hill_scores IS 'Detailed Bradford Hill causal assessment (9 criteria, 0-100 composite)';
COMMENT ON TABLE litigation_scores IS 'Business viability assessment (7 factors, 0-100+ composite)';
COMMENT ON TABLE regulatory_actions IS 'Tracks EU bans, IARC classifications, FDA actions, etc.';
COMMENT ON TABLE exposures IS 'Maps chemicals to products and exposed populations';
COMMENT ON TABLE predictions IS 'Stores predicted outcomes based on mechanistic evidence';
COMMENT ON TABLE epidemiology_validations IS 'SEER/CDC WONDER validation data';
COMMENT ON TABLE defendants IS 'Potential defendant companies (manufacturers, suppliers)';
COMMENT ON TABLE pubmed_papers IS 'Relevant scientific literature for each signal';
COMMENT ON TABLE litigation_status IS 'Pre-litigation confirmation (PACER, MDL, media coverage)';
COMMENT ON TABLE user_actions IS 'Audit trail of user interactions (watch list, validation, archiving)';
COMMENT ON TABLE discovery_dossiers IS 'Generated PDF dossiers for each validated signal';
