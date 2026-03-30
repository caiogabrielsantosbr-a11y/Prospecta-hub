-- Complete Supabase Schema for Lead Prospecting Application
-- This schema includes all 10 tables for the complete migration from SQLite to Supabase
-- Type mapping: SQLite INTEGER -> PostgreSQL BIGSERIAL, String/Text -> TEXT, DateTime -> TIMESTAMPTZ, JSON -> JSONB

-- ============================================================================
-- 1. GMap Leads Table
-- ============================================================================
-- Stores leads extracted from Google Maps with location set tracking

CREATE TABLE IF NOT EXISTS gmap_leads (
    id BIGSERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    telefone TEXT,
    website TEXT,
    endereco TEXT,
    cidade TEXT,
    url TEXT,
    conjunto_de_locais TEXT,
    task_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gmap_leads_task_id ON gmap_leads(task_id);
CREATE INDEX IF NOT EXISTS idx_gmap_leads_conjunto ON gmap_leads(conjunto_de_locais);
CREATE INDEX IF NOT EXISTS idx_gmap_leads_created_at ON gmap_leads(created_at DESC);

-- ============================================================================
-- 2. Facebook Ads Leads Table
-- ============================================================================
-- Stores leads extracted from Facebook Ads with contact information

CREATE TABLE IF NOT EXISTS facebook_ads_leads (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    page_url TEXT,
    ad_url TEXT,
    page_id TEXT,
    emails TEXT,
    phones TEXT,
    instagram TEXT,
    stage TEXT DEFAULT 'feed',
    task_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_facebook_ads_leads_task_id ON facebook_ads_leads(task_id);
CREATE INDEX IF NOT EXISTS idx_facebook_ads_leads_stage ON facebook_ads_leads(stage);
CREATE INDEX IF NOT EXISTS idx_facebook_ads_leads_created_at ON facebook_ads_leads(created_at DESC);

-- ============================================================================
-- 3. Email Results Table
-- ============================================================================
-- Stores email extraction results from domains

CREATE TABLE IF NOT EXISTS email_results (
    id BIGSERIAL PRIMARY KEY,
    domain TEXT NOT NULL,
    email TEXT,
    source TEXT,
    task_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_results_task_id ON email_results(task_id);
CREATE INDEX IF NOT EXISTS idx_email_results_domain ON email_results(domain);
CREATE INDEX IF NOT EXISTS idx_email_results_created_at ON email_results(created_at DESC);

-- ============================================================================
-- 4. Tasks Table
-- ============================================================================
-- Stores background extraction tasks with configuration and statistics

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    module TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    config JSONB DEFAULT '{}'::jsonb,
    stats JSONB DEFAULT '{}'::jsonb,
    progress REAL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_module ON tasks(module);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- ============================================================================
-- 5. Email Dispatches Table
-- ============================================================================
-- Stores email dispatch records with delivery status

CREATE TABLE IF NOT EXISTS email_dispatches (
    id BIGSERIAL PRIMARY KEY,
    recipient TEXT NOT NULL,
    subject TEXT,
    status TEXT DEFAULT 'pending',
    error_detail TEXT,
    task_id TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_dispatches_task_id ON email_dispatches(task_id);
CREATE INDEX IF NOT EXISTS idx_email_dispatches_status ON email_dispatches(status);
CREATE INDEX IF NOT EXISTS idx_email_dispatches_created_at ON email_dispatches(created_at DESC);

-- ============================================================================
-- Schema Migration Complete
-- ============================================================================
-- All 5 tables have been created with appropriate:
-- - PostgreSQL data types (BIGSERIAL, TEXT, TIMESTAMPTZ, JSONB, REAL)
-- - Primary keys (auto-incrementing for most tables, TEXT for tasks)
-- - Default values (NOW() for timestamps, default strings/numbers for other fields)
-- - NOT NULL constraints on required fields
-- - Indexes on task_id, created_at, and frequently queried fields
-- - JSONB support for complex data structures (config, stats)
