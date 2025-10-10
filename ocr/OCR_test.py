import os
import base64
import json
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

#define API key
API_KEY = os.getenv('AZURE_OCR_API_KEY', 'your_azure_ocr_api_key_here')
API_ENDPOINT = os.getenv('AZURE_OCR_ENDPOINT', 'https://mistral-ocr-2503-zxbfx.eastus.models.ai.azure.com/v1/ocr')

def encode_pdf(pdf_path):
    """
    Encodes a PDF file to base64 string
    """
    print(f"\nStep 1: Encoding PDF file {pdf_path}")
    try:
        with open(pdf_path, "rb") as pdf_file:
            file_content = pdf_file.read()
            print(f"- Read {len(file_content)} bytes from PDF file")
            encoded_string = base64.b64encode(file_content).decode('utf-8')
            print("- Successfully encoded PDF to base64")
            return encoded_string
    except Exception as e:
        print(f"Error encoding PDF file: {str(e)}")
        print(f"- Full error details: {type(e).__name__}: {str(e)}")
        return None

def process_pdf_with_ocr(pdf_path, api_key = API_KEY, api_endpoint = API_ENDPOINT, use_annotations=False):
    """
    Sends a PDF to the Azure OCR API and returns the response
    
    Args:
        pdf_path: Path to PDF file
        api_key: API key for authentication
        api_endpoint: API endpoint URL
        use_annotations: Whether to use bbox annotations (set to False if endpoint doesn't support it)
    """
    print("\nStep 2: Processing PDF with OCR")
    
    # Add annotation info to logging
    ocr_type = "Enhanced OCR with annotations" if use_annotations else "Standard OCR"
    print(f"- OCR Type: {ocr_type}")
    
    # Prepare the PDF file
    base64_pdf = encode_pdf(pdf_path)
    
    if not base64_pdf:
        print("- Failed to encode PDF, aborting OCR process")
        return None
    
    print("- Preparing API request")
    # Prepare the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    print(f"- Using API endpoint: {api_endpoint}")
    
    # Payload according to the provided format
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "document_url": f"data:application/pdf;base64,{base64_pdf}",
            "type": "document_url"
        },
        "include_image_base64": True
    }
    
    # Add bbox_annotation_format only if annotations are enabled
    if use_annotations:
        try:
            from .ocr_models import ImageAnnotation, response_format_from_pydantic_model
            payload["bbox_annotation_format"] = response_format_from_pydantic_model(ImageAnnotation)
            print("- Added bbox annotation format to payload")
        except Exception as e:
            print(f"- Warning: Could not add annotation format: {e}")
            print("- Continuing with standard OCR...")
    
    print("- Request payload prepared")
    print(f"- Headers: {json.dumps({k: ('Bearer ' + '*'*8) if k == 'Authorization' else v for k, v in headers.items()})}")
    print(f"- Payload structure: {json.dumps({k: '...' if k == 'document' else v for k, v in payload.items()})}")
    
    try:
        print("\nStep 3: Sending request to API")
        #print(response)
        # Send the request
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=120)
        print(f"- Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"- Response parsed as JSON successfully")
            
            # Check for success
            if response.status_code == 200:
                #print(response_data)
                print("- Successfully received response from API")
                if isinstance(response_data, dict):
                    print(f"- Response contains keys: {list(response_data.keys())}")
                else:
                    print(f"- Response is not a dictionary. Type: {type(response_data)}")
                    print(f"- Response content: {str(response_data)[:500]}...")
                return response_data
            else:
                print(f"Error: HTTP Status {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                if isinstance(response_data, dict):
                    print(f"Error response contains keys: {list(response_data.keys())}")
                print(f"Response body: {str(response_data)[:500]}...")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {str(e)}")
            print("- Raw response content:")
            print(response.text[:500])
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {type(e).__name__}: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"- Response status code: {e.response.status_code}")
            print(f"- Response headers: {dict(e.response.headers)}")
            print(f"- Response content: {e.response.text[:500]}...")
        return None

def save_text_to_file(text, output_path):
    """
    Saves the extracted text to a file
    """
    print(f"\nStep 4: Saving extracted text to {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"- Successfully saved {len(text)} characters to file")
        return True
    except Exception as e:
        print(f"Error saving text to file: {type(e).__name__}: {str(e)}")
        return False

def save_json_to_file(json_data, output_path):
    """
    Saves JSON data to a file
    """
    print(f"\nStep 5: Saving full JSON response to {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        print(f"- Successfully saved JSON response to file")
        return True
    except Exception as e:
        print(f"Error saving JSON to file: {type(e).__name__}: {str(e)}")
        return False

def save_image_from_base64(base64_data, output_path):
    """
    Saves an image from base64 data to a file
    """
    try:
        # If the base64 data has a prefix like 'data:image/jpeg;base64,', remove it
        if ';base64,' in base64_data:
            base64_data = base64_data.split(';base64,')[1]
        
        # Decode the base64 data and save to file
        image_data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        print(f"- Saved image to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving image: {type(e).__name__}: {str(e)}")
        return False

def test_api_connection(api_key = API_KEY, api_endpoint = API_ENDPOINT):
    """
    Tests the connection to the API endpoint
    """
    print("\nTesting API connection...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        print(f"- Attempting to connect to {api_endpoint}")
        # Simple HEAD request to check if the endpoint is reachable
        response = requests.head(api_endpoint, headers=headers, timeout=10)
        print(f"- Received response with status code: {response.status_code}")
        
        # Check if we can connect (even if we get an error, we're just testing connectivity)
        if response.status_code < 500:  # Any non-server error is considered "reachable"
            print("- Endpoint is reachable")
            return True
        else:
            print(f"- API endpoint returned server error: {response.status_code}")
            print(f"- Response headers: {dict(response.headers)}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"- Connection error: {type(e).__name__}: {str(e)}")
        return False

def extract_and_save_images(result, output_dir):
    """
    Extracts images from the OCR result and saves them to the output directory
    """
    print("\nStep 6: Extracting and saving images")
    image_count = 0
    
    if 'pages' in result:
        for page in result['pages']:
            if 'images' in page and page['images']:
                print(f"- Found {len(page['images'])} images in page {page.get('index', 'unknown')}")
                for image in page['images']:
                    if 'image_base64' in image and image['image_base64']:
                        image_id = image.get('id', f"image_{image_count}")
                        image_path = os.path.join(output_dir, image_id)
                        if save_image_from_base64(image['image_base64'], image_path):
                            image_count += 1
    
    if image_count > 0:
        print(f"- Successfully saved {image_count} images")
    else:
        print("- No images found in the OCR results")
    
    return image_count

def main():
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process PDF with OCR')
    parser.add_argument('pdf_path', help='Path to the PDF file', nargs='?', default=None)
    parser.add_argument('--test-connection', action='store_true', help='Test API connection without processing files')
    parser.add_argument('--output-dir', help='Directory to store output files, defaults to results/{pdf_name}')
    parser.add_argument('--use-annotations', action='store_true', help='Use bbox annotations (requires supported endpoint)')
    args = parser.parse_args()
    
    # Get API credentials 
    
    api_endpoint = os.environ.get("AZURE_OCR_ENDPOINT", 
                                 "https://mistral-ocr-2503-zxbfx.eastus.models.ai.azure.com/v1/ocr")
    
    # Test API connection if requested
    if args.test_connection:
        if test_api_connection():
            print("API connection successful!")
        else:
            print("API connection failed.")
        return
    
    # Get the PDF path or use default sample
    pdf_path = args.pdf_path
    if pdf_path is None:
        # Use the default sample PDF
        sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
        os.makedirs(sample_dir, exist_ok=True)
        pdf_path = os.path.join(sample_dir, "samplePDF2.pdf")
        if not os.path.exists(pdf_path):
            print(f"Default sample PDF not found at {pdf_path}")
            print("Please provide a PDF file path or create the sample PDF at the default location.")
            return
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} does not exist.")
        return
    
    # Create output directory
    pdf_name = Path(pdf_path).stem
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join("results", pdf_name)
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"- Created output directory: {output_dir}")
    
    # Set output file paths
    output_path = os.path.join(output_dir, f"{pdf_name}.md")
    json_output_path = os.path.join(output_dir, f"{pdf_name}_response.json")
    
    print(f"Processing {pdf_path}...")
    print(f"Using annotations: {args.use_annotations}")
    
    # Test connection before processing
    if not test_api_connection():
        print("Cannot connect to API. Please check your connection and credentials.")
        return
    
    # Process the PDF with OCR
    result = process_pdf_with_ocr(pdf_path, use_annotations=args.use_annotations)
    
    if result:
        # Save the full JSON response
        save_json_to_file(result, json_output_path)
        
        # Extract the text from the OCR result based on the response structure
        # Response contains 'pages' array with each page having 'markdown' field
        extracted_text = ""
        
        if 'pages' in result:
            print(f"- Found {len(result['pages'])} pages in the response")
            for page in result['pages']:
                if 'markdown' in page:
                    extracted_text += page['markdown'] + "\n\n"
                    print(f"- Added text from page {page.get('index', 'unknown')}")
        
        if not extracted_text:
            print("Warning: No text was extracted from the PDF.")
            extracted_text = "No text extracted."
        else:
            print(f"- Successfully extracted {len(extracted_text)} characters from {len(result.get('pages', []))} pages")
        
        # Save the text to a file
        save_text_to_file(extracted_text, output_path)
        
        # Extract and save images
        image_count = extract_and_save_images(result, output_dir)
        
        print(f"\nProcessing complete! Saved to directory: {output_dir}")
        print(f"- Markdown file: {os.path.basename(output_path)}")
        print(f"- JSON response file: {os.path.basename(json_output_path)}")
        if image_count > 0:
            print(f"- Images: {image_count} files")
    else:
        print("Failed to process the PDF.")

if __name__ == "__main__":
    main()
