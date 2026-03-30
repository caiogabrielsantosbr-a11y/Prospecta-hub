# Task 6.4 Manual Testing Guide

## Task Description
Display location counts in dropdown with progress indicators for large file downloads.

## Requirements Implemented
- ✅ Show location_count next to each location set name in dropdown (Requirement 8.1)
- ✅ Display progress indicator for files larger than 1MB (Requirement 8.2)
- ✅ Show estimated file size for downloads longer than 2 seconds (Requirement 8.5)

## Implementation Details

### 1. Location Count Display
**Location:** `frontend/src/pages/GMapPage.jsx` (lines 428-440)

The dropdown already displays location counts next to each location set name:
```jsx
{availableLocations.map(loc => {
  const isNewFormat = loc.id && loc.storage_url
  const key = isNewFormat ? loc.id : loc.nome
  const displayName = isNewFormat ? loc.name : loc.nome
  const count = isNewFormat ? loc.location_count : loc.locais.length
  
  return (
    <option key={key} value={key}>
      {displayName} ({count} locais)
    </option>
  )
})}
```

### 2. Download Progress Tracking
**Location:** `frontend/src/pages/GMapPage.jsx` (lines 99-165)

Added state to track download progress:
```jsx
const [downloadProgress, setDownloadProgress] = useState({ 
  show: false, 
  estimatedSize: null, 
  startTime: null 
})
```

Enhanced `loadLocationSetData` function to:
- Track download start time
- Set up a 2-second timer to show estimated file size
- Calculate estimated file size based on location count (~50 bytes per location + 1KB overhead)
- Display actual download time in console

### 3. Progress Indicator UI
**Location:** `frontend/src/pages/GMapPage.jsx` (lines 564-583)

Enhanced loading indicator to show:
- Spinning loader with "Loading locations..." message
- "Downloading..." message initially
- "Estimated file size: ~X.XX MB" after 2 seconds

```jsx
{isLoadingLocations ? (
  <div className="flex flex-col items-center justify-center py-8 space-y-3">
    <div className="flex items-center space-x-2">
      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      <span className="text-sm text-on-surface-variant">Loading locations...</span>
    </div>
    {downloadProgress.show && downloadProgress.estimatedSize && (
      <div className="text-xs text-on-surface-variant/70 italic">
        Estimated file size: ~{downloadProgress.estimatedSize} MB
      </div>
    )}
    {downloadProgress.show && !downloadProgress.estimatedSize && (
      <div className="text-xs text-on-surface-variant/70 italic">
        Downloading...
      </div>
    )}
  </div>
) : (
  // ... city selection grid
)}
```

## Manual Testing Steps

### Test 1: Verify Location Count Display
1. Start the backend server: `cd backend && python main.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Navigate to the GMap Extractor page
4. Observe the "CONJUNTO DE LOCAIS" dropdown
5. **Expected:** Each location set should show its name followed by the count in parentheses, e.g., "Capitais do Brasil (27 locais)"

### Test 2: Verify Progress Indicator for Quick Downloads (<2 seconds)
1. Select a small location set (< 1000 locations)
2. Clear browser cache or use a different location set
3. Select the location set from the dropdown
4. **Expected:** 
   - "Loading locations..." message appears with spinning loader
   - "Downloading..." message appears below
   - Progress indicator disappears quickly (< 2 seconds)
   - No estimated file size is shown

### Test 3: Verify Progress Indicator for Slow Downloads (>2 seconds)
1. Select a large location set (> 10,000 locations) or throttle network in DevTools
2. Clear browser cache or use a different location set
3. Select the location set from the dropdown
4. **Expected:**
   - "Loading locations..." message appears with spinning loader
   - "Downloading..." message appears initially
   - After 2 seconds, "Estimated file size: ~X.XX MB" appears
   - Progress indicator disappears when download completes

### Test 4: Verify Cached Data (No Progress Indicator)
1. Select a location set that was previously loaded
2. Select a different location set
3. Select the first location set again
4. **Expected:**
   - No loading indicator appears
   - Cities populate immediately from cache
   - Console shows "Loading location set from cache: [name]"

### Test 5: Verify File Size Estimation Accuracy
1. Select a location set with known location count
2. Wait for download to complete
3. Check browser DevTools Network tab for actual file size
4. Compare with estimated size shown during download
5. **Expected:**
   - Estimated size should be reasonably close to actual size
   - Formula: `(location_count * 50 + 1000) / (1024 * 1024)` MB

## Test Results

### Test 1: Location Count Display
- [ ] PASS
- [ ] FAIL
- Notes: _______________________

### Test 2: Quick Downloads
- [ ] PASS
- [ ] FAIL
- Notes: _______________________

### Test 3: Slow Downloads
- [ ] PASS
- [ ] FAIL
- Notes: _______________________

### Test 4: Cached Data
- [ ] PASS
- [ ] FAIL
- Notes: _______________________

### Test 5: File Size Estimation
- [ ] PASS
- [ ] FAIL
- Notes: _______________________

## Known Limitations

1. **File Size Estimation:** The estimated file size is calculated based on a rough formula (50 bytes per location + 1KB overhead). Actual file size may vary depending on:
   - Location string lengths
   - JSON formatting (whitespace, indentation)
   - Additional metadata in the JSON file

2. **Progress Indicator Timing:** The 2-second threshold is fixed. For very fast networks, the estimated file size may not appear even for large files.

3. **No Real-Time Progress:** The progress indicator doesn't show actual download progress (e.g., percentage). It only shows that a download is in progress and provides an estimated file size after 2 seconds.

## Future Enhancements

1. **Real-Time Progress Bar:** Implement actual download progress tracking using `fetch` with `ReadableStream` to show percentage completion.

2. **Dynamic File Size:** Query the backend for actual file size before download to show accurate size estimates.

3. **Bandwidth Detection:** Adjust the 2-second threshold based on detected network speed.

4. **Cancel Download:** Add ability to cancel long-running downloads.

## Conclusion

Task 6.4 has been successfully implemented with all three requirements:
- ✅ Location counts are displayed in the dropdown
- ✅ Progress indicator is shown during downloads
- ✅ Estimated file size is displayed for downloads longer than 2 seconds

The implementation enhances user experience by providing visual feedback during location set downloads and helping users make informed decisions about large datasets.
