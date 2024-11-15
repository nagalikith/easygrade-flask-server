import cv2
import numpy as np
import torch
from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image
import json
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
import yaml
import logging

class BaseDetector(ABC):
    """Abstract base class for different detection models"""
    @abstractmethod
    def detect_boxes(self, image: np.ndarray) -> List[List[float]]:
        pass

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Common preprocessing steps for all detectors"""
        # Normalize image size
        height, width = image.shape[:2]
        max_dimension = 1024
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_size = (int(width * scale), int(height * scale))
            image = cv2.resize(image, new_size)
        
        # Enhance contrast
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced

class DetrDetector(BaseDetector):
    def __init__(self, model_name: str = "facebook/detr-resnet-50"):
        super().__init__()
        self.processor = DetrImageProcessor.from_pretrained(model_name)
        self.model = DetrForObjectDetection.from_pretrained(model_name)
        self.confidence_threshold = 0.7
        # Labels for answer boxes - adjust based on your specific model's label mapping
        self.target_labels = {1, 76}  # Example labels for boxes/rectangles
        
    def detect_boxes(self, image: np.ndarray) -> List[List[float]]:
        # Preprocess image
        image = self.preprocess_image(image)
        image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Model inference
        inputs = self.processor(images=image_pil, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Post-process results
        target_sizes = torch.tensor([image_pil.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=self.confidence_threshold
        )[0]
        
        # Filter and format results
        boxes = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            if score > self.confidence_threshold and label.item() in self.target_labels:
                # Convert box coordinates to integers for practical use
                box_coords = [int(i) for i in box.tolist()]
                # Add box if it meets minimum size requirements
                width = box_coords[2] - box_coords[0]
                height = box_coords[3] - box_coords[1]
                if width * height > 1000:  # Minimum area threshold
                    boxes.append(box_coords)
        
        return boxes

class AnswerSheetProcessor:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.detector = self._initialize_detector()
        self._setup_output_directory()
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with more detailed formatting"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('answer_processor.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def process_submission(self, image_path: str, student_id: str, 
                         submission_id: str, save_visualization: bool = False) -> Dict:
        """Process a complete submission with enhanced error handling and validation"""
        try:
            # Input validation
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Load and validate image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image: {image_path}")
            
            # Record original image dimensions
            original_height, original_width = image.shape[:2]
            self.logger.info(f"Processing image of size {original_width}x{original_height}")
            
            # Detect answer boxes
            boxes = self.detector.detect_boxes(image)
            if not boxes:
                self.logger.warning(f"No answer boxes detected in {image_path}")
                return {
                    'status': 'warning',
                    'message': 'No answer boxes detected',
                    'student_id': student_id,
                    'submission_id': submission_id,
                    'num_answers': 0,
                    'answers': []
                }
            
            # Process detected boxes
            processed_answers = self._process_answer_boxes(image, boxes, student_id, submission_id)
            
            # Generate visualization if requested
            if save_visualization:
                self._save_visualization(image, boxes, student_id, submission_id)
            
            return {
                'status': 'success',
                'student_id': student_id,
                'submission_id': submission_id,
                'num_answers': len(processed_answers),
                'answers': processed_answers,
                'original_dimensions': {
                    'width': original_width,
                    'height': original_height
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing submission: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'student_id': student_id,
                'submission_id': submission_id
            }
    
    def _process_answer_boxes(self, image: np.ndarray, boxes: List[List[float]], 
                            student_id: str, submission_id: str) -> List[Dict]:
        """Process individual answer boxes with enhanced validation and normalization"""
        processed_answers = []
        
        # Sort boxes by vertical position (top to bottom)
        boxes = sorted(boxes, key=lambda x: x[1])
        
        for i, box in enumerate(boxes):
            try:
                x1, y1, x2, y2 = map(int, box)
                # Validate box coordinates
                if x1 >= x2 or y1 >= y2:
                    self.logger.warning(f"Invalid box coordinates: {box}")
                    continue
                
                # Extract and process answer section
                answer_section = image[y1:y2, x1:x2]
                processed_answer = self._process_single_answer(
                    answer_section, i, student_id, submission_id)
                
                if processed_answer:
                    processed_answers.append(processed_answer)
                    
            except Exception as e:
                self.logger.error(f"Error processing answer box {i}: {str(e)}")
                continue
        
        return processed_answers