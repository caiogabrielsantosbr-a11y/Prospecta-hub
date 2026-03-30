# Session Cache Utility

## Overview

The `sessionCache` utility provides a robust caching layer for location sets in the GMap extractor. It stores downloaded location JSON files in browser `sessionStorage` with automatic expiration and quota management.

## Features

- **1-hour TTL**: Cached entries automatically expire after 1 hour
- **Automatic cleanup**: Expired entries are removed on access
- **Quota management**: Handles storage quota exceeded errors by clearing oldest entries
- **Cache key format**: Uses `location-set:{id}` format for consistency
- **Timestamp tracking**: Each entry includes a timestamp for TTL validation
- **Statistics**: Provides cache statistics for monitoring

## Usage

### Import

```javascript
import { sessionCache } from '../utils/sessionCache'
```

### Basic Operations

#### Store Data

```javascript
const locationData = {
  locais: ['São Paulo, SP', 'Rio de Janeiro, RJ']
}

sessionCache.set('brasil-capitais', locationData)
```

#### Retrieve Data

```javascript
const data = sessionCache.get('brasil-capitais')

if (data) {
  // Use cached data
  console.log('Loaded from cache:', data)
} else {
  // Cache miss or expired - download fresh data
  const response = await fetch('/api/locations/...')
  const freshData = await response.json()
  sessionCache.set('brasil-capitais', freshData)
}
```

#### Clear Specific Entry

```javascript
sessionCache.clear('brasil-capitais')
```

#### Clear All Entries

```javascript
sessionCache.clearAll()
```

### Advanced Operations

#### Get Cache Statistics

```javascript
const stats = sessionCache.getStats()

console.log('Total entries:', stats.totalEntries)
console.log('Valid entries:', stats.validEntries)
console.log('Expired entries:', stats.expiredEntries)
console.log('Total size:', stats.totalSize, 'bytes')

// Detailed entry information
stats.entries.forEach(entry => {
  console.log(`${entry.key}: ${entry.age}ms old, ${entry.size} bytes`)
})
```

## Integration Example

### GMapPage Integration

```javascript
import { sessionCache } from '../utils/sessionCache'

const loadLocationSetData = async (setId) => {
  // Check cache first
  const cachedData = sessionCache.get(setId)
  
  if (cachedData) {
    console.log('Loading from cache')
    return cachedData
  }
  
  // Cache miss - download from API
  console.log('Downloading location set')
  const response = await fetch(`/api/locations/${setId}/full`)
  const data = await response.json()
  
  // Store in cache
  sessionCache.set(setId, data.locations)
  
  return data.locations
}
```

## Cache Behavior

### TTL (Time To Live)

- **Duration**: 1 hour (3600000 milliseconds)
- **Validation**: Checked on every `get()` call
- **Cleanup**: Expired entries are automatically removed

### Quota Management

When `sessionStorage` quota is exceeded:

1. The utility catches the `QuotaExceededError`
2. Calls `clearOldest()` to remove the oldest entry
3. Retries the storage operation
4. If retry fails, logs error and continues without caching

### Cache Key Format

All cache keys use the format: `location-set:{id}`

Examples:
- `location-set:brasil-capitais`
- `location-set:sudeste-brasil`
- `location-set:a1b2c3d4-e5f6-7890-abcd-ef1234567890`

## Testing

### Manual Testing

Open `sessionCache.manual-test.html` in a browser to run interactive tests:

```bash
# From the frontend directory
open src/utils/sessionCache.manual-test.html
```

The test page includes:
- Basic set/get operations
- TTL expiration validation
- Clear operations
- Cache statistics
- Multiple entries management
- Raw storage viewer

### Unit Tests

Run unit tests with vitest (when configured):

```bash
npm test -- sessionCache.test.js
```

## API Reference

### `sessionCache.get(key)`

Retrieve data from cache.

**Parameters:**
- `key` (string): Cache key without prefix

**Returns:**
- Cached data if found and not expired
- `null` if not found or expired

**Example:**
```javascript
const data = sessionCache.get('my-location-set')
```

### `sessionCache.set(key, data)`

Store data in cache with timestamp.

**Parameters:**
- `key` (string): Cache key without prefix
- `data` (any): Data to cache (must be JSON serializable)

**Example:**
```javascript
sessionCache.set('my-location-set', { locais: ['City 1', 'City 2'] })
```

### `sessionCache.clear(key)`

Remove a specific cache entry.

**Parameters:**
- `key` (string): Cache key without prefix

**Example:**
```javascript
sessionCache.clear('my-location-set')
```

### `sessionCache.clearAll()`

Remove all location-set cache entries.

**Example:**
```javascript
sessionCache.clearAll()
```

### `sessionCache.getStats()`

Get cache statistics.

**Returns:**
- Object with cache statistics:
  - `totalEntries`: Total number of cached entries
  - `validEntries`: Number of non-expired entries
  - `expiredEntries`: Number of expired entries
  - `totalSize`: Total size in bytes
  - `entries`: Array of entry details

**Example:**
```javascript
const stats = sessionCache.getStats()
console.log(`Cache has ${stats.validEntries} valid entries`)
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 7.1**: Cache key format `location-set:{name}` ✓
- **Requirement 7.2**: Timestamp stored with each entry ✓
- **Requirement 7.3**: 1-hour TTL check on retrieval ✓
- **Requirement 7.4**: Expired entries trigger fresh download ✓
- **Requirement 7.5**: Automatic cleanup on session end (browser behavior) ✓
- **Requirement 7.6**: Quota exceeded handling by clearing oldest entries ✓

## Browser Compatibility

The utility uses standard Web Storage API (`sessionStorage`) which is supported in:

- Chrome 4+
- Firefox 3.5+
- Safari 4+
- Edge (all versions)
- Opera 10.5+

## Performance Considerations

- **Cache hits**: Near-instant retrieval from sessionStorage
- **Cache misses**: Requires API call and network latency
- **Storage limits**: sessionStorage typically has 5-10MB limit per origin
- **Serialization**: JSON.stringify/parse overhead for large datasets

## Troubleshooting

### Cache not persisting

- Check browser console for errors
- Verify sessionStorage is not disabled
- Check if private/incognito mode is affecting storage

### Quota exceeded errors

- The utility automatically handles this by clearing oldest entries
- If persistent, consider reducing cache size or clearing manually

### Expired entries not clearing

- Entries are only cleared when accessed via `get()`
- Use `clearAll()` to manually clear all entries
- Use `getStats()` to identify expired entries

## Future Enhancements

Potential improvements for future versions:

- Compression for large datasets
- Configurable TTL per entry
- LRU (Least Recently Used) eviction policy
- Cache warming on page load
- Metrics and monitoring integration
