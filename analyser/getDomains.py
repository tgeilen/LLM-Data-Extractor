import csv
import os
import json

def get_unique_domains(csv_file_path):
    """
    Extract all unique domains from the given CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        A sorted list of unique domains
    """
    # Check if file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: File not found at {csv_file_path}")
        return []
    
    unique_domains = set()
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Check if 'Domain' column exists
            if 'Domain' not in reader.fieldnames:
                print("Error: CSV file does not contain a 'Domain' column")
                return []
                
            # Extract all domains
            for row in reader:
                domain = row.get('Domain', '').strip()
                if domain:
                    # Some domains might be comma-separated within the field
                    # (like "Multimodal,Language")
                    for d in domain.split(','):
                        unique_domains.add(d.strip())
    
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []
    
    # Return sorted list of unique domains
    return sorted(list(unique_domains))

def main():
    # Path to the CSV file
    csv_file_path = "/Users/tobig/code/MasterThesis/OCR/code/Epoch Database - Notable Models.csv"
    
    # Output JSON file path
    output_file = "domains.json"
    
    # Get unique domains
    domains = get_unique_domains(csv_file_path)
    
    # Save to JSON file
    if domains:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(domains, f, indent=2)
        print(f"Saved {len(domains)} unique domains to {output_file}")
        
        # Also print to console
        print(json.dumps(domains, indent=2))
    else:
        print("No domains found.")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("[]")

if __name__ == "__main__":
    main()
