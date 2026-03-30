"""
Location utilities for identifying and extracting location set information.

This module provides functions to:
- Identify which location JSON file corresponds to a list of cities
- Extract the location set name from JSON files
- Provide fallback naming when metadata is missing
"""

import json
import os
from pathlib import Path
from typing import Optional


def find_location_file_by_cities(cities: list[str]) -> Optional[str]:
    """
    Find the location JSON file that contains the given cities.
    
    Args:
        cities: List of city strings (e.g., ["São Paulo, SP", "Rio de Janeiro, RJ"])
        
    Returns:
        Path to the matching JSON file, or None if no match found
        
    Example:
        >>> find_location_file_by_cities(["São Paulo, SP", "Rio de Janeiro, RJ"])
        'backend/locais/brasil-capitais.json'
    """
    if not cities:
        return None
    
    # Get the locais directory path
    locais_dir = Path(__file__).parent.parent.parent / "locais"
    
    if not locais_dir.exists():
        return None
    
    # Iterate through all JSON files in the locais directory
    for json_file in locais_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if this file contains the cities
            if "locais" in data:
                file_cities = set(data["locais"])
                input_cities = set(cities)
                
                # If all input cities are in this file, we found a match
                if input_cities.issubset(file_cities):
                    return str(json_file)
                    
        except (json.JSONDecodeError, IOError):
            # Skip files that can't be read or parsed
            continue
    
    return None


def extract_name_from_json(file_path: str) -> str:
    """
    Extract the location set name from a JSON file.
    
    Reads the "nome" field from the JSON file. If the field doesn't exist,
    falls back to using the filename without extension.
    
    Args:
        file_path: Path to the location JSON file
        
    Returns:
        The location set name (from "nome" field or filename)
        
    Example:
        >>> extract_name_from_json("backend/locais/brasil-capitais.json")
        'Capitais do Brasil'
        
        >>> extract_name_from_json("backend/locais/no-nome-field.json")
        'no-nome-field'
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Try to get the "nome" field
        if "nome" in data and data["nome"]:
            return data["nome"]
            
    except (json.JSONDecodeError, IOError, KeyError):
        # If we can't read the file or parse it, fall through to fallback
        pass
    
    # Fallback: use filename without extension
    return Path(file_path).stem


def load_location_set_name(cities: list[str]) -> str:
    """
    Load the location set name for a given list of cities.
    
    This is the main entry point that combines file identification and name extraction.
    
    Args:
        cities: List of city strings (e.g., ["São Paulo, SP", "Rio de Janeiro, RJ"])
        
    Returns:
        The location set name, or "Conjunto Desconhecido" if no file found
        
    Example:
        >>> load_location_set_name(["São Paulo, SP", "Rio de Janeiro, RJ"])
        'Capitais do Brasil'
    """
    # Find the location file
    file_path = find_location_file_by_cities(cities)
    
    if not file_path:
        return "Conjunto Desconhecido"
    
    # Extract and return the name
    return extract_name_from_json(file_path)
