"""
Inference and Feature Extraction Pipeline for MediPaw Eye CNN.

Provides both a standalone CLI and an importable Python API (EyePredictor):
- Validates input images and handles corruption/missing files gracefully
- Applies identical ImageNet preprocessing and normalization as training
- Produces:
    1. Predicted ocular disease class and top confidence score
    2. Calibrated Softmax probability distribution across all 4 classes
    3. Intermediate pooled feature embedding vector (576-dim for MobileNetV3-Small)
       specifically designed for downstream MediPaw Multi-Modal ViT fusion
    4. Detailed input diagnostics and inference metadata
- Maintains strict clinical separation: disease probabilities are kept distinct
  from downstream triage severity scoring.
"""

import os
import sys
# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Union, Optional, Tuple, List

import numpy as np
from PIL import Image

import torch
import torchvision.transforms as transforms

# Import EyeCNN architecture
from eye_model import build_eye_model


class EyePredictor:
    """
    Inference and feature extraction interface for MediPaw Eye CNN.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        device: Optional[Union[str, torch.device]] = None
    ):
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.model_path = model_path or os.path.join(base_dir, "models", "eye_cnn", "best_eye_model.pth")
        self.config_path = config_path or os.path.join(base_dir, "models", "eye_cnn", "model_config.json")

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        elif isinstance(device, str):
            self.device = torch.device(device)
        else:
            self.device = device

        self.model = None
        self.class_names = []
        self.class_to_idx = {}
        self.idx_to_class = {}
        self.feature_dim = 576
        self.backbone_name = "mobilenet_v3_small"
        self.transform = None

        self._load_model_and_config()

    def _load_model_and_config(self):
        """Loads configuration, weights, and sets up transforms."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Eye CNN model checkpoint not found at: {self.model_path}.\n"
                f"Please verify training has completed and generated 'best_eye_model.pth'."
            )

        # Load checkpoint
        checkpoint = torch.load(self.model_path, map_location=self.device)
        self.class_names = checkpoint.get("class_names", [])
        self.class_to_idx = checkpoint.get("class_to_idx", {name: i for i, name in enumerate(self.class_names)})
        self.idx_to_class = {v: k for k, v in self.class_to_idx.items()}
        self.backbone_name = checkpoint.get("backbone", "mobilenet_v3_small")
        self.feature_dim = checkpoint.get("feature_dim", 576)

        num_classes = len(self.class_names)
        self.model = build_eye_model(
            num_classes=num_classes,
            backbone_name=self.backbone_name,
            pretrained=False,
            device=self.device
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

        # ImageNet normalization standard
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def predict(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        return_features: bool = True
    ) -> Dict[str, Any]:
        """
        Runs inference on an eye image.

        Args:
            image_input: File path, PIL Image, or numpy array.
            return_features: Whether to extract and return intermediate feature embeddings
                            for downstream ViT cross-modal fusion.

        Returns:
            Dictionary containing prediction results, probabilities, input metadata,
            and intermediate feature vectors.
        """
        start_time = time.time()

        # 1. Image loading and validation
        img = None
        orig_shape = None
        source_name = "in-memory-image"

        if isinstance(image_input, (str, Path)):
            img_path = str(image_input)
            source_name = os.path.basename(img_path)
            if not os.path.exists(img_path):
                return {
                    "status": "ERROR",
                    "error_message": f"Input image file not found: '{img_path}'",
                    "source": source_name
                }
            try:
                with Image.open(img_path) as raw_img:
                    raw_img.verify()
                img = Image.open(img_path).convert("RGB")
                orig_shape = img.size  # (width, height)
            except Exception as e:
                return {
                    "status": "ERROR",
                    "error_message": f"Unable to decode image file '{img_path}'. Reason: {str(e)}",
                    "source": source_name
                }

        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
            orig_shape = img.size

        elif isinstance(image_input, np.ndarray):
            try:
                img = Image.fromarray(image_input).convert("RGB")
                orig_shape = img.size
            except Exception as e:
                return {
                    "status": "ERROR",
                    "error_message": f"Invalid numpy image array: {str(e)}",
                    "source": source_name
                }
        else:
            return {
                "status": "ERROR",
                "error_message": f"Unsupported image input type: {type(image_input)}",
                "source": source_name
            }

        # 2. Preprocessing
        try:
            tensor = self.transform(img).unsqueeze(0).to(self.device)
        except Exception as e:
            return {
                "status": "ERROR",
                "error_message": f"Preprocessing failed: {str(e)}",
                "source": source_name
            }

        # 3. Model Inference
        with torch.no_grad():
            if return_features:
                logits, features = self.model.forward_with_features(tensor)
                feature_vec = features.squeeze(0).cpu().numpy().tolist()
            else:
                logits = self.model(tensor)
                feature_vec = None

            probs_tensor = torch.softmax(logits, dim=1).squeeze(0).cpu()
            probs_np = probs_tensor.numpy()

        pred_idx = int(np.argmax(probs_np))
        pred_class = self.idx_to_class.get(pred_idx, f"class_{pred_idx}")
        confidence = float(probs_np[pred_idx])

        # Map probabilities per class
        class_probabilities = {
            self.idx_to_class[i]: round(float(probs_np[i]), 5)
            for i in range(len(self.class_names))
        }

        inference_time_ms = round((time.time() - start_time) * 1000.0, 2)

        return {
            "status": "SUCCESS",
            "source": source_name,
            "predicted_class": pred_class,
            "predicted_class_id": pred_idx,
            "confidence": round(confidence, 4),
            "probabilities": class_probabilities,
            "intermediate_features": {
                "dimension": self.feature_dim,
                "embedding": feature_vec,
                "note_for_downstream_vit": "576-dim global average pooled feature representation ready for multi-modal cross-attention fusion"
            } if return_features else None,
            "input_details": {
                "original_dimensions": [orig_shape[0], orig_shape[1]],
                "model_input_resolution": [224, 224],
                "channels": 3,
                "device_used": str(self.device),
                "backbone": self.backbone_name,
                "inference_time_ms": inference_time_ms
            }
        }


def parse_cli():
    parser = argparse.ArgumentParser(description="Run ocular abnormality classification on a dog eye image.")
    parser.add_argument("--image", type=str, required=True, help="Path to the eye image file to inspect")
    parser.add_argument("--model", type=str, default="models/eye_cnn/best_eye_model.pth", help="Path to checkpoint")
    parser.add_argument("--save_json", type=str, default=None, help="Optional path to save prediction JSON output")
    parser.add_argument("--no_features", action="store_true", help="Exclude intermediate feature embedding from JSON output")
    return parser.parse_args()


def main():
    args = parse_cli()

    print("=" * 70)
    print("MediPaw Eye CNN: Ocular Abnormality Inference")
    print("=" * 70)

    try:
        predictor = EyePredictor(model_path=args.model)
    except Exception as e:
        print(f"Error initializing EyePredictor: {e}")
        sys.exit(1)

    result = predictor.predict(args.image, return_features=(not args.no_features))

    if result["status"] == "ERROR":
        print(f"\n[INFERENCE FAILED]")
        print(f"Error: {result['error_message']}")
        sys.exit(1)

    print(f"\nImage:            {result['source']} ({result['input_details']['original_dimensions'][0]}x{result['input_details']['original_dimensions'][1]})")
    print(f"Inference Time:   {result['input_details']['inference_time_ms']} ms (Device: {result['input_details']['device_used']})")
    print(f"Backbone:         {result['input_details']['backbone']}")
    print("-" * 70)
    print(f"PREDICTED CLASS:  {result['predicted_class'].upper()}")
    print(f"CONFIDENCE:       {result['confidence'] * 100:.2f}%")
    print("-" * 70)
    print("Class Probability Distribution:")
    for cls_name, prob in result["probabilities"].items():
        bar_len = int(prob * 40)
        bar = "#" * bar_len + "-" * (40 - bar_len)
        print(f"  {cls_name:16s}: {prob * 100:6.2f}% |{bar}|")
    print("-" * 70)

    if result.get("intermediate_features"):
        dim = result["intermediate_features"]["dimension"]
        print(f"Downstream ViT Feature Vector: Extracted {dim}-dimensional embedding.")

    if args.save_json:
        out_path = Path(args.save_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved detailed prediction JSON to: {args.save_json}")


if __name__ == "__main__":
    main()
