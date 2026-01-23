-- Migration: Add enrichment columns for FAERS discovery
-- Run with: psql $DATABASE_URL < schema/004_add_enrichment_columns.sql

-- Add defendant_type and metadata_json to defendants
ALTER TABLE defendants
ADD COLUMN IF NOT EXISTS defendant_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}';

-- Add product_type and metadata_json to products
ALTER TABLE products
ADD COLUMN IF NOT EXISTS product_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}';

-- Add metadata_json to injuries
ALTER TABLE injuries
ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}';

-- Add indexes for filtering
CREATE INDEX IF NOT EXISTS ix_defendants_type ON defendants(defendant_type);
CREATE INDEX IF NOT EXISTS ix_products_type ON products(product_type);
