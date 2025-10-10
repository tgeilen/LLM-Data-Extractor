"""
This module contains utility functions for the analyzers.
"""

import os
import json
import re
import binascii  # For debugging byte sequences


def read_markdown_file(file_path):
    """
    Read the content of a Markdown file
    
    Args:
        file_path: Path to the Markdown file
        
    Returns:
        The content of the file as a string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"Error reading Markdown file: {e}")
        return None


def clean_json_response(response_text):
    """
    Clean the response text by removing markdown code block markers and invalid characters.
    
    Args:
        response_text: The response text from the API
        
    Returns:
        Cleaned response text
    """
    if not response_text:
        return ""
    
    #print("Original response first 20 chars:", repr(response_text[:20]))
    
    # Check for BOM and other invisible characters
    if len(response_text) > 0:
        # Print first few bytes for debugging
        #print("First 10 bytes:", binascii.hexlify(response_text[:10].encode('utf-8')))
        pass
    
    # CONSERVATIVE markdown removal - only remove when we're absolutely certain
    original_text = response_text
    
    # Pattern 1: Text that starts with ```json and ends with ```
    if response_text.strip().startswith('```json') and response_text.strip().endswith('```'):
        #print("Found complete ```json block")
        lines = response_text.strip().split('\n')
        if len(lines) >= 3:  # Must have at least opening, content, and closing
            # Remove first and last lines
            content = '\n'.join(lines[1:-1])
            response_text = content.strip()
            #print("Removed complete ```json markers")
    
    # Pattern 2: Text that starts with ``` (generic) and ends with ```
    elif response_text.strip().startswith('```') and response_text.strip().endswith('```') and not response_text.strip().startswith('```json'):
        print("Found complete generic ``` block")
        lines = response_text.strip().split('\n')
        if len(lines) >= 3:  # Must have at least opening, content, and closing
            # Remove first and last lines
            content = '\n'.join(lines[1:-1])
            response_text = content.strip()
            print("Removed complete ``` markers")
    
    # Pattern 3: Only starting markdown (partial)
    elif response_text.strip().startswith('```json\n'):
        print("Found partial ```json start")
        response_text = response_text.strip()[8:]  # Remove '```json\n'
        print("Removed partial ```json start")
    
    elif response_text.strip().startswith('```\n'):
        print("Found partial ``` start")
        response_text = response_text.strip()[4:]  # Remove '```\n'
        print("Removed partial ``` start")
    
    # Only proceed with cleaning if we actually modified something
    if response_text != original_text:
        #print("Applied markdown cleaning")
        pass
    else:
        #print("No markdown markers detected - leaving content unchanged")
        pass
    
    # More aggressive cleaning of non-printable and control characters
    # Remove BOM and zero-width characters
    response_text = response_text.replace('\ufeff', '')  # BOM
    response_text = response_text.replace('\u200b', '')  # Zero width space
    response_text = response_text.replace('\u200c', '')  # Zero width non-joiner
    response_text = response_text.replace('\u200d', '')  # Zero width joiner
    response_text = response_text.replace('\u200e', '')  # Left-to-right mark
    response_text = response_text.replace('\u200f', '')  # Right-to-left mark
    
    # Remove any control characters (ASCII < 32 except tabs and newlines)
    response_text = ''.join(c for c in response_text if ord(c) >= 32 or c in '\t\n\r')
    
    # Remove any leading/trailing whitespace
    response_text = response_text.strip()
    
    # CONSERVATIVE boundary fixing - only if content clearly doesn't start/end properly
    # AND the fix would make it valid JSON
    if response_text and response_text[0] not in '{[':
        # Try to find where the JSON actually starts
        json_start = response_text.find('{')
        if json_start == -1:
            json_start = response_text.find('[')
        
        if json_start != -1 and json_start < 50:  # Only if it's near the beginning
            print(f"Found JSON start at position {json_start}, trimming prefix")
            response_text = response_text[json_start:]
    
    # Check for proper JSON ending (similar conservative approach)
    if response_text and response_text[-1] not in '}]':
        # Try to find where the JSON actually ends
        json_end = response_text.rfind('}')
        if json_end == -1:
            json_end = response_text.rfind(']')
        
        if json_end != -1 and json_end > len(response_text) - 50:  # Only if it's near the end
            print(f"Found JSON end at position {json_end}, trimming suffix")
            response_text = response_text[:json_end+1]
    
    #print("First 10 cleaned bytes:", binascii.hexlify(response_text[:10].encode('utf-8')))
    return response_text


def escape_latex_for_json(text):
    """
    Escape LaTeX symbols and structures to prevent JSON parsing errors.
    
    Args:
        text: Text containing potential LaTeX syntax
        
    Returns:
        Text with LaTeX symbols properly escaped for JSON
    """
    if text is None:
        return None
        
    # Escape backslashes (must be done first)
    text = text.replace('\\', '\\\\')
    
    # Escape double quotes
    text = text.replace('"', '\\"')
    
    # Replace common LaTeX constructs that might cause issues
    # This is not exhaustive but covers common cases
    latex_replacements = {
        # Math delimiters
        '$': '\\$',
        # Control characters
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        # Special LaTeX characters
        '%': '\\%',
        '&': '\\&',
        '_': '\\_',
        '^': '\\^',
        '~': '\\~',
        # Braces are important in LaTeX but can be problematic in certain contexts
        # Only escape them if needed in your specific case
        # '{': '\\{',
        # '}': '\\}',
    }
    
    for char, replacement in latex_replacements.items():
        text = text.replace(char, replacement)
    
    return text


def save_analysis_results(response_text, output_dir, base_filename):
    """
    Save the analysis results as both text and JSON (if valid)
    
    Args:
        response_text: The text response from the LLM
        output_dir: Directory to save results to
        base_filename: The base name for output files
        
    Returns:
        Tuple of (text_file_path, json_file_path or None)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save raw text response (preserve original for debugging)
    text_file_raw = os.path.join(output_dir, f"{base_filename}_raw_response.txt")
    with open(text_file_raw, 'wb') as file:  # Use binary mode to preserve all bytes
        file.write(response_text.encode('utf-8'))
    
    # Clean and process for JSON
    
    text_file = os.path.join(output_dir, f"{base_filename}_response.txt")
    with open(text_file, 'w', encoding='utf-8') as file:
        file.write(response_text)
    
    cleaned_response = clean_json_response(response_text)
    
    # Try to save as JSON if valid
    json_file = None
    try:
        # Use our robust JSON extraction function instead of json.loads
        if cleaned_response.strip().startswith('['):
            # For arrays, try direct parsing first without escaping (arrays are more fragile)
            print("DEBUG: Attempting direct JSON parsing for array response")
            try:
                from analyser.db_integration import extract_json_from_text
                json_response = extract_json_from_text(cleaned_response)
                
                if json_response is not None:
                    print(f"DEBUG: Direct array parsing SUCCESS - type: {type(json_response)}")
                    if isinstance(json_response, list):
                        print(f"DEBUG: Direct array parsing SUCCESS - {len(json_response)} items")
                else:
                    print(f"DEBUG: Direct array parsing failed, trying with LaTeX escaping")
                    # Only escape as fallback for arrays
                    escaped_response = escape_latex_for_json(cleaned_response)
                    json_response = extract_json_from_text(escaped_response)
                    
                    if json_response is not None:
                        print(f"DEBUG: Array parsing with escaping SUCCESS")
                    else:
                        raise ValueError("Both direct and escaped parsing failed for array")
            except Exception as e:
                print(f"DEBUG: Array parsing failed: {e}")
                raise e
        else:
            # For objects, always use LaTeX escaping (objects are more robust to escaping)
            print("DEBUG: Attempting JSON parsing for object response with LaTeX escaping")
            escaped_response = escape_latex_for_json(cleaned_response)
            from analyser.db_integration import extract_json_from_text
            json_response = extract_json_from_text(escaped_response)
            
            if json_response is not None:
                print(f"DEBUG: Object parsing with escaping SUCCESS")
            else:
                print(f"DEBUG: Object parsing failed, trying without escaping")
                # Fallback: try without escaping
                json_response = extract_json_from_text(cleaned_response)
                if json_response is not None:
                    print(f"DEBUG: Object parsing without escaping SUCCESS")
                else:
                    raise ValueError("Both escaped and direct parsing failed for object")
            
        json_file = os.path.join(output_dir, f"{base_filename}_analysis.json")
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(json_response, file, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"DEBUG: JSON parsing failed: {e}")
        
        # FIXED: One last attempt - properly handle both arrays and objects
        try:
            # Create a completely new JSON string from scratch
            json_file = os.path.join(output_dir, f"{base_filename}_analysis.json")
            
            # Read the cleaned response again
            content = cleaned_response.strip()
            
            # CRITICAL FIX: Preserve array structure
            if content.startswith('['):
                # For arrays, find the matching closing bracket
                bracket_count = 0
                start_pos = 0
                end_pos = len(content)
                
                # Find the actual end of the JSON array
                for i, char in enumerate(content):
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break
                
                json_content = content[start_pos:end_pos]
                print(f"DEBUG: Extracted array JSON: {len(json_content)} characters")
                
                # Try to parse the extracted array with our robust function
                try:
                    from analyser.db_integration import extract_json_from_text
                    test_parse = extract_json_from_text(json_content)
                    if test_parse is not None:
                        # If it parses successfully, save the parsed version
                        with open(json_file, 'w', encoding='utf-8') as file:
                            json.dump(test_parse, file, indent=2, ensure_ascii=False)
                        print("DEBUG: Created JSON file using robust parsing")
                    else:
                        # If parsing fails, save the raw extracted content
                        with open(json_file, 'w', encoding='utf-8') as file:
                            file.write(json_content)
                        print("DEBUG: Created JSON file using direct array extraction")
                except:
                    # Last resort: save raw content
                    with open(json_file, 'w', encoding='utf-8') as file:
                        file.write(json_content)
                    print("DEBUG: Created JSON file using raw array extraction")
                
            else:
                # For objects, find start and end of JSON object (original logic)
                start = content.find('{')
                end = content.rfind('}') + 1
                
                if start >= 0 and end > start:
                    json_content = content[start:end]
                    print(f"DEBUG: Extracted object JSON: {len(json_content)} characters")
                    
                    # Try to parse the extracted object with our robust function
                    try:
                        from analyser.db_integration import extract_json_from_text
                        # For objects, apply LaTeX escaping before parsing
                        escaped_content = escape_latex_for_json(json_content)
                        test_parse = extract_json_from_text(escaped_content)
                        if test_parse is not None:
                            # If it parses successfully, save the parsed version
                            with open(json_file, 'w', encoding='utf-8') as file:
                                json.dump(test_parse, file, indent=2, ensure_ascii=False)
                            print("DEBUG: Created JSON file using robust parsing with escaping")
                        else:
                            # If parsing fails, save the raw extracted content
                            with open(json_file, 'w', encoding='utf-8') as file:
                                file.write(json_content)
                            print("DEBUG: Created JSON file using direct object extraction")
                    except:
                        # Last resort: save raw content
                        with open(json_file, 'w', encoding='utf-8') as file:
                            file.write(json_content)
                        print("DEBUG: Created JSON file using raw object extraction")
                else:
                    raise ValueError("No valid JSON structure found")
            
            print("DEBUG: Created JSON file using corrected direct extraction")
            
        except Exception as ex:
            print(f"DEBUG: Final JSON creation attempt failed: {ex}")
            json_file = None
        
        # Save the escaped version for debugging
        debug_file = os.path.join(output_dir, f"{base_filename}_debug_escaped.txt")
        with open(debug_file, 'wb') as file:  # Binary mode to preserve all bytes
            file.write(cleaned_response.encode('utf-8'))
    
    return text_file, json_file


def parse_parameter_value(value_str):
    """
    Parse parameter values like "13B", "670M", "1.2K" into actual numbers.
    
    Args:
        value_str: String representation of the parameter value
        
    Returns:
        The numeric value as an integer or float, or None if parsing fails
    """
    if not value_str or not isinstance(value_str, str):
        return None
    
    # Clean the string - remove spaces and make uppercase
    clean_str = value_str.strip().upper()
    
    # Handle special cases
    if clean_str in ['UNKNOWN', 'N/A', 'NA', '-', '']:
        return None
    
    # Regular expression to match number followed by optional unit
    # Supports formats like: 13B, 670M, 1.2K, 50.5, 13.7B, etc.
    pattern = r'^([0-9]*\.?[0-9]+)\s*([KMGTB]?)$'
    match = re.match(pattern, clean_str)
    
    if not match:
        # Try to parse as plain number
        try:
            return float(clean_str)
        except ValueError:
            return None
    
    number_part = float(match.group(1))
    unit = match.group(2)
    
    # Convert based on unit
    multipliers = {
        'K': 1_000,
        'M': 1_000_000,
        'G': 1_000_000_000,
        'T': 1_000_000_000_000,
        'B': 1_000_000_000  # B typically means billion in model parameters
    }
    
    if unit in multipliers:
        result = number_part * multipliers[unit]
        # Return as integer if it's a whole number
        return int(result) if result.is_integer() else result
    else:
        # No unit, return the number as-is
        return int(number_part) if number_part.is_integer() else number_part


def should_parse_as_parameter(field_name):
    """
    Determine if a field should be parsed as a parameter value based on its name.
    
    Args:
        field_name: Name of the field
        
    Returns:
        True if the field should be parsed as a parameter value
    """
    if not field_name:
        return False
    
    field_lower = field_name.lower()
    
    # Fields that typically contain parameter counts
    parameter_indicators = [
        'parameter', 'param', 'size', 'model_size', 'num_param',
        'total_param', 'trainable_param', 'model_param'
    ]
    
    return any(indicator in field_lower for indicator in parameter_indicators)


def parse_parameter_value(value):
    """
    Parse parameter values like "13B", "670M", "1.3T", "156 billion", "156 Billion", "156 trillion token" into actual numbers.
    
    Args:
        value: The parameter value to parse (string, int, or float)
        
    Returns:
        The parsed numeric value if it's a parameter count, otherwise the original value
        
    Examples:
        "13B" -> 13000000000
        "670M" -> 670000000
        "1.2K" -> 1200
        "156 billion" -> 156000000000
        "156 Billion" -> 156000000000
        "156 trillion token" -> 156000000000000
        "500" -> 500
        "text value" -> "text value"
    """
    if not isinstance(value, str):
        return value
    
    # Clean the string
    clean_value = str(value).strip()
    
    # First try the abbreviated format (13B, 670M, etc.)
    abbreviated_pattern = r'^([0-9]*\.?[0-9]+)\s*([KMGTB])?$'
    match = re.match(abbreviated_pattern, clean_value, re.IGNORECASE)
    
    if match:
        number_str = match.group(1)
        suffix = match.group(2)
        
        try:
            number = float(number_str)
            
            if suffix:
                suffix = suffix.upper()
                multipliers = {
                    'K': 1_000,           # Thousand
                    'M': 1_000_000,       # Million  
                    'G': 1_000_000_000,   # Billion (sometimes used instead of B)
                    'T': 1_000_000_000_000, # Trillion
                    'B': 1_000_000_000    # Billion
                }
                
                if suffix in multipliers:
                    number *= multipliers[suffix]
            
            # Convert to int if it's a whole number, otherwise keep as float
            if number.is_integer():
                return int(number)
            else:
                return number
                
        except (ValueError, AttributeError):
            pass
    
    # Try spelled-out format (156 billion, 670 million, etc.)
    # Pattern matches: number + optional decimal + spelled-out unit + optional trailing words
    spelled_pattern = r'^([0-9]*\.?[0-9]+)\s+(thousand|million|billion|trillion)(?:\s+\w+)*$'
    match = re.match(spelled_pattern, clean_value, re.IGNORECASE)
    
    if match:
        number_str = match.group(1)
        unit = match.group(2).lower()
        
        try:
            number = float(number_str)
            
            # Apply multipliers for spelled-out units
            spelled_multipliers = {
                'thousand': 1_000,
                'million': 1_000_000,
                'billion': 1_000_000_000,
                'trillion': 1_000_000_000_000
            }
            
            if unit in spelled_multipliers:
                number *= spelled_multipliers[unit]
            
            # Convert to int if it's a whole number, otherwise keep as float
            if number.is_integer():
                return int(number)
            else:
                return number
                
        except (ValueError, AttributeError):
            pass
    
    # If neither pattern matches, return original value
    return value


def should_parse_field_as_parameter(field_name: str) -> bool:
    """
    Determine if a field should be parsed as a parameter count.
    
    Args:
        field_name: The name of the field
        
    Returns:
        True if the field should be parsed as a parameter count
    """
    parameter_fields = {
        'parameters',
        'parameter_count', 
        'num_parameters',
        'model_parameters',
        'total_parameters',
        'training_dataset_size',
        'dataset_size',
        'vocab_size',
        'vocabulary_size',
        'context_length',
        'sequence_length',
        'max_length',
        'hidden_size',
        'embedding_size',
        'num_layers',
        'num_heads',
        'attention_heads'
    }
    
    # Check if field name matches any parameter field (case insensitive)
    field_lower = field_name.lower()
    return any(param_field in field_lower for param_field in parameter_fields)


def format_parameter_display(numeric_value):
    """
    Convert a numeric parameter value back to human-readable format for display.
    
    Args:
        numeric_value: Numeric parameter value
        
    Returns:
        str: Human-readable format (e.g., "13B", "670M")
    """
    if not isinstance(numeric_value, (int, float)) or numeric_value <= 0:
        return str(numeric_value)
    
    # Define thresholds and suffixes
    if numeric_value >= 1_000_000_000_000:  # Trillion
        return f"{numeric_value / 1_000_000_000_000:.1f}T".rstrip('0').rstrip('.')
    elif numeric_value >= 1_000_000_000:  # Billion
        return f"{numeric_value / 1_000_000_000:.1f}B".rstrip('0').rstrip('.')
    elif numeric_value >= 1_000_000:  # Million
        return f"{numeric_value / 1_000_000:.1f}M".rstrip('0').rstrip('.')
    elif numeric_value >= 1_000:  # Thousand
        return f"{numeric_value / 1_000:.1f}K".rstrip('0').rstrip('.')
    else:
        return str(int(numeric_value) if numeric_value == int(numeric_value) else numeric_value)