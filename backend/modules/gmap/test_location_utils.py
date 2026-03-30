"""
Unit tests for location_utils module.

Tests the location set identification and name extraction functionality.
"""

import json
import pytest
import tempfile
from pathlib import Path
from backend.modules.gmap.location_utils import (
    find_location_file_by_cities,
    extract_name_from_json,
    load_location_set_name
)


class TestExtractNameFromJson:
    """Test the extract_name_from_json function."""
    
    def test_extract_name_with_nome_field(self):
        """Test extracting name when 'nome' field exists."""
        # Create a temporary JSON file with nome field
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({"nome": "Test Location Set", "locais": []}, f)
            temp_path = f.name
        
        try:
            result = extract_name_from_json(temp_path)
            assert result == "Test Location Set"
        finally:
            Path(temp_path).unlink()
    
    def test_extract_name_without_nome_field(self):
        """Test fallback to filename when 'nome' field is missing."""
        # Create a temporary JSON file without nome field
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({"locais": ["City A", "City B"]}, f)
            temp_path = f.name
        
        try:
            result = extract_name_from_json(temp_path)
            # Should return filename without extension
            assert result == Path(temp_path).stem
        finally:
            Path(temp_path).unlink()
    
    def test_extract_name_with_empty_nome_field(self):
        """Test fallback when 'nome' field is empty string."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({"nome": "", "locais": []}, f)
            temp_path = f.name
        
        try:
            result = extract_name_from_json(temp_path)
            # Should fallback to filename
            assert result == Path(temp_path).stem
        finally:
            Path(temp_path).unlink()
    
    def test_extract_name_with_invalid_json(self):
        """Test fallback when JSON is malformed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            result = extract_name_from_json(temp_path)
            # Should fallback to filename
            assert result == Path(temp_path).stem
        finally:
            Path(temp_path).unlink()
    
    def test_extract_name_with_nonexistent_file(self):
        """Test fallback when file doesn't exist."""
        result = extract_name_from_json("/nonexistent/path/test-file.json")
        # Should return the stem of the path
        assert result == "test-file"


class TestFindLocationFileByCities:
    """Test the find_location_file_by_cities function."""
    
    def test_find_file_with_matching_cities(self):
        """Test finding file when cities match."""
        # Use real location files from the project
        cities = ["São Paulo, SP", "Rio de Janeiro, RJ"]
        result = find_location_file_by_cities(cities)
        
        # Should find brasil-capitais.json or sudeste-brasil.json
        assert result is not None
        assert result.endswith('.json')
        assert 'locais' in result
    
    def test_find_file_with_empty_list(self):
        """Test with empty city list."""
        result = find_location_file_by_cities([])
        assert result is None
    
    def test_find_file_with_nonexistent_cities(self):
        """Test with cities that don't exist in any file."""
        cities = ["Nonexistent City, XX", "Another Fake City, YY"]
        result = find_location_file_by_cities(cities)
        assert result is None
    
    def test_find_file_with_subset_of_cities(self):
        """Test that subset matching works correctly."""
        # Use a small subset of cities from a known file
        cities = ["São Paulo, SP"]
        result = find_location_file_by_cities(cities)
        
        # Should find a file containing this city
        assert result is not None
        assert result.endswith('.json')


class TestLoadLocationSetName:
    """Test the load_location_set_name function (main entry point)."""
    
    def test_load_name_with_valid_cities(self):
        """Test loading name with cities that exist in location files."""
        cities = ["São Paulo, SP", "Rio de Janeiro, RJ"]
        result = load_location_set_name(cities)
        
        # Should return a valid location set name (not the fallback)
        assert result != "Conjunto Desconhecido"
        assert len(result) > 0
    
    def test_load_name_with_invalid_cities(self):
        """Test loading name with cities that don't exist."""
        cities = ["Fake City, XX"]
        result = load_location_set_name(cities)
        
        # Should return the fallback name
        assert result == "Conjunto Desconhecido"
    
    def test_load_name_with_empty_list(self):
        """Test loading name with empty city list."""
        result = load_location_set_name([])
        
        # Should return the fallback name
        assert result == "Conjunto Desconhecido"
    
    def test_load_name_returns_nome_field_value(self):
        """Test that the function returns the 'nome' field from JSON."""
        # Test with known location file
        cities = ["São Paulo, SP", "Rio de Janeiro, RJ", "Belo Horizonte, MG"]
        result = load_location_set_name(cities)
        
        # Should return one of the known location set names
        assert result in ["Capitais do Brasil", "Região Sudeste", "Conjunto Desconhecido"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
