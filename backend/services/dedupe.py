from typing import List, Dict, Tuple, Optional
from PIL import Image

def compute_perceptual_hash(image: Image.Image) -> str:
    """
    Computes a 64-bit Difference Hash (dHash) for a PIL Image.
    Grayscales image, resizes to 9x8, and compares adjacent pixels.
    Returns a 16-character hex string.
    """
    # 1. Convert to grayscale and resize to 9x8
    resized = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(resized.get_flattened_data()) if hasattr(resized, 'get_flattened_data') else list(resized.getdata())
    
    # 2. Compute pixel difference row by row
    difference = []
    for row in range(8):
        for col in range(8):
            pixel_left = pixels[row * 9 + col]
            pixel_right = pixels[row * 9 + col + 1]
            difference.append(pixel_left > pixel_right)
            
    # 3. Convert 64 booleans to a 64-bit integer hex string
    decimal_val = 0
    for idx, value in enumerate(difference):
        if value:
            decimal_val |= (1 << (63 - idx))
            
    return f"{decimal_val:016x}"

def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculates Hamming distance (bit difference count) between two 16-char hex hashes."""
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count('1')
    except (ValueError, TypeError):
        return 64

def check_duplicate(current_hash: str, existing_records: List[Dict], threshold: int = 5) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Compares current_hash against existing records.
    Returns (is_duplicate, matching_doc_id, hamming_distance).
    """
    if not current_hash:
        return False, None, None
        
    for record in existing_records:
        ex_hash = record.get("perceptual_hash")
        doc_id = record.get("id")
        if ex_hash and doc_id:
            dist = hamming_distance(current_hash, ex_hash)
            if dist <= threshold:
                return True, str(doc_id), dist
                
    return False, None, None
