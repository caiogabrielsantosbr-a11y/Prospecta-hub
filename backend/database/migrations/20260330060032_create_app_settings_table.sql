-- Create app_settings table for runtime configuration
-- This table stores system-wide configuration key-value pairs
-- Migration applied: 2026-03-30 06:00:32

CREATE TABLE IF NOT EXISTS app_settings (
    id BIGSERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create unique index on key column for fast lookups and constraint enforcement
CREATE UNIQUE INDEX IF NOT EXISTS idx_app_settings_key ON app_settings(key);

-- Create index on updated_at for tracking configuration changes
CREATE INDEX IF NOT EXISTS idx_app_settings_updated_at ON app_settings(updated_at DESC);

-- Add comment to table
COMMENT ON TABLE app_settings IS 'Stores system-wide configuration settings as key-value pairs';
COMMENT ON COLUMN app_settings.key IS 'Unique configuration key (e.g., backend_api_url)';
COMMENT ON COLUMN app_settings.value IS 'Configuration value stored as text (can be JSON string)';
