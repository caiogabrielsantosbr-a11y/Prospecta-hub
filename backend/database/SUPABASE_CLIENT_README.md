# Supabase Client Module

## Overview

This module provides a singleton Supabase client for the GMap Supabase Integration feature. It handles credential management, validation, and provides a foundation for cloud database operations.

## Features Implemented

### Task 1: Client Configuration ✅
- **Environment Variables**: Added SUPABASE_URL and SUPABASE_KEY to `.env` file
- **Singleton Pattern**: SupabaseClient implements singleton for instance reuse
- **Credential Validation**: Validates presence of credentials on initialization
- **Logging**: Logs warnings when credentials are missing with helpful messages
- **Graceful Degradation**: System continues to work even without Supabase credentials

### Task 2: Database Schema ✅
- **Table Creation**: Created `gmap_leads` table with all required columns
- **Indexes**: Added indexes on `task_id`, `conjunto_de_locais`, and `created_at`
- **Documentation**: SQL schema documented in `supabase_schema.sql`

## Usage

### Basic Usage

```python
from database.supabase_client import get_supabase_client

# Get the singleton client instance
client = get_supabase_client()

# Check if Supabase is available
if client.is_available():
    print("Supabase integration is enabled")
    url = client.get_url()
    key = client.get_key()
else:
    print("Supabase integration is disabled - credentials missing")
```

### Configuration

Add the following to your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
```

## Architecture

### Singleton Pattern

The `SupabaseClient` class implements the singleton pattern to ensure only one instance exists throughout the application lifecycle. This provides:

- **Resource efficiency**: Single connection pool
- **Consistent state**: All parts of the app use the same client
- **Easy testing**: Can reset singleton for test isolation

### Credential Validation

On initialization, the client:

1. Reads `SUPABASE_URL` and `SUPABASE_KEY` from environment variables
2. Strips whitespace from credentials
3. Validates that both are present and non-empty
4. If missing, logs a warning and disables integration
5. If present, marks client as available

### Logging Behavior

**When credentials are missing:**
```
WARNING - Supabase credentials missing: SUPABASE_URL, SUPABASE_KEY. 
Supabase integration is disabled. 
Please set these environment variables in .env file to enable cloud sync.
```

**When credentials are valid:**
```
INFO - Supabase client initialized successfully
```

## Testing

### Unit Tests

Run the unit tests:

```bash
cd backend
python -m pytest database/test_supabase_client.py -v
```

**Test Coverage:**
- ✅ Singleton pattern verification
- ✅ Initialization with valid credentials
- ✅ Initialization with missing credentials
- ✅ Initialization with missing URL only
- ✅ Initialization with missing KEY only
- ✅ Credential whitespace stripping
- ✅ get_supabase_client() function

### Manual Testing

Test the client manually:

```bash
cd backend
python -c "import sys; sys.path.insert(0, '.'); from database.supabase_client import get_supabase_client; client = get_supabase_client(); print('Available:', client.is_available())"
```

## Database Schema

### Table: gmap_leads

The `gmap_leads` table stores all leads extracted from Google Maps with location set tracking.

**Columns:**
- `id` (BIGSERIAL PRIMARY KEY): Auto-incrementing primary key
- `nome` (TEXT NOT NULL): Business name (required)
- `telefone` (TEXT): Phone number (may be "Sem Telefone")
- `website` (TEXT): Website URL (may be "Sem Website")
- `endereco` (TEXT): Full address
- `cidade` (TEXT): City from location set
- `url` (TEXT): Google Maps URL
- `conjunto_de_locais` (TEXT): Location set name (e.g., "Capitais do Brasil")
- `task_id` (TEXT): Extraction task ID for tracking
- `created_at` (TIMESTAMPTZ DEFAULT NOW()): Timestamp of record creation

**Indexes:**
- `idx_gmap_leads_task_id`: Index on `task_id` for efficient queries by task
- `idx_gmap_leads_conjunto`: Index on `conjunto_de_locais` for efficient queries by location set
- `idx_gmap_leads_created_at`: Index on `created_at` (DESC) for time-based queries

**Schema File:** `backend/database/supabase_schema.sql`

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

**Task 1 - Client Configuration:**
- **Requirement 4.1**: ✅ System reads credentials from environment variables (.env)
- **Requirement 4.2**: ✅ System validates presence of SUPABASE_URL and SUPABASE_KEY
- **Requirement 4.3**: ✅ System logs warning and disables integration when credentials are absent
- **Requirement 4.4**: ✅ System creates singleton instance for reuse

**Task 2 - Database Schema:**
- **Requirement 1.1**: ✅ Created `gmap_leads` table with all specified columns
- **Requirement 1.2**: ✅ Created index on `task_id` column
- **Requirement 1.3**: ✅ Created index on `conjunto_de_locais` column

## Next Steps

Future tasks will extend this client with:

- Connection to Supabase using the MCP client
- CRUD operations for gmap_leads table
- Retry logic with exponential backoff
- Batch insert operations
- Duplicate detection
- Query methods for retrieving leads

## API Reference

### SupabaseClient

#### Methods

**`__init__()`**
- Initializes the client with credentials from environment
- Validates credentials and logs warnings if missing
- Only initializes once (singleton pattern)

**`is_available() -> bool`**
- Returns True if credentials are valid and client is ready
- Returns False if credentials are missing

**`get_url() -> Optional[str]`**
- Returns the Supabase URL if available
- Returns None if credentials are missing

**`get_key() -> Optional[str]`**
- Returns the Supabase API key if available
- Returns None if credentials are missing

### Functions

**`get_supabase_client() -> SupabaseClient`**
- Returns the singleton SupabaseClient instance
- Creates instance on first call
- Returns same instance on subsequent calls

## File Structure

```
backend/database/
├── supabase_client.py              # Main client implementation
├── supabase_schema.sql             # SQL schema for gmap_leads table
├── test_supabase_client.py         # Unit tests
├── test_supabase_integration.py    # Integration test demo
└── SUPABASE_CLIENT_README.md       # This file
```
