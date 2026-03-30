# Email Dispatches Methods Summary

## Overview

This document summarizes the four email_dispatches methods added to `SupabaseClient` as part of task 1.5 of the Complete Supabase Migration spec.

## Implemented Methods

### 1. `insert_email_dispatch(dispatch_data: dict, max_retries: int = 3) -> bool`

**Purpose**: Insert a single email dispatch into Supabase with retry logic.

**Parameters**:
- `dispatch_data`: Dictionary containing dispatch fields
  - `recipient` (required): Email recipient address
  - `subject` (optional): Email subject line
  - `status` (optional): Dispatch status (default: 'pending')
  - `error_detail` (optional): Error details if dispatch failed
  - `task_id` (optional): Associated task ID
  - `sent_at` (optional): Timestamp when email was sent
- `max_retries`: Maximum retry attempts (default: 3)

**Returns**: `bool` - True if insert succeeded, False otherwise

**Error Handling**:
- Network errors: Retry with exponential backoff (2^attempt + jitter)
- Authentication errors (401/403): Disable integration immediately
- Rate limiting (429): Retry with exponential backoff + jitter
- Other HTTP errors: Log and return False

**Example**:
```python
dispatch_data = {
    'recipient': 'customer@example.com',
    'subject': 'Welcome to our service',
    'status': 'pending',
    'task_id': 'email-campaign-001'
}
success = await supabase_client.insert_email_dispatch(dispatch_data)
```

---

### 2. `insert_email_dispatches_batch(dispatches: list[dict], max_retries: int = 3) -> tuple[int, int]`

**Purpose**: Insert multiple email dispatches in a single batch operation with fallback to individual inserts.

**Parameters**:
- `dispatches`: List of dispatch dictionaries (same structure as `insert_email_dispatch`)
- `max_retries`: Maximum retry attempts for network errors (default: 3)

**Returns**: `tuple[int, int]` - (successful_inserts, failed_inserts)

**Behavior**:
1. Validates all dispatches (recipient field required)
2. Attempts batch insert for optimal performance
3. Falls back to individual inserts if batch fails
4. Returns statistics of successes and failures

**Error Handling**:
- Same as `insert_email_dispatch` for individual operations
- Batch failures trigger fallback to individual inserts

**Example**:
```python
dispatches = [
    {'recipient': 'user1@example.com', 'subject': 'Newsletter', 'task_id': 'campaign-1'},
    {'recipient': 'user2@example.com', 'subject': 'Newsletter', 'task_id': 'campaign-1'},
    {'recipient': 'user3@example.com', 'subject': 'Newsletter', 'task_id': 'campaign-1'}
]
success_count, failure_count = await supabase_client.insert_email_dispatches_batch(dispatches)
print(f"Inserted {success_count} dispatches, {failure_count} failed")
```

---

### 3. `get_email_dispatches_by_task(task_id: str, limit: int = 100, offset: int = 0) -> list[dict]`

**Purpose**: Query email dispatches by task_id with pagination support.

**Parameters**:
- `task_id` (required): Task ID to filter dispatches by
- `limit`: Maximum number of dispatches to return (default: 100)
- `offset`: Number of dispatches to skip for pagination (default: 0)

**Returns**: `list[dict]` - List of dispatch dictionaries with all fields, ordered by created_at DESC

**Error Handling**:
- Missing task_id: Log error and return empty list
- Invalid limit/offset: Use default values
- Network/auth errors: Log and return empty list

**Example**:
```python
# Get first 100 dispatches for a task
dispatches = await supabase_client.get_email_dispatches_by_task('campaign-001')

# Get next 100 dispatches (pagination)
more_dispatches = await supabase_client.get_email_dispatches_by_task('campaign-001', limit=100, offset=100)

# Get only 10 dispatches
recent = await supabase_client.get_email_dispatches_by_task('campaign-001', limit=10)
```

---

### 4. `update_email_dispatch_sent(id: int, sent_at: str) -> bool`

**Purpose**: Update the sent_at timestamp when an email is successfully sent.

**Parameters**:
- `id` (required): Dispatch ID to update
- `sent_at` (required): ISO 8601 timestamp string (e.g., "2024-01-15T10:30:00Z")

**Returns**: `bool` - True if update succeeded, False otherwise

**Behavior**:
- Updates both `sent_at` timestamp and `status` to 'sent'
- Uses PATCH request to update only specified fields

**Error Handling**:
- Missing id or sent_at: Log error and return False
- Network/auth errors: Log and return False

**Example**:
```python
from datetime import datetime

# Update dispatch when email is sent
dispatch_id = 12345
sent_timestamp = datetime.utcnow().isoformat() + 'Z'
success = await supabase_client.update_email_dispatch_sent(dispatch_id, sent_timestamp)

if success:
    print(f"Dispatch {dispatch_id} marked as sent")
```

---

## Schema Reference

The methods interact with the `email_dispatches` table in Supabase:

```sql
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
```

## Testing

Unit tests are provided in `test_email_dispatches_methods.py` covering:
- Single dispatch insert
- Batch dispatch insert
- Query by task_id with pagination
- Update sent_at timestamp
- Error handling (missing fields, unavailable client)
- Edge cases (empty batch, invalid parameters)

Run tests with:
```bash
pytest backend/database/test_email_dispatches_methods.py -v
```

## Requirements Validated

This implementation validates the following requirements from the spec:
- **Requirement 2.1**: Supabase_Client provides CRUD methods for email_dispatches
- **Requirement 2.2**: Implements retry logic with exponential backoff
- **Requirement 2.3**: Supports batch inserts with fallback
- **Requirement 2.5**: Maintains compatibility with existing interface patterns
- **Requirement 8.1**: Email_Dispatch_Worker can use Supabase_Client to save dispatches
- **Requirement 8.2**: Email_Dispatch_Worker can use Supabase_Client to save dispatches
- **Requirement 8.3**: Email_Dispatch_Router can query dispatches from Supabase
- **Requirement 8.5**: System can update sent_at when email is sent successfully

## Integration Notes

These methods follow the exact same patterns as existing methods in SupabaseClient:
- Singleton pattern for client instance
- Exponential backoff retry logic (2^attempt + random jitter)
- Authentication error detection and integration disabling
- Rate limiting handling (429 responses)
- Structured logging with contextual information
- Graceful degradation when Supabase is unavailable
- Batch insert with fallback to individual inserts
- Pagination support for queries

The implementation is ready for use by the Email Dispatch module worker and router.
