import fitz  # PyMuPDF
import numpy as np
import cv2
import pytesseract
from PIL import Image
import io
from typing import Dict, List, Tuple, Optional, Union
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    MIXED = "mixed"

@dataclass
class PageAnalysis:
    page_type: PageType
    text_percentage: float
    image_percentage: float
    dpi: Optional[float] = None
    is_scanned: bool = False

class HybridPDFProcessor:
    def __init__(self):
        self.text_threshold = 0.1  # Minimum text content to consider page as text
        self.min_text_confidence = 0.6  # OCR confidence threshold
        self.target_dpi = 300  # Target DPI for image processing
        
    def analyze_page(self, page: fitz.Page) -> PageAnalysis:
        """Determine if page is text-based, image-based, or mixed"""
        try:
            # Get text content
            text_areas = page.get_text("dict")["blocks"]
            text_count = sum(1 for block in text_areas if block["type"] == 0)
            
            # Get image content
            image_list = page.get_images()
            image_count = len(image_list)
            
            # Calculate page coverage
            page_area = page.rect.width * page.rect.height
            text_area = sum(
                (block["bbox"][2] - block["bbox"][0]) * 
                (block["bbox"][3] - block["bbox"][1])
                for block in text_areas if block["type"] == 0
            )
            
            # Calculate percentages
            text_percentage = text_area / page_area
            image_percentage = self._calculate_image_coverage(page, image_list)
            
            # Determine if page is scanned
            is_scanned = self._check_if_scanned(page, image_list)
            
            # Determine page type
            if text_percentage > 0.7:
                page_type = PageType.TEXT
            elif image_percentage > 0.7:
                page_type = PageType.IMAGE
            else:
                page_type = PageType.MIXED
                
            # Calculate DPI if it's an image page
            dpi = self._calculate_dpi(page) if page_type != PageType.TEXT else None
            
            return PageAnalysis(
                page_type=page_type,
                text_percentage=text_percentage,
                image_percentage=image_percentage,
                dpi=dpi,
                is_scanned=is_scanned
            )
            
        except Exception as e:
            logger.error(f"Error analyzing page: {str(e)}")
            return PageAnalysis(
                page_type=PageType.TEXT,  # Default to TEXT as safer option
                text_percentage=1.0,
                image_percentage=0.0
            )

    def process_page(self, page: fitz.Page) -> Dict:
        """Process page using appropriate method based on content type"""
        try:
            # Analyze page type
            analysis = self.analyze_page(page)
            logger.info(f"Page analysis: {analysis}")
            
            if analysis.page_type == PageType.TEXT:
                return self._process_text_page(page)
            elif analysis.page_type == PageType.IMAGE:
                return self._process_image_page(page)
            else:
                return self._process_mixed_page(page, analysis)
                
        except Exception as e:
            logger.error(f"Error processing page: {str(e)}")
            return {}

    def _process_text_page(self, page: fitz.Page) -> Dict:
        """Process page using text-based methods"""
        try:
            # Extract text blocks
            blocks = page.get_text("dict")["blocks"]
            
            # Process text blocks for questions
            questions = []
            for block in blocks:
                if block["type"] == 0:  # Text block
                    question_info = self._extract_question_from_text(block)
                    if question_info:
                        questions.append(question_info)
            
            return {
                'page_type': PageType.TEXT.value,
                'questions': questions,
                'confidence': 1.0  # High confidence for text-based extraction
            }
            
        except Exception as e:
            logger.error(f"Error processing text page: {str(e)}")
            return {}

    def _process_image_page(self, page: fitz.Page) -> Dict:
        """Process page using image-based methods"""
        try:
            # Convert page to image at appropriate DPI
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Perform OCR
            ocr_data = pytesseract.image_to_data(
                img, 
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )
            
            # Process OCR results for questions
            questions = self._extract_questions_from_ocr(ocr_data)
            
            # Calculate overall confidence
            confidence = np.mean([q['confidence'] for q in questions]) if questions else 0.0
            
            return {
                'page_type': PageType.IMAGE.value,
                'questions': questions,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error processing image page: {str(e)}")
            return {}

    def _process_mixed_page(self, page: fitz.Page, analysis: PageAnalysis) -> Dict:
        """Process page containing both text and images"""
        try:
            # Get results from both methods
            text_results = self._process_text_page(page)
            image_results = self._process_image_page(page)
            
            # Merge results, preferring higher confidence detections
            merged_questions = self._merge_question_results(
                text_results.get('questions', []),
                image_results.get('questions', []),
                analysis
            )
            
            return {
                'page_type': PageType.MIXED.value,
                'questions': merged_questions,
                'confidence': np.mean([q['confidence'] for q in merged_questions]) 
                    if merged_questions else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error processing mixed page: {str(e)}")
            return {}

    def _merge_question_results(
        self,
        text_questions: List[Dict],
        image_questions: List[Dict],
        analysis: PageAnalysis
    ) -> List[Dict]:
        """Merge and deduplicate questions from text and image processing"""
        merged = []
        used_positions = set()
        
        # Sort questions by confidence
        all_questions = [(q, 'text') for q in text_questions]
        all_questions.extend([(q, 'image') for q in image_questions])
        all_questions.sort(key=lambda x: x[0]['confidence'], reverse=True)
        
        for question, source in all_questions:
            # Check position overlap with existing questions
            pos = question['bbox']
            overlaps = False
            
            for used_pos in used_positions:
                if self._check_overlap(pos, used_pos):
                    overlaps = True
                    break
            
            if not overlaps:
                # Adjust confidence based on page analysis
                if source == 'text':
                    confidence = question['confidence'] * (1 + analysis.text_percentage)
                else:
                    confidence = question['confidence'] * (1 + analysis.image_percentage)
                
                question['confidence'] = min(confidence, 1.0)
                merged.append(question)
                used_positions.add(pos)
        
        return merged

    def _extract_question_from_text(self, block: Dict) -> Optional[Dict]:
        """Extract question information from text block"""
        text = " ".join([span["text"] for line in block["lines"] 
                        for span in line["spans"]])
        
        # Question detection logic here
        # Returns None if no question found
        pass

    def _extract_questions_from_ocr(self, ocr_data: Dict) -> List[Dict]:
        """Extract questions from OCR results"""
        questions = []
        
        # Process OCR data to find questions
        # Group text by lines and analyze patterns
        pass

    @staticmethod
    def _check_overlap(bbox1: Tuple, bbox2: Tuple, threshold: float = 0.5) -> bool:
        """Check if two bounding boxes overlap significantly"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return False
            
        overlap_area = (x2 - x1) * (y2 - y1)
        bbox1_area = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        bbox2_area = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        
        return overlap_area > threshold * min(bbox1_area, bbox2_area)

    def _calculate_image_coverage(
        self,
        page: fitz.Page,
        image_list: List
    ) -> float:
        """Calculate how much of the page is covered by images"""
        try:
            page_area = page.rect.width * page.rect.height
            image_area = 0
            
            for img in image_list:
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                image_area += pix.width * pix.height
                pix = None
            
            return image_area / page_area
            
        except Exception as e:
            logger.error(f"Error calculating image coverage: {str(e)}")
            return 0.0

    def _check_if_scanned(self, page: fitz.Page, image_list: List) -> bool:
        """Determine if page is likely a scanned document"""
        try:
            if not image_list:
                return False
                
            # Check for full-page images
            page_area = page.rect.width * page.rect.height
            
            for img in image_list:
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                # If image covers most of page and is grayscale/RGB
                if (pix.width * pix.height > 0.9 * page_area and
                    pix.n in (1, 3)):  # Grayscale or RGB
                    return True
                    
                pix = None
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if scanned: {str(e)}")
            return False

    def _calculate_dpi(self, page: fitz.Page) -> Optional[float]:
        """Calculate effective DPI of page images"""
        try:
            # Get page dimensions in points (1/72 inch)
            page_width_pt = page.rect.width
            page_height_pt = page.rect.height
            
            # Get image dimensions
            image_list = page.get_images()
            if not image_list:
                return None
                
            max_dpi = 0
            for img in image_list:
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                # Calculate DPI based on image dimensions
                width_dpi = pix.width / (page_width_pt / 72)
                height_dpi = pix.height / (page_height_pt / 72)
                max_dpi = max(max_dpi, max(width_dpi, height_dpi))
                
                pix = None
            
            return max_dpi
            
        except Exception as e:
            logger.error(f"Error calculating DPI: {str(e)}")
            return None

# Flask application setup
from flask import Flask, request, jsonify
import base64

app = Flask(__name__)

@app.route('/process_submission', methods=['POST'])
def process_submission():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    
    try:
        # Save file temporarily
        temp_path = 'temp_submission.pdf'
        file.save(temp_path)
        
        # Process document
        processor = HybridPDFProcessor()
        questions_by_page = processor.process_document(temp_path)
        
        # Convert results to JSON-serializable format
        results = {}
        for page_num, questions in questions_by_page.items():
            results[str(page_num)] = [
                {
                    'question_number': q.question_number,
                    'question_bbox': q.question_bbox,
                    'answer_bbox': q.answer_bbox,
                    'pixmap': base64.b64encode(q.pixmap).decode('utf-8') 
                        if q.pixmap else None,
                    'confidence': q.confidence
                }
                for q in questions
            ]
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)