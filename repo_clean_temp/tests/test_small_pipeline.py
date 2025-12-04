"""Small pipeline test for pdf-topic-scanner.

This test should remain lightweight and use stubs/mocks. It ensures the
pipeline pieces integrate at a basic level.

Test coverage:
- Feature engineering: extraction and enrichment
- Hierarchy building: section nesting and tree construction

"""
import os
import json

from src.features.feature_engineer import enrich_blocks_with_features
from src.hierarchy.tree_builder import build_hierarchy


def test_pipeline_smoke():
    """Basic smoke test that exercises core pipeline."""
    # Test feature engineering
    test_blocks = [
        {
            "text": "Chapter 1: Introduction",
            "page": 1,
            "font_size": 18.0,
            "font_family": "Arial-Bold",
            "is_bold": True,
            "is_italic": False,
            "bbox": {"x0": 50, "y0": 100, "x1": 400, "y1": 120},
        },
        {
            "text": "This is a short document with some content.",
            "page": 1,
            "font_size": 12.0,
            "font_family": "Arial",
            "is_bold": False,
            "is_italic": False,
            "bbox": {"x0": 50, "y0": 140, "x1": 550, "y1": 160},
        },
    ]

    # Enrich blocks with features
    enriched = enrich_blocks_with_features(test_blocks)
    assert len(enriched) == 2
    assert "features" in enriched[0]
    assert "word_count" in enriched[0]["features"]

    # Test hierarchy building
    classified_blocks = [
        {**enriched[0], "classification": "H1"},
        {**enriched[1], "classification": "BODY"},
    ]
    metadata = {"source_file": "test.pdf", "total_blocks": 2, "total_pages": 1}
    hierarchy = build_hierarchy(classified_blocks, metadata)
    assert "sections" in hierarchy
    assert len(hierarchy["sections"]) > 0
    assert hierarchy["sections"][0]["title"] == "Chapter 1: Introduction"
