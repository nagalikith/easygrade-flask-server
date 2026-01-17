import json
import os
import sys
import tempfile
import unittest

import cv2
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from py_lib.answer_extractor import (  # noqa: E402
    DEFAULT_INDEX_NAME,
    extract_submission_answers,
    load_template_boxes,
)


class AnswerExtractorTests(unittest.TestCase):
    def _make_test_image(self, path: str) -> None:
        image = np.full((800, 600, 3), 255, dtype=np.uint8)
        cv2.rectangle(image, (50, 50), (550, 200), (0, 0, 0), thickness=-1)
        cv2.rectangle(image, (50, 300), (550, 450), (0, 0, 0), thickness=-1)
        cv2.imwrite(path, image)

    def test_extracts_answers_from_image(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, "submission.png")
            out_dir = os.path.join(tmpdir, "answers")
            self._make_test_image(image_path)

            index = extract_submission_answers(image_path, out_dir)
            self.assertGreaterEqual(len(index["answers"]), 2)

            index_path = os.path.join(out_dir, DEFAULT_INDEX_NAME)
            self.assertTrue(os.path.exists(index_path))

            for answer in index["answers"]:
                answer_path = os.path.join(out_dir, answer["path"])
                self.assertTrue(os.path.exists(answer_path))
                self.assertIn("ocr_text", answer)
                self.assertIn("ocr_confidence", answer)
                self.assertIn("ocr_error", answer)

    def test_template_boxes_override_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assignment_dir = os.path.join(tmpdir, "assignment")
            os.makedirs(assignment_dir, exist_ok=True)
            image_path = os.path.join(tmpdir, "submission.png")
            out_dir = os.path.join(tmpdir, "answers")
            self._make_test_image(image_path)

            template = {
                "boxes": [
                    {"page": 1, "question_num": 3, "bbox": [0.08, 0.06, 0.92, 0.26]},
                    {"page": 1, "question_num": 7, "bbox": [0.08, 0.36, 0.92, 0.56]},
                ]
            }
            template_path = os.path.join(assignment_dir, "__answer_template.json")
            with open(template_path, "w") as handle:
                json.dump(template, handle)

            template_boxes = load_template_boxes(assignment_dir)
            index = extract_submission_answers(
                image_path, out_dir, template_boxes=template_boxes)

            question_nums = {answer["question_num"] for answer in index["answers"]}
            self.assertEqual(question_nums, {3, 7})
            self.assertTrue(all(
                answer["source"] == "template" for answer in index["answers"]
            ))
            for answer in index["answers"]:
                self.assertIn("ocr_text", answer)

    def test_extracts_answers_from_pdf(self):
        import fitz

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "submission.pdf")
            out_dir = os.path.join(tmpdir, "answers")

            doc = fitz.open()
            page = doc.new_page(width=600, height=800)
            page.draw_rect(fitz.Rect(50, 50, 550, 200), color=(0, 0, 0), fill=(0, 0, 0))
            page.draw_rect(fitz.Rect(50, 300, 550, 450), color=(0, 0, 0), fill=(0, 0, 0))
            doc.save(pdf_path)
            doc.close()

            index = extract_submission_answers(pdf_path, out_dir)
            self.assertGreaterEqual(len(index["answers"]), 2)
            for answer in index["answers"]:
                answer_path = os.path.join(out_dir, answer["path"])
                self.assertTrue(os.path.exists(answer_path))
                self.assertIn("ocr_text", answer)


if __name__ == "__main__":
    unittest.main()
