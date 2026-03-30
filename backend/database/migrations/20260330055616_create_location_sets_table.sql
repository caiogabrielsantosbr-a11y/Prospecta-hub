-- Create location_sets table for managing geographic location collections
-- This table stores metadata for location sets used by the GMap extractor
-- Migration applied: 2026-03-30 05:56:16
-- Validates Requirements: 1.2, 1.5, 1.6

CREATE TABLE IF NOT EXISTS location_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    file_path TEXT NOT NULL,
    location_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on name column for fast lookups and unique constraint enforcement
CREATE INDEX IF NOT EXISTS idx_location_sets_name ON location_sets(name);

-- Create index on created_at for sorting by creation date (DESC)
CREATE INDEX IF NOT EXISTS idx_location_sets_created_at ON location_sets(created_at DESC);

-- Add comments to table and columns
COMMENT ON TABLE location_sets IS 'Stores metadata for geographic location collections used by GMap extractor';
COMMENT ON COLUMN location_sets.id IS 'UUID primary key, auto-generated';
COMMENT ON COLUMN location_sets.name IS 'Unique human-readable name (3-100 characters)';
COMMENT ON COLUMN location_sets.description IS 'Description of the location set (max 500 characters)';
COMMENT ON COLUMN location_sets.file_path IS 'Supabase Storage path format: {uuid}.json';
COMMENT ON COLUMN location_sets.location_count IS 'Number of locations in the set (for display purposes)';
COMMENT ON COLUMN location_sets.created_at IS 'Timestamp of creation (for sorting)';
