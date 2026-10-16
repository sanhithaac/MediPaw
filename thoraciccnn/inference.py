"""
Inference Module for MediPaw Thoracic CNN.

Handles input image validation, preprocessing, feature extraction, and prediction.
Gracefully handles missing checkpoints and unannotated data states.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Union, Optional

import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from dataset_loader import parse_patient_id_from_filename, IMAGENET_MEAN, IMAGENET_STD
from model import build_thoracic_model


class ThoracicPredictor:
    """
    Inference and feature extraction interface for Thoracic CNN.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        backbone_name: str = "mobilenet_v3_small",
        device: Optional[Union[str, torch.device]] = None
    ):
        self.backbone_name = backbone_name
        self.model_path = model_path or os.path.join(_THIS_DIR, "checkpoints", "best_thoracic_model.pth")

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        elif isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        self.model = None
        self.is_trained = False
        self.feature_dim = 576 if backbone_name == "mobilenet_v3_small" else 512

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])

        self._load_model()

    def _load_model(self):
        """Attempts to load model weights if checkpoint is available."""
        if os.path.exists(self.model_path):
            try:
                ckpt = torch.load(self.model_path, map_location=self.device)
                self.backbone_name = ckpt.get("backbone", self.backbone_name)
                self.is_trained = ckpt.get("trained", False)
                self.feature_dim = ckpt.get("feature_dim", self.feature_dim)

                self.model = build_thoracic_model(
                    backbone_name=self.backbone_name,
                    pretrained=False,
                    device=self.device
                )
                self.model.load_state_dict(ckpt["model_state_dict"])
                self.model.eval()
            except Exception as e:
                print(f"[ThoracicPredictor Warning] Checkpoint load failed: {e}")
                self.model = None
                self.is_trained = False
        else:
            self.model = None
            self.is_trained = False

    def predict(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        return_features: bool = True
    ) -> Dict[str, Any]:
        """
        Runs inference or feature extraction on a thoracic radiograph.
        """
        start_time = time.time()
        source_name = "in-memory"
        pid = "unknown"

        # 1. Image decoding & validation
        if isinstance(image_input, (str, Path)):
            img_path = str(image_input)
            source_name = os.path.basename(img_path)
            pid = parse_patient_id_from_filename(img_path)

            if not os.path.exists(img_path):
                return {
                    "status": "error",
                    "model_name": "Thoracic CNN",
                    "task": "Vertebral Heart Score (VHS) Regression",
                    "prediction": None,
                    "confidence": None,
                    "model_ready": False,
                    "warnings": [f"Input image file not found: '{img_path}'"],
                    "diagnostics": {"source": source_name}
                }
            try:
                with Image.open(img_path) as raw:
                    img = raw.convert("RGB")
                    orig_size = img.size
            except Exception as e:
                return {
                    "status": "error",
                    "model_name": "Thoracic CNN",
                    "task": "Vertebral Heart Score (VHS) Regression",
                    "prediction": None,
                    "confidence": None,
                    "model_ready": False,
                    "warnings": [f"Unable to decode image file: {str(e)}"],
                    "diagnostics": {"source": source_name}
                }

        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
            orig_size = img.size

        elif isinstance(image_input, np.ndarray):
            try:
                img = Image.fromarray(image_input).convert("RGB")
                orig_size = img.size
            except Exception as e:
                return {
                    "status": "error",
                    "model_name": "Thoracic CNN",
                    "task": "Vertebral Heart Score (VHS) Regression",
                    "prediction": None,
                    "confidence": None,
                    "model_ready": False,
                    "warnings": [f"Invalid numpy array image: {str(e)}"],
                    "diagnostics": {"source": source_name}
                }
        else:
            return {
                "status": "error",
                "model_name": "Thoracic CNN",
                "task": "Vertebral Heart Score (VHS) Regression",
                "prediction": None,
                "confidence": None,
                "model_ready": False,
                "warnings": [f"Unsupported image input type: {type(image_input)}"],
                "diagnostics": {"source": source_name}
            }

        # 2. Check if trained model is available
        if not self.is_trained or self.model is None:
            # Checkpoint not trained on verified ground-truth
            elapsed = time.time() - start_time
            return {
                "status": "unvalidated_prototype",
                "model_name": "Thoracic CNN (Canine Radiograph)",
                "task": "Vertebral Heart Score (VHS) Regression / Feature Extraction",
                "prediction": "Awaiting Clinical Ground-Truth Annotations",
                "confidence": None,
                "vhs_score": None,
                "feature_vector": None,
                "is_trained": False,
                "model_ready": False,
                "warnings": [
                    "Thoracic dataset (PMC8111263 / Mendeley ktx4cj55pn/1) consists of 153 unannotated canine radiographs released without ground-truth VHS measurements or pathology labels.",
                    "No artificial labels have been fabricated. Supervised model weights are not trained on clinical ground truth.",
                    "For veterinary clinical decision-support, ground-truth annotations must be collected and trained."
                ],
                "diagnostics": {
                    "source": source_name,
                    "patient_id": pid,
                    "dimensions": orig_size,
                    "inference_time_ms": round(elapsed * 1000, 2)
                }
            }

        # 3. Model Inference (when trained weights exist)
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            if return_features:
                vhs_pred, feat = self.model.forward_with_features(tensor)
                feature_vec = feat.squeeze(0).cpu().numpy().tolist()
            else:
                vhs_pred = self.model(tensor)
                feature_vec = None

        val = float(vhs_pred.item())
        elapsed = time.time() - start_time

        return {
            "status": "ok",
            "model_name": "Thoracic CNN (Canine Radiograph)",
            "task": "Vertebral Heart Score (VHS) Regression",
            "prediction": f"Predicted VHS: {val:.2f}",
            "confidence": None,  # Not applicable for uncalibrated regression
            "vhs_score": round(val, 2),
            "feature_vector": feature_vec,
            "is_trained": True,
            "model_ready": True,
            "warnings": [],
            "diagnostics": {
                "source": source_name,
                "patient_id": pid,
                "dimensions": orig_size,
                "inference_time_ms": round(elapsed * 1000, 2)
            }
        }
