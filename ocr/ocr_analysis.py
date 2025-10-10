import os
import json
import base64
import requests
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from .ocr_models import ImageAnnotation, response_format_from_pydantic_model

class EnhancedOCRProcessor:
    """Enhanced OCR processor with detailed image annotations only"""
    
    def __init__(self, api_key: str, api_endpoint: str, timeout: int = 120):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def encode_pdf(self, pdf_path: str) -> Optional[str]:
        """Encode PDF file to base64 string"""
        try:
            with open(pdf_path, "rb") as pdf_file:
                file_content = pdf_file.read()
                encoded_string = base64.b64encode(file_content).decode('utf-8')
                return encoded_string
        except Exception as e:
            print(f" Error encoding PDF: {e}")
            return None
    
    def process_pdf_with_annotations(
        self, 
        pdf_path: str, 
        output_dir: str,
        max_pages: int = 8,
        include_images: bool = False,
        use_annotations: bool = True,  # New flag to control annotation usage
        verbose: bool = False
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
        """
        Process PDF with enhanced OCR including detailed image annotations only
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save results
            max_pages: Maximum pages to process for annotations (API limit: 8)
            include_images: Whether to include base64 images in response
            use_annotations: Whether to use bbox annotations (set to False if endpoint doesn't support it)
            verbose: Enable detailed logging
            
        Returns:
            Tuple of (markdown_path, json_path, annotations_dict)
        """
        if verbose:
            ocr_type = "Enhanced OCR with annotations" if use_annotations else "Standard OCR"
            print(f" Processing PDF with {ocr_type}: {pdf_path}")
        
        # Encode PDF
        base64_pdf = self.encode_pdf(pdf_path)
        if not base64_pdf:
            return None, None, None
        
        # Try enhanced OCR with bbox annotations if enabled
        if use_annotations:
            try:
                if verbose:
                    print("  - Attempting enhanced OCR with bbox annotations...")
                
                payload = {
                    "model": "mistral-ocr-latest",
                    "document": {
                        "document_url": f"data:application/pdf;base64,{base64_pdf}",
                        "type": "document_url"
                    },
                    "bbox_annotation_format": response_format_from_pydantic_model(ImageAnnotation),
                    "include_image_base64": include_images
                }
                
                start_time = time.time()
                response = requests.post(
                    self.api_endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                elapsed_time = time.time() - start_time
                
                if verbose:
                    print(f"  - Enhanced OCR response received in {elapsed_time:.2f}s (Status: {response.status_code})")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result is not None and isinstance(result, dict):
                        if verbose:
                            print("  - Enhanced OCR with annotations succeeded!")
                        return self._process_ocr_response(result, pdf_path, output_dir, verbose)
                    else:
                        if verbose:
                            print("  - Enhanced OCR returned None/invalid response, falling back to standard OCR...")
                        raise Exception("Enhanced OCR returned None response")
                else:
                    if verbose:
                        print(f"  - Enhanced OCR failed with status {response.status_code}, falling back to standard OCR...")
                    raise Exception(f"Enhanced OCR API error: {response.status_code}")
                    
            except Exception as e:
                if verbose:
                    print(f"  - Enhanced OCR with annotations failed: {str(e)}")
                    print("  - Falling back to standard OCR...")
        
        # Standard OCR fallback (or direct use if use_annotations=False)
        try:
            if verbose:
                fallback_msg = "  - Using standard OCR fallback..." if use_annotations else "  - Using standard OCR..."
                print(fallback_msg)
            
            fallback_payload = {
                "model": "mistral-ocr-latest",
                "document": {
                    "document_url": f"data:application/pdf;base64,{base64_pdf}",
                    "type": "document_url"
                },
                "include_image_base64": include_images
            }
            
            fallback_response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=fallback_payload,
                timeout=self.timeout
            )
            
            if fallback_response.status_code == 200:
                result = fallback_response.json()
                if result is not None and isinstance(result, dict):
                    if verbose:
                        success_msg = "  - Standard OCR fallback succeeded!" if use_annotations else "  - Standard OCR succeeded!"
                        print(success_msg)
                    return self._process_ocr_response(result, pdf_path, output_dir, verbose)
                else:
                    print(" Standard OCR also returned None")
                    return None, None, None
            else:
                print(f" Standard OCR failed: {fallback_response.status_code}")
                return None, None, None
                
        except Exception as fallback_error:
            print(f" Standard OCR error: {fallback_error}")
            return None, None, None

    def _process_ocr_response(
        self, 
        result: Dict, 
        pdf_path: str, 
        output_dir: str, 
        verbose: bool
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
        """Process the OCR API response and save results"""
        
        # Validate result parameter
        if result is None:
            print(" Cannot process None result")
            return None, None, None
        
        if not isinstance(result, dict):
            print(f" Result must be a dictionary, got {type(result)}")
            return None, None, None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        pdf_name = Path(pdf_path).stem
        
        # Extract text content and image annotations
        extracted_text = ""
        image_annotations = []
        
        # Check if pages exist in result
        if 'pages' not in result:
            print("️ No 'pages' key found in OCR response")
            pages = []
        else:
            pages = result['pages']
            if pages is None:
                print("️ Pages is None in OCR response")
                pages = []
        
        if verbose and pages:
            print(f"  - Processing {len(pages)} pages")
        
        for page_idx, page in enumerate(pages):
            # Validate page object
            if page is None:
                if verbose:
                    print(f"  - Skipping None page at index {page_idx}")
                continue
            
            if not isinstance(page, dict):
                if verbose:
                    print(f"  - Skipping invalid page at index {page_idx}: {type(page)}")
                continue
            
            # Add page header
            extracted_text += f"\n\n--- Page {page_idx + 1} ---\n\n"
            
            # Add markdown content (this is the key part that was missing!)
            if 'markdown' in page and page['markdown'] is not None:
                extracted_text += page['markdown'] + "\n\n"
            
            # Process image annotations if they exist
            if 'bbox_annotations' in page and page['bbox_annotations'] is not None:
                page_annotations = self._process_page_annotations(
                    page['bbox_annotations'], 
                    page_idx + 1, 
                    verbose
                )
                if page_annotations:
                    image_annotations.extend(page_annotations)
                    
                    # Add annotation summaries to markdown
                    extracted_text += "\n### Visual Elements on this Page:\n\n"
                    for i, annotation in enumerate(page_annotations):
                        title = annotation.get('title', 'Untitled') if annotation else 'Untitled'
                        img_type = annotation.get('image_type', 'Unknown') if annotation else 'Unknown'
                        description = annotation.get('detailed_description', 'No description') if annotation else 'No description'
                        
                        extracted_text += f"**Figure {page_idx + 1}.{i + 1}:** {title}\n"
                        extracted_text += f"- Type: {img_type}\n"
                        extracted_text += f"- Description: {description}\n"
                        
                        if annotation and annotation.get('data_content'):
                            extracted_text += f"- Data: {annotation['data_content']}\n"
                        if annotation and annotation.get('key_insights'):
                            extracted_text += f"- Key Insights: {annotation['key_insights']}\n"
                        if annotation and annotation.get('visualization_type'):
                            extracted_text += f"- Chart Type: {annotation['visualization_type']}\n"
                        extracted_text += "\n"
        
        # Ensure we have some content even if no markdown was found
        if not extracted_text.strip():
            extracted_text = "No text content extracted from PDF."
            if verbose:
                print("️ No markdown content found in any pages")
        
        # Save markdown file
        md_path = os.path.join(output_dir, f"{pdf_name}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Save complete JSON response
        json_path = os.path.join(output_dir, f"{pdf_name}_ocr_response.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Save structured annotations if any were found
        annotations_summary = None
        if image_annotations:
            annotations_path = os.path.join(output_dir, f"{pdf_name}_image_annotations.json")
            annotations_summary = {
                'total_annotations': len(image_annotations),
                'annotations_by_page': {},
                'all_annotations': image_annotations,
                'annotation_types': self._get_annotation_statistics(image_annotations)
            }
            
            # Group annotations by page
            for annotation in image_annotations:
                page_num = annotation.get('page', 1)
                if page_num not in annotations_summary['annotations_by_page']:
                    annotations_summary['annotations_by_page'][page_num] = []
                annotations_summary['annotations_by_page'][page_num].append(annotation)
            
            with open(annotations_path, 'w', encoding='utf-8') as f:
                json.dump(annotations_summary, f, indent=2, ensure_ascii=False)
            
            if verbose:
                print(f"  - Image annotations: {annotations_path}")
        
        if verbose:
            print(f" OCR processing complete:")
            print(f"  - Markdown: {md_path}")
            print(f"  - Full response: {json_path}")
            print(f"  - Text length: {len(extracted_text):,} characters")
            print(f"  - Image annotations: {len(image_annotations)}")
        
        return md_path, json_path, annotations_summary
    
    def _process_page_annotations(
        self, 
        bbox_annotations: List[Dict], 
        page_num: int, 
        verbose: bool
    ) -> List[Dict]:
        """Process image annotations for a single page"""
        
        processed_annotations = []
        
        for i, annotation in enumerate(bbox_annotations):
            try:
                # Extract the structured annotation data
                annotation_data = annotation.get('annotation', {})
                
                processed_annotation = {
                    'page': page_num,
                    'annotation_id': f"page_{page_num}_img_{i + 1}",
                    'bbox': annotation.get('bbox', {}),
                    **annotation_data
                }
                
                processed_annotations.append(processed_annotation)
                
                if verbose:
                    img_type = annotation_data.get('image_type', 'Unknown')
                    title = annotation_data.get('title', 'Untitled')
                    print(f"    - Found {img_type}: {title}")
                
            except Exception as e:
                if verbose:
                    print(f"    - Warning: Could not process annotation {i}: {e}")
                continue
        
        return processed_annotations
    
    def _get_annotation_statistics(self, annotations: List[Dict]) -> Dict[str, int]:
        """Get statistics about annotation types"""
        stats = {}
        for annotation in annotations:
            img_type = annotation.get('image_type', 'unknown')
            stats[img_type] = stats.get(img_type, 0) + 1
        return stats

# Convenience function for backward compatibility
def process_pdf_with_enhanced_ocr(
    pdf_path: str,
    output_dir: Optional[str] = None,
    api_key: Optional[str] = None,
    api_endpoint: Optional[str] = None,
    max_pages: int = 8,
    include_images: bool = False,
    use_annotations: bool = True,  # New parameter
    verbose: bool = True
) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
    """
    Enhanced OCR processing function with detailed image annotations only
    
    This function provides detailed analysis of visual content in PDFs,
    focusing specifically on images, graphs, charts, tables, and figures.
    
    Args:
        use_annotations: Whether to use bbox annotations (set to False if endpoint doesn't support it)
    """
    
    # Use default configuration if not provided
    if not api_key:
        api_key = os.getenv('AZURE_OCR_API_KEY', 'your_azure_ocr_api_key_here')
    if not api_endpoint:
        api_endpoint = os.getenv('AZURE_OCR_ENDPOINT', 'https://mistral-ocr-2503-zxbfx.eastus.models.ai.azure.com/v1/ocr')
    
    if not output_dir:
        pdf_name = Path(pdf_path).stem
        output_dir = f"results/{pdf_name}"
    
    # Create enhanced OCR processor
    processor = EnhancedOCRProcessor(api_key, api_endpoint)
    
    # Process the PDF
    return processor.process_pdf_with_annotations(
        pdf_path, 
        output_dir, 
        max_pages, 
        include_images, 
        use_annotations,  # Pass the flag
        verbose
    )
