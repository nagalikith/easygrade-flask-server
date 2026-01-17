import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import py_lib.vision_ocr as vision_ocr

DEFAULT_TEMPLATE_NAME = "__answer_template.json"
DEFAULT_INDEX_NAME = "answers.json"

logger = logging.getLogger(__name__)

# Template format: {"boxes": [{"page": 1, "question_num": 1, "bbox": [x1, y1, x2, y2]}]}


def load_template_boxes(assignment_dir: str,
                        template_name: str = DEFAULT_TEMPLATE_NAME
                        ) -> Optional[List[Dict]]:
    template_path = os.path.join(assignment_dir, template_name)
    if not os.path.exists(template_path):
        return None

    try:
        with open(template_path, "r") as handle:
            data = json.load(handle)
    except Exception as exc:
        logger.error("Failed reading template boxes: %s", exc)
        return None

    boxes = data.get("boxes", data)
    normalized = []
    for entry in boxes if isinstance(boxes, list) else []:
        if "bbox" not in entry:
            continue
        question_num = int(entry.get("question_num", entry.get("question", 0))) or None
        normalized.append({
            "page": int(entry.get("page", 1)),
            "question_num": question_num,
            "bbox": entry["bbox"]
        })
    return normalized or None


def extract_submission_answers(submission_path: str,
                               output_dir: str,
                               template_boxes: Optional[List[Dict]] = None,
                               dpi: int = 200,
                               ocr_enabled: bool = True,
                               ocr_lang: str = "eng") -> Dict:
    os.makedirs(output_dir, exist_ok=True)
    pages = _load_pages(submission_path, dpi=dpi)
    answers = []
    question_counter = 1
    ocr_error = None

    for page_num, image in enumerate(pages, start=1):
        page_boxes = _get_page_boxes(template_boxes, page_num)
        if page_boxes:
            for entry in page_boxes:
                question_num = entry.get("question_num") or question_counter
                question_counter = max(question_counter, question_num + 1)
                bbox = _scale_bbox(entry["bbox"], image.shape)
                saved, crop = _save_answer_crop(
                    image, bbox, output_dir, question_num, page_num)
                if saved and crop is not None:
                    ocr_text, ocr_conf, ocr_err = _extract_ocr_text(
                        crop, ocr_lang, ocr_enabled)
                    ocr_error = ocr_error or ocr_err
                    answers.append({
                        "question_num": question_num,
                        "page": page_num,
                        "bbox": bbox,
                        "path": saved,
                        "source": "template",
                        "ocr_text": ocr_text,
                        "ocr_confidence": ocr_conf,
                        "ocr_error": ocr_err
                    })
            continue

        boxes = _detect_boxes(image)
        for bbox in _sort_boxes(boxes):
            saved, crop = _save_answer_crop(
                image, bbox, output_dir, question_counter, page_num)
            if saved and crop is not None:
                ocr_text, ocr_conf, ocr_err = _extract_ocr_text(
                    crop, ocr_lang, ocr_enabled)
                ocr_error = ocr_error or ocr_err
                answers.append({
                    "question_num": question_counter,
                    "page": page_num,
                    "bbox": bbox,
                    "path": saved,
                    "source": "auto",
                    "ocr_text": ocr_text,
                    "ocr_confidence": ocr_conf,
                    "ocr_error": ocr_err
                })
            question_counter += 1

    index = {
        "source_file": os.path.basename(submission_path),
        "answers": answers,
        "ocr_enabled": ocr_enabled,
        "ocr_lang": ocr_lang,
        "ocr_error": ocr_error
    }
    _write_index(output_dir, index)
    return index


def _write_index(output_dir: str, index: Dict) -> None:
    index_path = os.path.join(output_dir, DEFAULT_INDEX_NAME)
    with open(index_path, "w") as handle:
        json.dump(index, handle)


def _get_page_boxes(template_boxes: Optional[List[Dict]],
                    page_num: int) -> List[Dict]:
    if not template_boxes:
        return []
    return [entry for entry in template_boxes if entry.get("page") == page_num]


def _load_pages(submission_path: str, dpi: int = 200) -> List:
    ext = os.path.splitext(submission_path)[1].lower()
    if ext == ".pdf":
        return _load_pdf_pages(submission_path, dpi)
    return _load_image_pages(submission_path)


def _load_pdf_pages(submission_path: str, dpi: int) -> List:
    import fitz
    import numpy as np
    import cv2

    doc = fitz.open(submission_path)
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8)
        img = img.reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        pages.append(img)
    doc.close()
    return pages


def _load_image_pages(submission_path: str) -> List:
    import cv2

    image = cv2.imread(submission_path)
    if image is None:
        raise ValueError(f"Unable to read image: {submission_path}")
    return [image]


def _scale_bbox(bbox: List[float], image_shape: Tuple[int, int, int]) -> List[int]:
    height, width = image_shape[:2]
    max_coord = max(bbox)
    if max_coord <= 1.0:
        x1 = int(bbox[0] * width)
        y1 = int(bbox[1] * height)
        x2 = int(bbox[2] * width)
        y2 = int(bbox[3] * height)
    else:
        x1, y1, x2, y2 = map(int, bbox)
    return _clamp_bbox([x1, y1, x2, y2], width, height)


def _clamp_bbox(bbox: List[int], width: int, height: int) -> List[int]:
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, width - 1))
    x2 = max(0, min(x2, width - 1))
    y1 = max(0, min(y1, height - 1))
    y2 = max(0, min(y2, height - 1))
    if x2 <= x1:
        x2 = min(width - 1, x1 + 1)
    if y2 <= y1:
        y2 = min(height - 1, y1 + 1)
    return [x1, y1, x2, y2]


def _save_answer_crop(image, bbox: List[int], output_dir: str,
                      question_num: int, page_num: int):
    import cv2

    x1, y1, x2, y2 = bbox
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return None, None
    filename = f"answer_{question_num}_p{page_num}.png"
    out_path = os.path.join(output_dir, filename)
    cv2.imwrite(out_path, crop)
    return filename, crop


def _detect_boxes(image) -> List[List[int]]:
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, edge_kernel, iterations=1)

    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 21, 15)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.bitwise_or(thresh, edges)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = gray.shape
    page_area = height * width
    min_area = page_area * 0.001
    max_area = page_area * 0.9
    min_side = max(15, int(min(height, width) * 0.015))
    boxes = []
    for cnt in contours:
        contour_area = cv2.contourArea(cnt)
        if contour_area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        rect_area = w * h
        if rect_area <= 0:
            continue
        if rect_area > max_area:
            continue
        if w < min_side or h < min_side:
            continue
        aspect = w / float(h)
        if aspect < 0.15 or aspect > 12.0:
            continue
        extent = contour_area / float(rect_area)
        if extent < 0.05:
            continue
        boxes.append([x, y, x + w, y + h])

    return _merge_overlaps(boxes)


def _merge_overlaps(boxes: List[List[int]]) -> List[List[int]]:
    merged = []
    for box in sorted(boxes, key=lambda b: (b[1], b[0])):
        added = False
        for idx, existing in enumerate(merged):
            if _iou(box, existing) > 0.3 or _contains(box, existing) or _contains(existing, box):
                merged[idx] = [
                    min(existing[0], box[0]),
                    min(existing[1], box[1]),
                    max(existing[2], box[2]),
                    max(existing[3], box[3])
                ]
                added = True
                break
        if not added:
            merged.append(box)
    return merged


def _iou(box_a: List[int], box_b: List[int]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return inter / float(area_a + area_b - inter)


def _contains(box_a: List[int], box_b: List[int]) -> bool:
    return (
        box_a[0] <= box_b[0]
        and box_a[1] <= box_b[1]
        and box_a[2] >= box_b[2]
        and box_a[3] >= box_b[3]
    )


def _sort_boxes(boxes: List[List[int]]) -> List[List[int]]:
    return sorted(boxes, key=lambda b: (b[1], b[0]))


def _extract_ocr_text(image, lang: str, enabled: bool):
    if not enabled:
        return "", None, None
    return vision_ocr.extract_text(image, lang)
