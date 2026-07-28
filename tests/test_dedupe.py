import pytest
from PIL import Image, ImageDraw
from backend.services.dedupe import compute_perceptual_hash, hamming_distance, check_duplicate

def create_sample_image(bg_color=(255, 255, 255), line_rect=(0, 0, 100, 200)):
    img = Image.new("RGB", (200, 200), color=bg_color)
    draw = ImageDraw.Draw(img)
    draw.rectangle(line_rect, fill=(0, 0, 0))
    return img

def test_compute_perceptual_hash():
    img1 = create_sample_image(line_rect=(0, 0, 100, 200))
    hash1 = compute_perceptual_hash(img1)
    
    assert isinstance(hash1, str)
    assert len(hash1) == 16  # 64-bit hex hash

def test_identical_image_hash_matching():
    img1 = create_sample_image(line_rect=(10, 10, 150, 150))
    img2 = create_sample_image(line_rect=(10, 10, 150, 150))
    
    hash1 = compute_perceptual_hash(img1)
    hash2 = compute_perceptual_hash(img2)
    
    assert hash1 == hash2
    assert hamming_distance(hash1, hash2) == 0

def test_check_duplicate_positive():
    img = create_sample_image(line_rect=(20, 20, 180, 180))
    hash1 = compute_perceptual_hash(img)
    
    existing = [
        {"id": "doc-abc-123", "perceptual_hash": hash1}
    ]
    
    is_dup, match_id, dist = check_duplicate(hash1, existing, threshold=5)
    assert is_dup is True
    assert match_id == "doc-abc-123"
    assert dist == 0

def test_check_duplicate_negative():
    # Vertical split vs Horizontal split images produce distinct hashes
    img1 = create_sample_image(line_rect=(0, 0, 100, 200))   # Left half black
    img2 = create_sample_image(line_rect=(0, 0, 200, 100))   # Top half black
    
    hash1 = compute_perceptual_hash(img1)
    hash2 = compute_perceptual_hash(img2)
    
    existing = [
        {"id": "doc-diff-999", "perceptual_hash": hash2}
    ]
    
    is_dup, match_id, dist = check_duplicate(hash1, existing, threshold=5)
    assert is_dup is False
    assert hamming_distance(hash1, hash2) > 5
