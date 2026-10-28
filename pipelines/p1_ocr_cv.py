"""P1  OCR + classical CV.

OCR (PP-OCRv6 small via RapidOCR) -> OpenCV: ink left after erasing the words, shaped like a pen loop
-> erase those strokes and OCR again -> words inside each loop -> mapper.
"""
import cv2

from pipelines.common import mapper, marks_cv, ocr


def run(task):
    path = task["image_path"]
    first = ocr.read(path)
    cands = marks_cv.candidates(path, first)
    shape = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE).shape
    page = ocr.best_reading(ocr.read_without(path, marks_cv.stroke_mask(shape, cands)), first) if cands else first
    return mapper.answer(task, page, marks_cv.circled_groups(page, cands))
