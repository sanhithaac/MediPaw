"""
MediPaw Thoracic CNN — Backend Integration API.

Exposes a clean, documented, JSON-serializable callable for the MediPaw backend:
    from thoraciccnn.thoraciccnn_api import predict_thoracic

    result = predict_thoracic("path/to/radiograph.png")
"""

import os
import sys
from typing import Dict, Any, Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from inference import ThoracicPredictor

# Module-level cached predictor instance to prevent reloading weights on every request
_GLOBAL_PREDICTOR: Optional[ThoracicPredictor] = None


def get_predictor(model_path: Optional[str] = None) -> ThoracicPredictor:
    """Returns or initializes the singleton ThoracicPredictor instance."""
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None or (model_path and model_path != _GLOBAL_PREDICTOR.model_path):
        _GLOBAL_PREDICTOR = ThoracicPredictor(model_path=model_path)
    return _GLOBAL_PREDICTOR


def predict_thoracic(
    image_path: str,
    model_path: Optional[str] = None,
    return_features: bool = False
) -> Dict[str, Any]:
    """
    Predict VHS or extract features from a canine thoracic radiograph.

    Parameters:
        image_path: File path to radiograph (PNG, JPG, GIF).
        model_path: Optional custom path to model checkpoint.
        return_features: If True, includes intermediate feature vector for ViT fusion.

    Returns:
        JSON-serializable dictionary with standard MediPaw schema.
    """
    try:
        predictor = get_predictor(model_path=model_path)
        return predictor.predict(image_path, return_features=return_features)
    except Exception as exc:
        return {
            "status": "error",
            "model_name": "Thoracic CNN",
            "task": "Vertebral Heart Score (VHS) Regression",
            "prediction": None,
            "confidence": None,
            "vhs_score": None,
            "feature_vector": None,
            "is_trained": False,
            "model_ready": False,
            "warnings": [f"Execution error in Thoracic CNN module: {str(exc)}"],
            "diagnostics": {"source": os.path.basename(image_path) if image_path else "unknown"}
        }


if __name__ == "__main__":
    test_img = sys.argv[1] if len(sys.argv) > 1 else None
    if not test_img:
        sample_dir = os.path.join(_THIS_DIR, "data")
        if os.path.exists(sample_dir):
            files = [os.path.join(sample_dir, f) for f in os.listdir(sample_dir) if f.endswith(".png")]
            if files:
                test_img = files[0]

    if test_img:
        print(f"Testing predict_thoracic on: {test_img}")
        res = predict_thoracic(test_img)
        import pprint
        pprint.pprint(res)
    else:
        print("No image provided for testing.")
