# Implementation Plan: Location Sets Management

## Overview

This implementation plan converts the location sets management system from local file-based storage to Supabase Storage with a full CRUD interface. The implementation follows an incremental approach: database schema → backend API → frontend UI → integration with existing GMap extractor → migration tooling.

## Tasks

- [x] 1. Set up Supabase infrastructure and database schema
  - [x] 1.1 Create Supabase Storage bucket configuration
    - Create "location-files" bucket with public read access
    - Configure bucket policies for authenticated write access
    - _Requirements: 1.1, 1.3_
  
  - [x] 1.2 Create location_sets database table migration
    - Write SQL migration for location_sets table with columns: id (uuid, primary key), name (text, unique), description (text), file_path (text), location_count (integer), created_at (timestamptz)
    - Add constraints for primary key and unique name
    - _Requirements: 1.2, 1.5, 1.6_
  
  - [ ]* 1.3 Write unit tests for database schema
    - Test table creation and constraints
    - Test unique name constraint enforcement
    - _Requirements: 1.2, 1.5, 1.6_

- [x] 2. Implement backend location sets CRUD methods in supabase_client.py
  - [x] 2.1 Add create_location_set method
    - Generate UUID for file_path
    - Upload JSON to Supabase Storage at "location-files/{uuid}.json"
    - Insert metadata record into location_sets table
    - Handle duplicate name errors
    - _Requirements: 1.3, 1.4, 2.4, 2.5, 2.6_
  
  - [x] 2.2 Add get_all_location_sets method
    - Query all records from location_sets table
    - Sort by created_at descending
    - Return list of location set metadata
    - _Requirements: 3.1, 3.3_
  
  - [x] 2.3 Add get_location_set_preview method
    - Download JSON file from Supabase Storage
    - Parse and extract first 10 locations
    - Handle files with fewer than 10 locations
    - _Requirements: 4.1, 4.2, 4.4_
  
  - [x] 2.4 Add get_location_set_full method
    - Download complete JSON file from Supabase Storage
    - Parse and return full location array
    - _Requirements: 6.4, 6.7_
  
  - [x] 2.5 Add delete_location_set method
    - Delete JSON file from Supabase Storage
    - Delete metadata record from location_sets table
    - Handle file deletion failures gracefully
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [ ]* 2.6 Write unit tests for CRUD methods
    - Test create with valid and invalid data
    - Test duplicate name handling
    - Test get operations
    - Test delete operations
    - _Requirements: 2.1-2.7, 3.1-3.5, 4.1-4.5, 5.1-5.5_

- [x] 3. Implement backend API endpoints in locations router
  - [x] 3.1 Update GET /api/locations endpoint
    - Replace file system reading with get_all_location_sets call
    - Return location set metadata with location_count
    - Maintain backward compatibility with existing response format
    - _Requirements: 3.1, 3.2, 3.3, 11.1, 11.2_
  
  - [x] 3.2 Create POST /api/locations endpoint
    - Accept name, description, and JSON array in request body
    - Validate JSON format and structure
    - Validate name length (3-100 chars) and description length (max 500 chars)
    - Validate locais array has at least 1 location
    - Validate each location is a non-empty string
    - Trim whitespace from location strings
    - Reject files larger than 10MB
    - Call create_location_set method
    - Return success with location count or error message
    - _Requirements: 2.1-2.7, 10.3, 10.5, 10.7, 10.8, 12.1-12.6_
  
  - [x] 3.3 Create GET /api/locations/{location_set_id}/preview endpoint
    - Call get_location_set_preview method
    - Return first 10 locations
    - Handle download and parsing errors
    - _Requirements: 4.1-4.5, 10.2, 10.3_
  
  - [x] 3.4 Create GET /api/locations/{location_set_id}/full endpoint
    - Call get_location_set_full method
    - Return complete location array
    - Handle download and parsing errors
    - _Requirements: 6.4, 6.7, 10.2, 10.3_
  
  - [x] 3.5 Create DELETE /api/locations/{location_set_id} endpoint
    - Call delete_location_set method
    - Return success confirmation
    - Handle errors gracefully
    - _Requirements: 5.2-5.5, 10.1, 10.4_
  
  - [ ]* 3.6 Write integration tests for API endpoints
    - Test POST with valid and invalid JSON
    - Test GET endpoints with various scenarios
    - Test DELETE with existing and non-existing sets
    - Test error handling for all endpoints
    - _Requirements: 2.1-2.7, 3.1-3.5, 4.1-4.5, 5.1-5.5, 10.1-10.8_

- [x] 4. Checkpoint - Ensure backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement frontend Admin UI for location sets management
  - [x] 5.1 Create LocationSetsPage component
    - Create new page component at frontend/src/pages/LocationSetsPage.jsx
    - Add route in App.jsx for /admin/location-sets
    - Implement basic page layout with navigation
    - _Requirements: 2.1, 3.1, 4.1, 5.1_
  
  - [x] 5.2 Implement location sets list view
    - Fetch and display all location sets from GET /api/locations
    - Display name, description, location_count, and formatted created_at
    - Sort by created_at descending
    - Show "No location sets available" message when empty
    - Format dates in human-readable format (e.g., "Jan 15, 2025")
    - _Requirements: 3.1-3.5_
  
  - [x] 5.3 Implement create location set form
    - Add form with fields: name, description, JSON textarea
    - Validate JSON format on client side
    - Display validation errors for invalid JSON
    - Show success confirmation with location count after creation
    - Display error messages for duplicate names or other failures
    - _Requirements: 2.1-2.7, 10.2, 10.3, 10.7, 10.8_
  
  - [x] 5.4 Implement location set preview functionality
    - Add preview button for each location set
    - Fetch and display first 10 locations from preview endpoint
    - Show all locations if fewer than 10 exist
    - Display error messages on failure
    - _Requirements: 4.1-4.5, 10.2, 10.3_
  
  - [x] 5.5 Implement location set deletion
    - Add delete button for each location set
    - Show confirmation dialog with location set name
    - Call DELETE endpoint on confirmation
    - Refresh list after successful deletion
    - Display warning if set is in use (optional enhancement)
    - _Requirements: 5.1-5.6, 10.1_

- [ ] 6. Integrate location sets with GMap extractor
  - [x] 6.1 Update GMapPage to fetch location sets metadata
    - Replace local file loading with API call to GET /api/locations
    - Populate dropdown with location set names and counts
    - _Requirements: 6.1, 6.2_
  
  - [x] 6.2 Implement session cache for downloaded location sets
    - Create utility functions for sessionStorage management
    - Implement cache key format "location-set:{name}"
    - Store timestamp with each cached entry
    - Implement 1-hour TTL check
    - Handle quota exceeded errors by clearing oldest entries
    - _Requirements: 7.1-7.6_
  
  - [x] 6.3 Implement lazy loading of location JSON
    - Download location JSON only when user selects a set
    - Check session cache before downloading
    - Display "Loading locations..." indicator during download
    - Store downloaded JSON in session cache
    - Parse JSON and populate city selection checkboxes
    - _Requirements: 6.3-6.7, 8.3, 8.4_
  
  - [x] 6.4 Display location counts in dropdown
    - Show location_count next to each location set name in dropdown
    - Display progress indicator for files larger than 1MB
    - Show estimated file size for downloads longer than 2 seconds
    - _Requirements: 8.1, 8.2, 8.5_
  
  - [ ]* 6.5 Write integration tests for GMap extractor
    - Test location set selection and loading
    - Test session cache behavior
    - Test lazy loading functionality
    - _Requirements: 6.1-6.8, 7.1-7.6, 8.1-8.5_

- [ ] 7. Checkpoint - Test end-to-end flow
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement migration tooling
  - [ ] 8.1 Create migration endpoint POST /api/locations/migrate
    - Scan backend/locais/ directory for JSON files
    - Read and parse each JSON file
    - Upload valid files to Supabase Storage
    - Create location_sets table records
    - Skip files with duplicate names and log warnings
    - Return migration summary with success/failure counts
    - Make endpoint idempotent
    - _Requirements: 9.1-9.8_
  
  - [ ]* 8.2 Write tests for migration endpoint
    - Test migration with valid files
    - Test duplicate name handling
    - Test idempotency
    - Test error handling
    - _Requirements: 9.1-9.8_

- [ ] 9. Final validation and cleanup
  - [ ] 9.1 Verify backward compatibility
    - Test that existing GMap extractor logic works unchanged
    - Verify Location_JSON format compatibility
    - Test with both old format (locais only) and new format (nome, descricao, locais)
    - _Requirements: 11.1-11.5_
  
  - [ ] 9.2 Add comprehensive error handling
    - Verify all error messages are descriptive
    - Test Supabase Storage upload/download failures
    - Test JSON parsing errors
    - Test database operation failures
    - _Requirements: 10.1-10.8_
  
  - [ ]* 9.3 Write end-to-end integration tests
    - Test complete flow: create → list → preview → use in GMap → delete
    - Test session cache across multiple selections
    - Test error scenarios
    - _Requirements: All requirements_

- [ ] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Implementation uses Python/FastAPI for backend and React for frontend
- Supabase Storage and PostgreSQL are used for persistence
- Session cache uses browser sessionStorage API
- Migration endpoint allows one-time migration from local files
- Backward compatibility maintained with existing GMap extractor
