-- Time series data for trend analysis
-- Stores aggregated counts by product and time period

CREATE TABLE IF NOT EXISTS signal_timeseries (
    id SERIAL PRIMARY KEY,

    -- Product identification
    product_name TEXT NOT NULL,
    source TEXT NOT NULL,  -- 'faers' | 'maude' | 'pubmed'

    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Aggregated metrics
    report_count INTEGER NOT NULL DEFAULT 0,
    serious_count INTEGER DEFAULT 0,

    -- Top reactions/problems for this period
    top_reactions JSONB,  -- [{reaction: str, count: int}, ...]

    -- Additional metadata
    metadata JSONB,  -- manufacturer, product_code, category, etc.

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ensure uniqueness per product/source/period
    UNIQUE(product_name, source, period_start)
);

-- Index for efficient trend queries
CREATE INDEX IF NOT EXISTS idx_timeseries_lookup
    ON signal_timeseries(product_name, source, period_start);

CREATE INDEX IF NOT EXISTS idx_timeseries_source
    ON signal_timeseries(source, period_start);

CREATE INDEX IF NOT EXISTS idx_timeseries_date_range
    ON signal_timeseries(period_start, period_end);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_timeseries_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER timeseries_update_timestamp
    BEFORE UPDATE ON signal_timeseries
    FOR EACH ROW
    EXECUTE FUNCTION update_timeseries_timestamp();

COMMENT ON TABLE signal_timeseries IS 'Historical time series data for trend analysis. Stores aggregated report counts by product and time period to enable slope, acceleration, and sustained trend detection.';
COMMENT ON COLUMN signal_timeseries.product_name IS 'Drug/device name as it appears in source data';
COMMENT ON COLUMN signal_timeseries.source IS 'Data source: faers (drugs), maude (devices), pubmed (literature)';
COMMENT ON COLUMN signal_timeseries.period_start IS 'Start date of aggregation period (typically quarter start)';
COMMENT ON COLUMN signal_timeseries.period_end IS 'End date of aggregation period (typically quarter end)';
COMMENT ON COLUMN signal_timeseries.report_count IS 'Total adverse event reports in this period';
COMMENT ON COLUMN signal_timeseries.serious_count IS 'Number of serious adverse events in this period';
COMMENT ON COLUMN signal_timeseries.top_reactions IS 'Top 10 reactions/problems with counts for this period';
COMMENT ON COLUMN signal_timeseries.metadata IS 'Additional contextual data: manufacturer, product_code, FDA class, etc.';
