import pytest
from ocr_engine import preprocess_frame
import numpy as np
import cv2

def test_preprocess_frame():
    # Create a dummy black image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    processed = preprocess_frame(img)
    
    # Check if grayscale (2 dimensions)
    assert len(processed.shape) == 2
    # Check if binary (values are 0 or 255) - roughly
    unique_vals = np.unique(processed)
    assert len(unique_vals) <= 2

def test_dedup_logic():
    # Mock logic for Levenshtein
    from Levenshtein import ratio
    str1 = "Hello World"
    str2 = "Hello Worl" # slightly noisy OCR
    sim = ratio(str1, str2)
    assert sim > 0.8