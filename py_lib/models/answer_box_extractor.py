import cv2
import numpy as np
import torch
from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image
import json
from pathlib import Path
import boto3
import io

class AnswerSheetProcessor:
    def __init__(self):
        # Initialize DETR model for object detection
        self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        self.model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
        
        # S3 configuration
        self.s3_client = boto3.client('s3',
            aws_access_key_id='YOUR_ACCESS_KEY',
            aws_secret_access_key='YOUR_SECRET_KEY',
            region_name='YOUR_REGION'
        )
        self.bucket_name = 'your-bucket-name'
        
        # Define standard sizes for answer boxes
        self.TARGET_HEIGHT = 800
        self.TARGET_WIDTH = 600
        
        # Configure answer box detection parameters
        self.MIN_BOX_AREA = 50000  # Minimum area for valid answer box
        self.OVERLAP_THRESHOLD = 0.5  # IoU threshold for box merging

    def preprocess_image(self, image):
        """Preprocess image for better box detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Remove noise
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPHOLOGYEX_CLOSE, kernel)
        
        return thresh

    def detect_answer_boxes(self, image_path):
        """Detect answer boxes using DETR model"""
        # Load and preprocess image
        image = Image.open(image_path)
        inputs = self.processor(images=image, return_tensors="pt")
        
        # Get predictions
        outputs = self.model(**inputs)
        
        # Convert outputs to normalized boxes
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=0.7
        )[0]
        
        # Convert to list of boxes
        boxes = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(i, 2) for i in box.tolist()]
            # Only keep boxes labeled as "text" or with high confidence
            if score > 0.7 and (label == 76 or label == 1):  # DETR labels for text/box
                boxes.append(box)
        
        return self.merge_overlapping_boxes(boxes)

    def merge_overlapping_boxes(self, boxes):
        """Merge overlapping bounding boxes"""
        if not boxes:
            return []
            
        def calculate_iou(box1, box2):
            # Calculate intersection over union
            x1 = max(box1[0], box2[0])
            y1 = max(box1[1], box2[1])
            x2 = min(box1[2], box2[2])
            y2 = min(box1[3], box2[3])
            
            if x2 < x1 or y2 < y1:
                return 0.0
                
            intersection = (x2 - x1) * (y2 - y1)
            area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
            area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
            union = area1 + area2 - intersection
            
            return intersection / union if union > 0 else 0.0
        
        # Sort boxes by y-coordinate
        boxes = sorted(boxes, key=lambda x: x[1])
        merged_boxes = []
        current_box = boxes[0]
        
        for next_box in boxes[1:]:
            iou = calculate_iou(current_box, next_box)
            
            if iou > self.OVERLAP_THRESHOLD:
                # Merge boxes
                current_box = [
                    min(current_box[0], next_box[0]),
                    min(current_box[1], next_box[1]),
                    max(current_box[2], next_box[2]),
                    max(current_box[3], next_box[3])
                ]
            else:
                merged_boxes.append(current_box)
                current_box = next_box
        
        merged_boxes.append(current_box)
        return merged_boxes

    def extract_and_resize_answers(self, image_path):
        """Extract and resize individual answer sections"""
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError("Could not read image")
            
        # Get answer boxes
        boxes = self.detect_answer_boxes(image_path)
        
        # Sort boxes by y-coordinate (top to bottom)
        boxes = sorted(boxes, key=lambda x: x[1])
        
        # Extract and process each answer section
        processed_answers = []
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            
            # Extract answer section
            answer_section = image[y1:y2, x1:x2]
            
            # Calculate aspect ratio
            aspect_ratio = (x2 - x1) / (y2 - y1)
            
            # Determine new dimensions maintaining aspect ratio
            if aspect_ratio > (self.TARGET_WIDTH / self.TARGET_HEIGHT):
                new_width = self.TARGET_WIDTH
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = self.TARGET_HEIGHT
                new_width = int(new_height * aspect_ratio)
            
            # Resize answer section
            resized_answer = cv2.resize(answer_section, (new_width, new_height))
            
            # Add white padding to reach target size
            padded_answer = np.ones((self.TARGET_HEIGHT, self.TARGET_WIDTH, 3), 
                                  dtype=np.uint8) * 255
            y_offset = (self.TARGET_HEIGHT - new_height) // 2
            x_offset = (self.TARGET_WIDTH - new_width) // 2
            padded_answer[y_offset:y_offset+new_height, 
                         x_offset:x_offset+new_width] = resized_answer
            
            processed_answers.append({
                'answer_number': i + 1,
                'image': padded_answer,
                'original_bbox': box
            })
        
        return processed_answers

    def save_to_s3(self, processed_answers, student_id, submission_id):
        """Save processed answers to S3"""
        results = []
        
        for answer in processed_answers:
            # Convert image to bytes
            success, encoded_image = cv2.imencode('.png', answer['image'])
            if not success:
                continue
                
            image_bytes = io.BytesIO(encoded_image.tobytes())
            
            # Generate S3 key
            s3_key = f'processed_answers/{student_id}/{submission_id}/answer_{answer["answer_number"]}.png'
            
            # Upload to S3
            try:
                self.s3_client.upload_fileobj(
                    image_bytes, 
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': 'image/png'}
                )
                
                results.append({
                    'answer_number': answer['answer_number'],
                    's3_key': s3_key,
                    'original_bbox': answer['original_bbox']
                })
                
            except Exception as e:
                print(f"Error uploading answer {answer['answer_number']}: {str(e)}")
        
        return results

    def process_submission(self, image_path, student_id, submission_id):
        """Process a complete submission"""
        try:
            # Extract and resize answers
            processed_answers = self.extract_and_resize_answers(image_path)
            
            # Save to S3 and get results
            results = self.save_to_s3(processed_answers, student_id, submission_id)
            
            return {
                'status': 'success',
                'student_id': student_id,
                'submission_id': submission_id,
                'num_answers': len(results),
                'answers': results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'student_id': student_id,
                'submission_id': submission_id
            }