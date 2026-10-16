"""
MediPaw Multi-Modal ViT — Backend Integration API.

Public interface for the MediPaw backend adapters:

    from multimodal_vit.multimodal_api import fuse_model_results

    fused = fuse_model_results(list_of_model_result_dicts)
"""

from __future__ import annotations
import os
import sys
from typing import Any, Dict, List, Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from inference import run_fusion, collect_features_from_results


def fuse_model_results(
    model_results: List[Dict[str, Any]],
    model_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fuses available CNN feature embeddings via the Multi-Modal ViT.

    Args:
        model_results: List of standardized model result dicts from MediPaw adapters.
                       Results that include a 'feature_vector' key (len 576) participate in fusion.
        model_path:    Optional custom path to ViT checkpoint.

    Returns:
        JSON-serializable dict with fusion output.
    """
    feature_list = collect_features_from_results(model_results)
    return run_fusion(feature_list, model_path=model_path)


if __name__ == "__main__":
    # Smoke-test with random 576-dim feature vectors
    import json
    dummy_results = [
        {
            "model_name": "Eye CNN (Ocular Pathology)",
            "feature_vector": [0.0] * 576,
            "status": "ok",
        },
        {
            "model_name": "Thoracic CNN (Canine Radiograph)",
            "feature_vector": [0.1] * 576,
            "status": "ok",
        },
    ]
    result = fuse_model_results(dummy_results)
    print(json.dumps(result, indent=2))
