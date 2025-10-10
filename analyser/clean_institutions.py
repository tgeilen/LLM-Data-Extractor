#!/usr/bin/env python3
"""
Script to clean and parse research institutions from orgs.txt file.
Creates a new file with one research institution per line for easy import into Google Sheets.
"""

import re
import json
import sys
from typing import List, Set


def clean_institution_name(name: str) -> str:
    """
    Clean and normalize an institution name.
    
    Args:
        name: Raw institution name
        
    Returns:
        Cleaned institution name
    """
    # Remove extra whitespace
    name = name.strip()
    
    # Remove all quotes (single and double)
    name = re.sub(r'["\']', '', name)
    
    # Remove brackets and parentheses
    name = re.sub(r'[\[\](){}]', '', name)
    
    # Remove common prefixes/suffixes that might be artifacts
    name = re.sub(r'^n/a$', '', name, flags=re.IGNORECASE)  # Remove n/a entries
    name = re.sub(r'^unknown$', '', name, flags=re.IGNORECASE)  # Remove unknown entries
    name = re.sub(r'^not specified$', '', name, flags=re.IGNORECASE)  # Remove not specified entries
    
    # Clean up extra spaces
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def parse_json_like_format(text: str) -> List[str]:
    """
    Parse JSON-like format entries like: {"University of Washington","Allen Institute for AI"}
    
    Args:
        text: Text containing JSON-like format
        
    Returns:
        List of institution names
    """
    institutions = []
    
    # Try to parse as JSON first
    try:
        # Replace double quotes with single quotes for JSON parsing
        json_text = text.replace('""', '"')
        parsed = json.loads(json_text)
        if isinstance(parsed, list):
            institutions.extend(parsed)
        elif isinstance(parsed, str):
            institutions.append(parsed)
    except json.JSONDecodeError:
        # If JSON parsing fails, try manual parsing
        # Remove outer braces and split by comma
        inner_text = text.strip('{}')
        # Split by comma, but be careful with commas inside quotes
        parts = []
        current_part = ""
        in_quotes = False
        quote_char = None
        
        for char in inner_text:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_part += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current_part += char
            elif char == ',' and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        institutions.extend(parts)
    
    return institutions


def split_by_separators(text: str) -> List[str]:
    """
    Split text by various separators: semicolon, comma, &, and 'and'.
    Handles multiple separators in the same text.
    
    Args:
        text: Text to split
        
    Returns:
        List of parts after splitting
    """
    # Define separators in order of preference (most specific first)
    separators = [';', ',', ' & ', ' and ']
    
    # Start with the original text
    current_parts = [text.strip()]
    
    # Apply each separator to all current parts
    for sep in separators:
        new_parts = []
        for part in current_parts:
            if sep in part:
                # Split this part by the separator
                split_parts = [p.strip() for p in part.split(sep) if p.strip()]
                new_parts.extend(split_parts)
            else:
                # Keep the part as is
                new_parts.append(part)
        current_parts = new_parts
    
    # Filter out empty parts
    return [part for part in current_parts if part.strip()]


def parse_institution_line(line: str) -> List[str]:
    """
    Parse a single line from the orgs.txt file and extract all institutions.
    
    Args:
        line: Single line from the file
        
    Returns:
        List of institution names found in the line
    """
    institutions = []
    line = line.strip()
    
    if not line or line.lower() in ['n/a', 'unknown', 'not specified', '']:
        return institutions
    
    # Handle JSON-like format (starts with { and contains double quotes)
    if line.startswith('{') and '""' in line:
        institutions.extend(parse_json_like_format(line))
    
    # Handle quoted strings
    elif line.startswith('"') and line.endswith('"'):
        # Remove outer quotes
        inner_text = line[1:-1]
        institutions.extend(split_by_separators(inner_text))
    
    # Handle unquoted strings with separators
    else:
        institutions.extend(split_by_separators(line))
    
    return institutions


def process_orgs_file(input_file: str, output_file: str) -> None:
    """
    Process the orgs.txt file and create a cleaned output file.
    
    Args:
        input_file: Path to input orgs.txt file
        output_file: Path to output cleaned file
    """
    all_institutions: Set[str] = set()
    
    print(f"Processing {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Parse the line
                institutions = parse_institution_line(line)
                
                # Clean and add institutions
                for inst in institutions:
                    cleaned = clean_institution_name(inst)
                    if cleaned:  # Only add non-empty institutions
                        all_institutions.add(cleaned)
                
                # Progress indicator
                if line_num % 100 == 0:
                    print(f"Processed {line_num} lines, found {len(all_institutions)} unique institutions so far...")
    
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Sort institutions alphabetically
    sorted_institutions = sorted(all_institutions)
    
    # Write to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for institution in sorted_institutions:
                f.write(f"{institution}\n")
        
        print(f"\nSuccessfully processed {len(sorted_institutions)} unique institutions.")
        print(f"Output written to: {output_file}")
        
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


def main():
    """Main function to run the script."""
    input_file = "orgs.txt"
    output_file = "cleaned_institutions.txt"
    
    # Allow command line arguments to override default files
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print("Research Institution Cleaner")
    print("=" * 40)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print()
    
    process_orgs_file(input_file, output_file)
    
    print(f"\nThe cleaned file '{output_file}' is ready")
    print("Each line contains one research institution.")


if __name__ == "__main__":
    main()
