# Requirements Document

## Introduction

The Location Sets Management System enables administrators to manage collections of geographic locations (cities, regions) for the GMap extractor through Supabase Storage, replacing the current local file-based approach that is incompatible with Vercel deployments. The system provides CRUD operations for location sets, seamless integration with the existing GMap extractor workflow, and efficient handling of large datasets (50k+ locations).

## Glossary

- **Location_Set**: A named collection of geographic locations with metadata (name, description, location count, creation date)
- **Location_JSON**: A JSON file containing an array of location strings stored in Supabase Storage
- **Admin_UI**: The administrative interface for managing location sets
- **GMap_Extractor**: The existing Google Maps data extraction interface
- **Supabase_Storage**: Cloud object storage service for storing Location_JSON files
- **Location_Sets_Table**: Database table storing metadata for each Location_Set
- **Session_Cache**: Browser sessionStorage used to cache downloaded Location_JSON files
- **Location_String**: A formatted geographic identifier (e.g., "São Paulo, SP")

## Requirements

### Requirement 1: Supabase Storage Infrastructure

**User Story:** As a system administrator, I want location files stored in Supabase Storage, so that the application works correctly when deployed to Vercel.

#### Acceptance Criteria

1. THE System SHALL create a Supabase Storage bucket named "location-files" with public read access
2. THE System SHALL create a location_sets table with columns: id (uuid), name (text), description (text), file_path (text), location_count (integer), created_at (timestamptz)
3. THE System SHALL store Location_JSON files in Supabase Storage with the path format "location-files/{uuid}.json"
4. WHEN a Location_Set is created, THE System SHALL generate a unique UUID for the file_path
5. THE System SHALL enforce a primary key constraint on the location_sets table id column
6. THE System SHALL enforce a unique constraint on the location_sets table name column

### Requirement 2: Location Set Creation

**User Story:** As an administrator, I want to create new location sets by pasting JSON arrays, so that I can add location collections for extraction campaigns.

#### Acceptance Criteria

1. WHEN an administrator provides a name, description, and JSON array, THE Admin_UI SHALL validate the JSON format
2. IF the JSON is invalid, THEN THE Admin_UI SHALL display a descriptive error message indicating the parsing failure
3. WHEN valid JSON is provided, THE System SHALL parse the array and count the number of Location_String entries
4. WHEN the JSON is valid, THE System SHALL upload the Location_JSON to Supabase Storage
5. WHEN the upload succeeds, THE System SHALL insert a record into the Location_Sets_Table with name, description, file_path, location_count, and created_at
6. IF a Location_Set with the same name already exists, THEN THE System SHALL return an error indicating the duplicate name
7. WHEN the Location_Set is created successfully, THE Admin_UI SHALL display a success confirmation with the location count

### Requirement 3: Location Set Listing

**User Story:** As an administrator, I want to view all existing location sets, so that I can see what collections are available.

#### Acceptance Criteria

1. THE Admin_UI SHALL display a list of all Location_Set records from the Location_Sets_Table
2. FOR EACH Location_Set, THE Admin_UI SHALL display the name, description, location_count, and created_at date
3. THE Admin_UI SHALL sort Location_Set records by created_at in descending order (newest first)
4. WHEN no Location_Set records exist, THE Admin_UI SHALL display a message indicating no location sets are available
5. THE Admin_UI SHALL format the created_at timestamp in a human-readable format (e.g., "Jan 15, 2025")

### Requirement 4: Location Set Preview

**User Story:** As an administrator, I want to preview the first 10 locations from a set, so that I can verify the content without downloading the entire file.

#### Acceptance Criteria

1. WHEN an administrator requests a preview, THE System SHALL download the Location_JSON from Supabase Storage
2. THE System SHALL parse the Location_JSON and extract the first 10 Location_String entries
3. THE Admin_UI SHALL display the first 10 Location_String entries in a readable list format
4. IF the Location_Set contains fewer than 10 locations, THE Admin_UI SHALL display all available locations
5. IF the download or parsing fails, THEN THE Admin_UI SHALL display an error message indicating the failure reason

### Requirement 5: Location Set Deletion

**User Story:** As an administrator, I want to delete location sets, so that I can remove outdated or incorrect collections.

#### Acceptance Criteria

1. WHEN an administrator requests deletion, THE Admin_UI SHALL display a confirmation dialog with the Location_Set name
2. WHEN the administrator confirms deletion, THE System SHALL delete the Location_JSON file from Supabase Storage
3. WHEN the file deletion succeeds, THE System SHALL delete the corresponding record from the Location_Sets_Table
4. IF the file deletion fails, THEN THE System SHALL log the error and still attempt to delete the database record
5. WHEN the deletion completes, THE Admin_UI SHALL refresh the location sets list
6. IF the Location_Set is currently in use by an active extraction, THEN THE System SHALL display a warning but allow deletion

### Requirement 6: GMap Extractor Integration

**User Story:** As a user, I want to select location sets from a dropdown in the GMap extractor, so that I can choose which locations to extract.

#### Acceptance Criteria

1. WHEN the GMap_Extractor loads, THE System SHALL fetch all Location_Set metadata from the Location_Sets_Table
2. THE GMap_Extractor SHALL display a dropdown populated with Location_Set names and location counts
3. WHEN a user selects a Location_Set, THE System SHALL check the Session_Cache for the Location_JSON
4. IF the Location_JSON is not in Session_Cache, THEN THE System SHALL download it from Supabase Storage
5. WHEN downloading, THE GMap_Extractor SHALL display a loading indicator with the text "Loading locations..."
6. WHEN the download completes, THE System SHALL store the Location_JSON in Session_Cache with a TTL of 1 hour
7. WHEN the Location_JSON is loaded, THE GMap_Extractor SHALL parse it and populate the city selection checkboxes
8. THE System SHALL maintain the existing Location_JSON format: {"nome": string, "descricao": string, "locais": string[]}

### Requirement 7: Session Cache Management

**User Story:** As a user, I want downloaded location sets cached during my session, so that I don't have to wait for repeated downloads.

#### Acceptance Criteria

1. WHEN a Location_JSON is downloaded, THE System SHALL store it in Session_Cache with a key format "location-set:{name}"
2. THE System SHALL store a timestamp with each cached Location_JSON entry
3. WHEN retrieving from Session_Cache, THE System SHALL check if the cached entry is older than 1 hour
4. IF the cached entry is older than 1 hour, THEN THE System SHALL delete it and download a fresh copy
5. WHEN the browser session ends, THE System SHALL automatically clear all cached Location_JSON entries
6. THE System SHALL handle Session_Cache quota exceeded errors by clearing the oldest entries

### Requirement 8: Performance Optimization

**User Story:** As a user, I want to see location counts before downloading, so that I can make informed decisions about large datasets.

#### Acceptance Criteria

1. THE GMap_Extractor dropdown SHALL display the location_count next to each Location_Set name
2. WHEN downloading a Location_JSON larger than 1MB, THE System SHALL display a progress indicator
3. THE System SHALL implement lazy loading by only downloading Location_JSON when a Location_Set is selected
4. THE System SHALL not preload any Location_JSON files on page load
5. WHEN a download takes longer than 2 seconds, THE System SHALL display the estimated file size

### Requirement 9: Migration from Local Files

**User Story:** As an administrator, I want to migrate existing local JSON files to Supabase Storage, so that I can preserve existing location sets.

#### Acceptance Criteria

1. THE System SHALL provide a migration endpoint at "/api/locations/migrate"
2. WHEN the migration endpoint is called, THE System SHALL scan the "backend/locais/" directory for JSON files
3. FOR EACH JSON file found, THE System SHALL read the file content and parse the JSON
4. FOR EACH valid JSON file, THE System SHALL upload the content to Supabase Storage
5. FOR EACH uploaded file, THE System SHALL create a corresponding Location_Sets_Table record
6. IF a Location_Set with the same name already exists, THEN THE System SHALL skip that file and log a warning
7. WHEN the migration completes, THE System SHALL return a summary with counts of successful and failed migrations
8. THE migration endpoint SHALL be idempotent and safe to run multiple times

### Requirement 10: Error Handling and Validation

**User Story:** As a user, I want clear error messages when operations fail, so that I can understand and resolve issues.

#### Acceptance Criteria

1. WHEN a Supabase Storage upload fails, THE System SHALL display an error message indicating "Failed to upload location file"
2. WHEN a Supabase Storage download fails, THE System SHALL display an error message indicating "Failed to load location set"
3. WHEN JSON parsing fails, THE System SHALL display an error message with the specific parsing error
4. WHEN a database operation fails, THE System SHALL log the error details and display a generic error message to the user
5. THE System SHALL validate that Location_JSON arrays contain only string values
6. IF a Location_JSON array contains non-string values, THEN THE System SHALL return an error indicating "Invalid location format"
7. THE System SHALL validate that Location_Set names are between 3 and 100 characters
8. THE System SHALL validate that Location_Set descriptions are no longer than 500 characters

### Requirement 11: Backward Compatibility

**User Story:** As a developer, I want the new system to maintain compatibility with existing location formats, so that no code refactoring is required in the GMap extractor.

#### Acceptance Criteria

1. THE System SHALL parse Location_JSON files with the structure: {"nome": string, "descricao": string, "locais": string[]}
2. THE System SHALL support Location_JSON files with only a "locais" array for backward compatibility
3. WHEN a Location_JSON lacks "nome" or "descricao" fields, THE System SHALL use the Location_Set metadata values
4. THE GMap_Extractor SHALL continue to work with the existing city selection and extraction logic without modifications
5. THE System SHALL maintain the existing Location_String format (e.g., "São Paulo, SP")

### Requirement 12: Location Set JSON Format Validation

**User Story:** As a system, I want to validate location JSON structure during creation, so that only properly formatted data is stored.

#### Acceptance Criteria

1. WHEN validating Location_JSON, THE System SHALL verify the presence of a "locais" array
2. THE System SHALL verify that the "locais" array contains at least 1 Location_String
3. IF the "locais" array is empty, THEN THE System SHALL return an error indicating "Location set must contain at least one location"
4. THE System SHALL verify that each Location_String in the "locais" array is a non-empty string
5. THE System SHALL trim whitespace from each Location_String before storage
6. THE System SHALL reject Location_JSON files larger than 10MB with an error message indicating the size limit

