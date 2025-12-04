"""Feature Engineering for PDF Blocks.

Takes raw line-level blocks from pdf_parser.parse_pdf and enriches them with
useful features for heading detection:
- font_rank, relative_size
- bold/italic flags
- text stats (word_count, char_count, is_short)
- casing patterns (ALL CAPS, Title Case)
- numbering patterns (1., 1.1, 2.3.4, etc.)
- simple position features (left-aligned, centered, width ratio)
"""

from typing import List, Dict
from collections import Counter
import re

# Assume standard PDF width for now; can later infer from page if needed
PAGE_WIDTH = 612  # points, typical US Letter width


def enrich_blocks_with_features(blocks: List[Dict]) -> List[Dict]:
    """Adds a 'features' dict to each block for heading detection.

    Computes font-based, text-based, and position-based features that help
    distinguish headings from body text. Features include font rank, relative size,
    boldness, numbering patterns, casing, and indentation.

    Args:
        blocks (List[Dict]): raw blocks from PDF parser.
    Returns:
        List[Dict]: enriched blocks with 'features' dict containing:
            - font_features: font_rank, relative_size, is_bold, is_italic
            - text_features: word_count, casing patterns, numbering, etc.
            - position_features: alignment, indentation, text width
    """
    if not blocks:
        return blocks

    # 1) Compute per-page font statistics
    page_stats = _compute_page_font_stats(blocks)

    # 2) Enrich each block with features
    enriched = []
    for block in blocks:
        page = block["page"]
        stats = page_stats.get(page, {})

        font_features = _font_features(block, stats)
        text_features = _text_features(block)
        position_features = _position_features(block)

        features = {
            **font_features,
            **text_features,
            **position_features,
        }

        block["features"] = features
        enriched.append(block)

    return enriched


# ---------- internal helpers ----------

def _compute_page_font_stats(blocks: List[Dict]) -> Dict[int, Dict]:
    """For each page, compute:
    - list of all font sizes
    - body_text_size (most common)
    - unique_sizes sorted desc for rank calculation
    """
    page_fonts: Dict[int, List[float]] = {}

    for b in blocks:
        page = b["page"]
        size = b.get("font_size")
        if size is None:
            continue
        page_fonts.setdefault(page, []).append(size)

    page_stats: Dict[int, Dict] = {}
    for page, sizes in page_fonts.items():
        if not sizes:
            continue
        size_counter = Counter(sizes)
        body_text_size, _ = size_counter.most_common(1)[0]
        unique_sizes = sorted(set(sizes), reverse=True)
        page_stats[page] = {
            "body_text_size": float(body_text_size),
            "unique_sizes": unique_sizes,
        }

    return page_stats


def _font_features(block: Dict, stats: Dict) -> Dict:
    font_size = float(block.get("font_size", 0.0))
    is_bold = bool(block.get("is_bold", False))
    is_italic = bool(block.get("is_italic", False))
    font_family = str(block.get("font_family", "")).lower()

    body_size = stats.get("body_text_size", font_size or 1.0)
    unique_sizes = stats.get("unique_sizes", [font_size])

    # font_rank: 1 = largest size on the page
    try:
        font_rank = unique_sizes.index(font_size) + 1
    except ValueError:
        font_rank = len(unique_sizes)

    # relative size vs body text
    relative_size = font_size / body_size if body_size > 0 else 1.0
    
    # Enhanced bold detection: check font_family for weight indicators
    # Many PDFs encode bold in font name rather than flag
    enhanced_bold = is_bold or ("bold" in font_family or "heavy" in font_family or "black" in font_family)

    return {
        "font_rank": font_rank,
        "relative_size": round(relative_size, 2),
        "is_bold": enhanced_bold,
        "is_italic": is_italic,
        "font_family": font_family,
    }


# regex patterns for numbering
NUMBERED_RE = re.compile(r"^\d+\.\s*")          # "1. ", "2. "
MULTI_LEVEL_RE = re.compile(r"^\d+(\.\d+)+\s*") # "1.1 ", "2.3.4 "
ROMAN_RE = re.compile(r"^(?=[IVXLCDM]+\.)[IVXLCDM]+\.\s*", re.IGNORECASE)
LETTER_RE = re.compile(r"^[A-Z]\.\s*")

def _text_features(block: Dict) -> Dict:
    text: str = block.get("text", "").strip()
    words = text.split()
    word_count = len(words)
    char_count = len(text)

    is_all_caps = text.isupper() and char_count > 3
    is_title_case = text.istitle()
    
    # Count uppercase letters for better casing detection
    uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

    numbering_pattern = "none"
    has_numbering = False

    if MULTI_LEVEL_RE.match(text):
        numbering_pattern = "multi_level"
        has_numbering = True
    elif NUMBERED_RE.match(text):
        numbering_pattern = "numbered"
        has_numbering = True
    elif ROMAN_RE.match(text):
        numbering_pattern = "roman"
        has_numbering = True
    elif LETTER_RE.match(text):
        numbering_pattern = "lettered"
        has_numbering = True

    is_short = word_count < 10
    is_very_short = word_count < 6  # Additional feature for very short headings

    return {
        "word_count": word_count,
        "char_count": char_count,
        "is_short": is_short,
        "is_very_short": is_very_short,
        "is_all_caps": is_all_caps,
        "is_title_case": is_title_case,
        "uppercase_ratio": round(uppercase_ratio, 2),
        "has_numbering": has_numbering,
        "numbering_pattern": numbering_pattern,
    }


def _position_features(block: Dict) -> Dict:
    bbox = block.get("bbox", {}) or {}
    x0 = float(bbox.get("x0", 0.0))
    x1 = float(bbox.get("x1", 0.0))

    text_width = max(x1 - x0, 1.0)
    text_width_ratio = round(text_width / PAGE_WIDTH, 3)

    center_x = (x0 + x1) / 2.0
    page_center = PAGE_WIDTH / 2.0

    # Improved thresholds based on typical PDF layouts
    left_margin = 50   # Standard left margin
    is_left_aligned = x0 < left_margin + 20
    is_centered = abs(center_x - page_center) < 75
    is_indented = x0 > left_margin + 30  # Indented text (often subsections)
    indent_level = max(0, int((x0 - left_margin) / 30))  # Estimate indent depth

    return {
        "text_width_ratio": text_width_ratio,
        "is_left_aligned": is_left_aligned,
        "is_centered": is_centered,
        "is_indented": is_indented,
        "indent_level": indent_level,
        "left_margin": round(x0, 2),
    }


# --- quick manual test ---
if __name__ == "__main__":
    # Example: run on a few parsed blocks (requires pdf_parser to work and a sample PDF)
    from src.core.pdf_parser import parse_pdf

    sample_pdf = "tests/sample_pdfs/simple_doc.pdf"
    parsed_blocks = parse_pdf(sample_pdf)
    enriched_blocks = enrich_blocks_with_features(parsed_blocks)

    for b in enriched_blocks[:5]:
        print(b["text"])
        print("  features:", b["features"])
