"""
Utilities for integrating analyzers with the database.
"""

import os
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from .utils import read_markdown_file, save_analysis_results, parse_parameter_value, should_parse_field_as_parameter, clean_json_response
from db.paper_dao import PaperDAO
from db.model_dao import ModelDAO
from db.extraction_dao import ExtractionDAO

def get_or_create_model(model_name, provider, context_size=None, version=None):
    """
    Get a model from the database or create it if it doesn't exist
    
    Args:
        model_name: Name of the model
        provider: Provider of the model
        context_size: Context size in tokens
        version: Version of the model
        
    Returns:
        The model ID
    """
    # Try to get existing model
    model = ModelDAO.get_model_by_name_provider(model_name, provider, version)
    
    if model:
        return model['id']
    
    # Create new model
    return ModelDAO.insert_model(model_name, provider, context_size, version)

def store_paper_from_md_file(md_file_path, arxiv_id=None, title=None, store_content=True, published_date=None):
    """
    Store a paper in the database from a markdown file
    
    Args:
        md_file_path: Path to the markdown file
        arxiv_id: ArXiv ID of the paper (optional)
        title: Title of the paper (optional)
        store_content: Whether to store the content in the database
        published_date: Publication date of the paper (datetime object, optional)
        
    Returns:
        The paper ID
    """
    # Make sure file exists
    if not os.path.exists(md_file_path):
        #print(f"Error: Markdown file not found at {md_file_path}")
        return None
    
    # Extract info from the path if not provided
    if not arxiv_id:
        # Try to extract from filename
        filename = Path(md_file_path).stem
        arxiv_id = filename.replace('_', '/')
    
    if not title:
        # Use the filename as title if not provided
        title = Path(md_file_path).stem
    
    # Read content if requested
    md_content = None
    if store_content:
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
        except Exception as e:
            #print(f"Warning: Could not read markdown file: {e}")
            pass
    
    # Store in database
    return PaperDAO.insert_paper(arxiv_id, title, md_file_path, md_content, None, published_date)

def extract_json_from_text(text):
    """
    Extract JSON from text that may contain additional content.
    Tries multiple strategies to find and parse valid JSON.
    
    Args:
        text: String that may contain JSON
        
    Returns:
        Parsed JSON data or None if no valid JSON found
    """
    #print(f"DEBUG: extract_json_from_text - Input length: {len(text)} chars")
    #print(f"DEBUG: extract_json_from_text - First 50 chars: {repr(text[:50])}")
    
    def _extract_boundaries(text, start_pos, open_char, close_char):
        """Helper function to extract JSON boundaries by counting brackets/braces."""
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start_pos, len(text)):
            char = text[i]
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if not in_string:
                if char == open_char:
                    depth += 1
                elif char == close_char:
                    depth -= 1
                    if depth == 0:
                        return text[start_pos:i+1]
        return None
    
    # Strategy 1: Try to find JSON object boundaries
    def find_json_boundaries(s):
        """Find the boundaries of a JSON object or array in a string."""
        #print(f"DEBUG: find_json_boundaries - Looking for JSON boundaries")
        # Look for opening brace/bracket
        start_obj = s.find('{')
        start_arr = s.find('[')
        
        #print(f"DEBUG: find_json_boundaries - start_obj: {start_obj}, start_arr: {start_arr}")
        
        # Determine which comes first (or if either exists)
        if start_obj != -1 and start_arr != -1:
            # Both found - choose whichever comes first
            if start_obj < start_arr:
                #print(f"DEBUG: find_json_boundaries - Using object boundaries starting at {start_obj}")
                return _extract_boundaries(s, start_obj, '{', '}')
            else:
                #print(f"DEBUG: find_json_boundaries - Using array boundaries starting at {start_arr}")
                return _extract_boundaries(s, start_arr, '[', ']')
        elif start_obj != -1:
            #print(f"DEBUG: find_json_boundaries - Using object boundaries starting at {start_obj}")
            return _extract_boundaries(s, start_obj, '{', '}')
        elif start_arr != -1:
            #print(f"DEBUG: find_json_boundaries - Using array boundaries starting at {start_arr}")
            return _extract_boundaries(s, start_arr, '[', ']')
        else:
            #print(f"DEBUG: find_json_boundaries - No JSON boundaries found")
            return None

    # Strategy 2: Enhanced array boundary detection for multiple objects
    def find_array_boundaries(s):
        """Find boundaries for JSON array containing multiple objects."""
        #print(f"DEBUG: find_array_boundaries - Looking for array boundaries")
        # Look for pattern: object, object, ... (comma-separated objects)
        first_obj = s.find('{')
        if first_obj == -1:
            #print(f"DEBUG: find_array_boundaries - No object start found")
            return None
        
        #print(f"DEBUG: find_array_boundaries - First object at position {first_obj}")
        
        # Find all complete objects
        objects = []
        current_pos = first_obj
        
        while current_pos < len(s):
            obj_start = s.find('{', current_pos)
            if obj_start == -1:
                break
                
            # Find end of this object using bracket counting
            depth = 0
            in_string = False
            escape_next = False
            obj_end = -1
            
            for i in range(obj_start, len(s)):
                char = s[i]
                
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            obj_end = i + 1
                            break
            
            if obj_end > 0:
                # Extract this object
                obj_text = s[obj_start:obj_end]
                try:
                    # Validate it's proper JSON
                    json.loads(obj_text)
                    objects.append(obj_text)
                    #print(f"DEBUG: find_array_boundaries - Found valid object {len(objects)}")
                except:
                    # If not valid JSON, stop processing
                    #print(f"DEBUG: find_array_boundaries - Invalid JSON object, stopping")
                    break
                
                # Look for the next object after comma
                remaining = s[obj_end:].strip()
                if remaining.startswith(','):
                    # Find the position after the comma
                    comma_pos = obj_end + s[obj_end:].find(',') + 1
                    current_pos = comma_pos
                else:
                    # No more objects
                    break
            else:
                break
        
        if len(objects) > 1:
            # Wrap multiple objects in array
            objects_text = ', '.join(objects)
            result = f"[{objects_text}]"
            #print(f"DEBUG: find_array_boundaries - Created array with {len(objects)} objects")
            return result
        elif len(objects) == 1:
            # Single object
            #print(f"DEBUG: find_array_boundaries - Single object found")
            return objects[0]
        
        #print(f"DEBUG: find_array_boundaries - No valid objects found")
        return None
    
    # Strategy 2: Try regex patterns for JSON
    def extract_with_regex(s):
        """Try to extract JSON using regex patterns."""
        # Pattern for JSON object
        obj_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        # Pattern for JSON array
        arr_pattern = r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
        
        # Try object pattern first
        obj_match = re.search(obj_pattern, s, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group())
            except:
                pass
        
        # Try array pattern
        arr_match = re.search(arr_pattern, s, re.DOTALL)
        if arr_match:
            try:
                return json.loads(arr_match.group())
            except:
                pass
        
        return None
    
    strategies = [
        # Strategy 1: Try parsing the cleaned text directly
        lambda: json.loads(text),
        
        # Strategy 2: Find JSON boundaries and parse
        lambda: json.loads(find_json_boundaries(text)) if find_json_boundaries(text) else None,
        
        # Strategy 3: Enhanced array boundary detection for comma-separated objects
        lambda: json.loads(find_array_boundaries(text)) if find_array_boundaries(text) else None,
        
        # Strategy 4: Simple comma-separated object wrapper
        lambda: _wrap_comma_separated_objects(text),
        
        # Strategy 5: Use regex extraction
        lambda: extract_with_regex(text),
        
        # Strategy 6: Try to fix common JSON issues
        lambda: json.loads(text.replace('```json', '').replace('```', '').strip()),
        
        # Strategy 7: Handle trailing commas
        lambda: json.loads(re.sub(r',(\s*[}\]])', r'\1', text)),
        
        # Strategy 8: Remove extra trailing data after valid JSON
        lambda: _parse_json_with_trailing_data(text),
        
        # Strategy 9: Try to extract multiple JSON objects and wrap in array
        lambda: _extract_multiple_json_objects(text),
    ]
    
    for i, strategy in enumerate(strategies):
        try:
            #print(f"DEBUG: extract_json_from_text - Trying strategy {i+1}")
            result = strategy()
            if result is not None:
                #print(f"DEBUG: extract_json_from_text - Strategy {i+1} SUCCESS: {type(result)}")
                if isinstance(result, list):
                    #print(f"DEBUG: extract_json_from_text - Result is list with {len(result)} items")
                    pass
                elif isinstance(result, dict):
                    #print(f"DEBUG: extract_json_from_text - Result is dict with {len(result)} keys")
                    pass
                return result
        except Exception as e:
            #print(f"DEBUG: extract_json_from_text - Strategy {i+1} FAILED: {e}")
            continue
    
    #print(f"DEBUG: extract_json_from_text - All strategies failed")
    return None

def _extract_multiple_json_objects(text):
    """Extract multiple JSON objects from text and wrap them in an array."""
    # Find all JSON-like objects
    objects = []
    remaining = text
    
    while remaining:
        # Try to find a JSON object
        start_obj = remaining.find('{')
        if start_obj == -1:
            break
            
        # Find the end of this object
        depth = 0
        in_string = False
        escape_next = False
        end_pos = -1
        
        for i in range(start_obj, len(remaining)):
            char = remaining[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = i + 1
                        break
        
        if end_pos > 0:
            candidate = remaining[start_obj:end_pos]
            try:
                obj = json.loads(candidate)
                objects.append(obj)
                remaining = remaining[end_pos:]
            except:
                # Skip this and try to find the next object
                remaining = remaining[start_obj + 1:]
        else:
            break
    
    return objects if objects else None

def store_extraction_results(paper_id, model_id, response, temperature=None):
    """
    Store extraction results in the database with robust JSON parsing
    
    Args:
        paper_id: ID of the paper
        model_id: ID of the model
        response: Model response (raw or parsed)
        temperature: Temperature used for generation
        
    Returns:
        List of extraction run IDs created
    """
    #print(f"DEBUG: store_extraction_results - Starting with response type: {type(response)}")
    
    # Create extraction run
    run_id = ExtractionDAO.insert_extraction_run(paper_id, model_id, temperature, response)
    #print(f"DEBUG: store_extraction_results - Created run ID: {run_id}")
    
    # If response is a string, try to parse it with robust methods
    extraction_data = None
    parse_success = False
    
    #print(f"DEBUG: store_extraction_results - Response type: {type(response)}")
    if isinstance(response, str):
        #print(f"DEBUG: store_extraction_results - Response first 100 chars: {response[:100]}")
        pass

    if isinstance(response, str):
        #print("DEBUG: store_extraction_results - Response is string, attempting robust JSON parsing")
        pass
        
        # First clean the response to remove markdown artifacts
        try:
            cleaned_response = clean_json_response(response)
            #print(f"DEBUG: store_extraction_results - Cleaned response length: {len(cleaned_response)}")
            #print(f"DEBUG: store_extraction_results - Cleaned response first 100 chars: {cleaned_response[:100]}")
            
            # Try robust JSON extraction
            extraction_data = extract_json_from_text(cleaned_response)
            
            if extraction_data is not None:
                parse_success = True
                #print(f"DEBUG: store_extraction_results - JSON parsing SUCCESS. Type: {type(extraction_data)}")
                if isinstance(extraction_data, list):
                    #print(f"DEBUG: store_extraction_results - Parsed as list with {len(extraction_data)} items")
                    pass
                elif isinstance(extraction_data, dict):
                    #print(f"DEBUG: store_extraction_results - Parsed as dict with {len(extraction_data)} keys")
                    pass
            else:
                #print("DEBUG: store_extraction_results - All JSON parsing strategies failed")
                pass
                
        except Exception as e:
            #print(f"DEBUG: store_extraction_results - JSON parsing error: {e}")
            pass
            
            
    elif isinstance(response, dict):
        extraction_data = response
        parse_success = True
        #print(f"DEBUG: store_extraction_results - Response is already dict")
        
    elif isinstance(response, list):
        extraction_data = response
        parse_success = True
        #print(f"DEBUG: store_extraction_results - Response is already list")
    
    # If parsing failed, try to extract any recognizable data patterns
    if not parse_success and isinstance(response, str):
        #print("DEBUG: store_extraction_results - Attempting partial data extraction...")
        extraction_data = _extract_partial_data(response)
        if extraction_data:
            #print("DEBUG: store_extraction_results - Partial data extraction successful")
            pass
        else:
            #print("DEBUG: store_extraction_results - No recognizable data patterns found")
            pass
    
    # Helper function to store a single field with parameter parsing
    def store_field(run_id, field_name, field_data, model_instance_id):
        #print(f"DEBUG: store_field - Storing field '{field_name}' for instance {model_instance_id}")
        if isinstance(field_data, dict):
            value = field_data.get('value')
            confidence = field_data.get('confidence', 0)
            # Check for both references_text and references fields
            references = field_data.get('references_text')
            if references is None:
                references = field_data.get('references')
            
            if value is not None:
                # Parse parameter values if this is a parameter field
                if should_parse_field_as_parameter(field_name):
                    parsed_value = parse_parameter_value(value)
                    #print(f"DEBUG: store_field - Parsed parameter '{field_name}': '{value}' -> {parsed_value}")
                    value = parsed_value
                
                ExtractionDAO.insert_extracted_field(
                    run_id, field_name, value, confidence, references, model_instance_id
                )
        else:
            # If just a simple value, use default confidence
            value = field_data
            if value is not None:
                # Parse parameter values if this is a parameter field
                if should_parse_field_as_parameter(field_name):
                    parsed_value = parse_parameter_value(value)
                    #print(f"DEBUG: store_field - Parsed parameter '{field_name}': '{value}' -> {parsed_value}")
                    value = parsed_value
                
                ExtractionDAO.insert_extracted_field(
                    run_id, field_name, value, 50, None, model_instance_id
                )
    
    # Check if we have an array of models or a single model
    if isinstance(extraction_data, list):
        #print(f"DEBUG: store_extraction_results - Processing {len(extraction_data)} models from list")
        
        # Store each model with a different model_instance_id
        for model_idx, model_data in enumerate(extraction_data):
            #print(f"DEBUG: store_extraction_results - Processing model {model_idx + 1}/{len(extraction_data)}")
            if isinstance(model_data, dict):
                #print(f"DEBUG: store_extraction_results - Model {model_idx} has {len(model_data)} fields")
                # Store the fields for this model with its model_instance_id
                for field_name, field_data in model_data.items():
                    store_field(run_id, field_name, field_data, model_idx)
            else:
                #print(f"DEBUG: store_extraction_results - Warning: Model {model_idx} data type: {type(model_data)}")
                pass
                
    # Otherwise if it's a dict (single model), store with model_instance_id=0
    elif extraction_data and isinstance(extraction_data, dict):
        #print(f"DEBUG: store_extraction_results - Processing single model dict with {len(extraction_data)} fields")
        for field_name, field_data in extraction_data.items():
            store_field(run_id, field_name, field_data, 0)
    else:
        # If we couldn't parse the JSON, still store the run but with a note
        #print("DEBUG: store_extraction_results - Could not parse extraction data, storing run without fields")
        if extraction_data is None:
            #print("DEBUG: store_extraction_results - Raw response stored in extraction_run table for manual review")
            pass
    
    #print(f"DEBUG: store_extraction_results - Returning run_ids: [{run_id}]")
    return [run_id]

def _extract_partial_data(response_text):
    """
    Extract partial data from malformed responses using pattern matching.
    This is a fallback when JSON parsing completely fails.
    """
    try:
        # Look for common field patterns - now enhanced to handle multiple models
        patterns = {
            'model_name': r'"model_name"\s*:\s*[{]?\s*"value"\s*:\s*"([^"]*)"',
            'architecture': r'"architecture"\s*:\s*[{]?\s*"value"\s*:\s*"([^"]*)"',
            'domain': r'"domain"\s*:\s*[{]?\s*"value"\s*:\s*\[?["]?([^"\]]*)["]?',
            'organization': r'"organization"\s*:\s*[{]?\s*"value"\s*:\s*"([^"]*)"',
            'parameters': r'"parameters"\s*:\s*[{]?\s*"value"\s*:\s*"([^"]*)"',
            'training_dataset': r'"training_dataset"\s*:\s*[{]?\s*"value"\s*:\s*\[?["]?([^"\]]*)["]?',
            'input_modality': r'"input_modality"\s*:\s*[{]?\s*"value"\s*:\s*\[?["]?([^"\]]*)["]?',
            'output_modality': r'"output_modality"\s*:\s*[{]?\s*"value"\s*:\s*\[?["]?([^"\]]*)["]?',
        }
        
        # Try to find multiple model sections
        model_sections = []
        
        # Look for patterns that might indicate model boundaries
        # Split by potential model separators
        potential_models = re.split(r'}\s*[,\n\r]*\s*{', response_text)
        
        if len(potential_models) > 1:
            #print(f"Found {len(potential_models)} potential model sections in malformed response")
            
            for i, section in enumerate(potential_models):
                # Add back braces if they were removed by split
                if not section.strip().startswith('{'):
                    section = '{' + section
                if not section.strip().endswith('}'):
                    section = section + '}'
                
                extracted_model = {}
                for field, pattern in patterns.items():
                    match = re.search(pattern, section, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        # Create proper field structure
                        extracted_model[field] = {
                            "value": value,
                            "confidence": 30,  # Low confidence for partial extraction
                            "references": "partial extraction from malformed response"
                        }
                
                if extracted_model:
                    model_sections.append(extracted_model)
            
            return model_sections if model_sections else None
        else:
            # Single model case
            extracted = {}
            for field, pattern in patterns.items():
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    extracted[field] = {
                        "value": value,
                        "confidence": 30,
                        "references": "partial extraction from malformed response"
                    }
            
            return [extracted] if extracted else None  # Always return as array for consistency
        
    except Exception as e:
        #print(f"Error in partial data extraction: {e}")
        return None

def _wrap_comma_separated_objects(text):
    """Try to wrap comma-separated objects in an array."""
    #print(f"DEBUG: _wrap_comma_separated_objects - Input length: {len(text)} chars")
    #print(f"DEBUG: _wrap_comma_separated_objects - First 100 chars: {repr(text[:100])}")
    
    # Strategy 1: Try to find complete JSON objects separated by commas
    objects = []
    remaining = text.strip()
    
    while remaining:
        # Find the start of a JSON object
        start_obj = remaining.find('{')
        if start_obj == -1:
            #print(f"DEBUG: _wrap_comma_separated_objects - No more objects found")
            break
        
        #print(f"DEBUG: _wrap_comma_separated_objects - Found object start at position {start_obj}")
        
        # Find the end of this object by counting braces
        depth = 0
        in_string = False
        escape_next = False
        end_pos = -1
        
        for i in range(start_obj, len(remaining)):
            char = remaining[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        end_pos = i + 1
                        break
        
        if end_pos > 0:
            # Extract this object
            obj_text = remaining[start_obj:end_pos]
            #print(f"DEBUG: _wrap_comma_separated_objects - Extracted object: {len(obj_text)} chars")
            #print(f"DEBUG: _wrap_comma_separated_objects - Object preview: {repr(obj_text[:100])}")
            
            try:
                # Validate it's proper JSON
                obj = json.loads(obj_text)
                objects.append(obj)
                #print(f"DEBUG: _wrap_comma_separated_objects - Valid JSON object {len(objects)}")
                
                # Look for more objects after this one
                remaining = remaining[end_pos:].strip()
                
                # Skip any commas or whitespace
                if remaining.startswith(','):
                    remaining = remaining[1:].strip()
                    #print(f"DEBUG: _wrap_comma_separated_objects - Found comma, continuing...")
                elif remaining:
                    # Check if there's more content that might be another object
                    #print(f"DEBUG: _wrap_comma_separated_objects - Remaining content: {repr(remaining[:50])}")
                    if not remaining.startswith('{'):
                        # No more objects, stop here
                        #print(f"DEBUG: _wrap_comma_separated_objects - No more valid objects, stopping")
                        break
                else:
                    # No more content
                    #print(f"DEBUG: _wrap_comma_separated_objects - No more content")
                    break
                    
            except json.JSONDecodeError as e:
                #print(f"DEBUG: _wrap_comma_separated_objects - Invalid JSON: {e}")
                # If this object is invalid, stop processing
                break
        else:
            #print(f"DEBUG: _wrap_comma_separated_objects - Could not find complete object")
            break
    
    if len(objects) > 1:
        #print(f"DEBUG: _wrap_comma_separated_objects - Created array with {len(objects)} objects")
        return objects
    elif len(objects) == 1:
        #print(f"DEBUG: _wrap_comma_separated_objects - Single object found, wrapping in array")
        return [objects[0]]  # Always return as array for consistency
    
    #print(f"DEBUG: _wrap_comma_separated_objects - No valid objects found")
    return None

def _parse_json_with_trailing_data(text):
    """Parse JSON that may have extra content after the valid JSON structure."""
    #print(f"DEBUG: _parse_json_with_trailing_data - Input length: {len(text)} chars")
    #print(f"DEBUG: _parse_json_with_trailing_data - First 100 chars: {repr(text[:100])}")
    
    # Find the first opening bracket/brace
    first_obj = text.find('{')
    first_arr = text.find('[')
    
    #print(f"DEBUG: _parse_json_with_trailing_data - first_obj: {first_obj}, first_arr: {first_arr}")
    
    if first_obj == -1 and first_arr == -1:
        #print(f"DEBUG: _parse_json_with_trailing_data - No JSON found")
        return None
    
    # Determine starting point
    if first_obj == -1:
        start = first_arr
        is_array = True
        open_char, close_char = '[', ']'
    elif first_arr == -1:
        start = first_obj
        is_array = False
        open_char, close_char = '{', '}'
    else:
        if first_obj < first_arr:
            start = first_obj
            is_array = False
            open_char, close_char = '{', '}'
        else:
            start = first_arr
            is_array = True
            open_char, close_char = '[', ']'
    
    #print(f"DEBUG: _parse_json_with_trailing_data - Starting at {start}, is_array: {is_array}")
    
    # Track depth to find the end
    depth = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    # Found the end, extract just this part
                    json_text = text[start:i+1]
                    #print(f"DEBUG: _parse_json_with_trailing_data - Extracted JSON: {len(json_text)} chars")
                    #print(f"DEBUG: _parse_json_with_trailing_data - JSON preview: {repr(json_text[:100])}")
                    
                    try:
                        result = json.loads(json_text)
                        #print(f"DEBUG: _parse_json_with_trailing_data - SUCCESS parsing JSON")
                        # Always return as array for consistency
                        if isinstance(result, dict):
                            return [result]
                        else:
                            return result
                    except json.JSONDecodeError as e:
                        #print(f"DEBUG: _parse_json_with_trailing_data - JSON parsing failed: {e}")
                        return None
    
    #print(f"DEBUG: _parse_json_with_trailing_data - Could not find complete JSON structure")
    return None

def analyze_and_store(analyzer, md_file_path, model_name, provider, version=None,
                     arxiv_id=None, title=None, temperature=None, context_size=None, published_date=None):
    """
    Analyze a paper and store the results in the database
    
    Args:
        analyzer: Analyzer instance to use (BaseAnalyser or ChunkedAnalyser)
        md_file_path: Path to the markdown file
        model_name: Name of the model
        provider: Provider of the model
        version: Version of the model (optional)
        arxiv_id: ArXiv ID of the paper (optional)
        title: Title of the paper (optional)
        temperature: Temperature used for generation (optional)
        context_size: Context size in tokens (optional)
        published_date: Publication date of the paper (datetime object, optional)
        
    Returns:
        A tuple of (paper_id, model_id, list_of_run_ids)
    """
    # Import here to avoid circular imports
    from analyser.chunked_analyser import ChunkedAnalyser
    
    # Store the paper
    paper_id = store_paper_from_md_file(md_file_path, arxiv_id, title, True, published_date)
    if not paper_id:
        return None, None, None
    
    # Get or create the model
    model_id = get_or_create_model(model_name, provider, context_size, version)
    
    # Check if it's a chunked analyzer
    if isinstance(analyzer, ChunkedAnalyser):
        #print("Detected ChunkedAnalyser - using analyze_publication method")
        
        # Use the chunked analysis method
        try:
            text_file, json_file = analyzer.analyze_publication(md_file_path, arxiv_id=arxiv_id)
            
            if not json_file or not os.path.exists(json_file):
                #print("Error: ChunkedAnalyser did not produce a JSON response file")
                return paper_id, model_id, None
            
            # Read response from the generated file
            with open(json_file, 'r', encoding='utf-8') as f:
                response_content = f.read()
            
            #print(f"\nChunked LLM Response loaded from: {json_file}")
            #print(f"Response length: {len(response_content)} characters")
            
        except Exception as e:
            #print(f"Error in chunked analysis: {e}")
            return paper_id, model_id, None
    else:
        #print("Detected BaseAnalyser - using traditional prompt/query method")
        
        # Read the markdown content
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        except Exception as e:
            #print(f"Error reading markdown file: {e}")
            return paper_id, model_id, None
        
        # Prepare the prompt
        prompt = analyzer.prepare_prompt(markdown_content)
        
        # Query the LLM API
        response = analyzer.query_llm(prompt)
        
        if not response:
            #print("Error: No response from LLM API")
            return paper_id, model_id, None
        
        # Process the response
        try:
            response_content = analyzer.extract_response_content(response)
            #print("\nLLM Response:")
            #print(len(response_content))
        except Exception as e:
            #print(f"Error processing response: {e}")
            return paper_id, model_id, None
    
    # Store the results - now returns a list of run IDs (one per model)
    try:
        run_ids = store_extraction_results(paper_id, model_id, response_content, temperature)
        return paper_id, model_id, run_ids
    except Exception as e:
        #print(f"Error storing extraction results: {e}")
        return paper_id, model_id, None