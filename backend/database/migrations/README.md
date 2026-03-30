# Database Migrations

This directory contains SQL migration files for the Supabase database.

## Migration Naming Convention

Migrations follow the pattern: `YYYYMMDDHHMMSS_description.sql`

Example: `20260330060032_create_app_settings_table.sql`

## Applied Migrations

| Version | Name | Description | Applied Date |
|---------|------|-------------|--------------|
| 20260330030614 | remove_instagram_and_trello_features | Removed Instagram and Trello related features | 2026-03-30 |
| 20260330031111 | restore_instagram_column_facebook_ads | Restored Instagram column to facebook_ads_leads | 2026-03-30 |
| 20260330050937 | add_email_column_to_gmap_leads | Added email column to gmap_leads table | 2026-03-30 |
| 20260330060032 | create_app_settings_table | Created app_settings table for runtime configuration | 2026-03-30 |

## How to Apply Migrations

Migrations are applied using the Supabase MCP tools:

```javascript
// Using the mcp_supabase_apply_migration tool
mcp_supabase_apply_migration({
  name: "migration_name",
  query: "SQL content here"
})
```

## app_settings Table

The `app_settings` table stores system-wide configuration as key-value pairs:

- **id**: Auto-incrementing primary key
- **key**: Unique configuration key (e.g., "backend_api_url")
- **value**: Configuration value stored as text (can be JSON string)
- **created_at**: Timestamp when the setting was created
- **updated_at**: Timestamp when the setting was last updated

### Indexes

- `idx_app_settings_key`: Unique index on the key column
- `idx_app_settings_updated_at`: Index on updated_at for tracking changes

### Usage Example

```sql
-- Insert or update a configuration setting
INSERT INTO app_settings (key, value, updated_at)
VALUES ('backend_api_url', 'https://abc123.ngrok.io', NOW())
ON CONFLICT (key) 
DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

-- Retrieve a configuration setting
SELECT value FROM app_settings WHERE key = 'backend_api_url';

-- Delete a configuration setting
DELETE FROM app_settings WHERE key = 'backend_api_url';
```
