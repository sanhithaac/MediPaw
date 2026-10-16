"""
Unified Model Adapters for MediPaw AI Pipeline.

Standardizes output schemas across all 5 models:
1. Eye CNN (Ocular Pathology)
2. Skin CNN (Dermatological Pathology)
3. YOLOv8 (Wound / Trauma Detection)
4. U-Net (Wound Surface Area Segmentation)
5. Thoracic CNN (Vertebral Heart Score & Radiograph Features)
"""

import os
import sys
import time
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from PIL import Image, ImageDraw

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Directory for saving annotated previews
UPLOAD_DIR = os.path.join(_BACKEND_DIR, "static", "uploads")
OUTPUT_DIR = os.path.join(_BACKEND_DIR, "static", "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# 1. Eye CNN Adapter
# =============================================================================

_EYE_PREDICTOR = None

def get_eye_predictor():
    global _EYE_PREDICTOR
    if _EYE_PREDICTOR is None:
        try:
            from eyecnn.src.predict_eye import EyePredictor
            model_path = os.path.join(_PROJECT_ROOT, "eyecnn", "models", "eye_cnn", "best_eye_model.pth")
            if os.path.exists(model_path):
                _EYE_PREDICTOR = EyePredictor(model_path=model_path)
            else:
                _EYE_PREDICTOR = "CHECKPOINT_MISSING"
        except Exception as e:
            print(f"[Adapter Error] EyePredictor initialization failed: {e}")
            _EYE_PREDICTOR = f"ERROR: {str(e)}"
    return _EYE_PREDICTOR


def run_eye_analysis(image_path: str) -> Dict[str, Any]:
    predictor = get_eye_predictor()
    if predictor == "CHECKPOINT_MISSING":
        return {
            "status": "unavailable",
            "model_name": "Eye CNN (Ocular Pathology)",
            "prediction": "Model Checkpoint Missing",
            "confidence": None,
            "model_ready": False,
            "is_trained": False,
            "probabilities": {},
            "warnings": ["Eye CNN weights 'best_eye_model.pth' not found."],
            "diagnostics": {"source": os.path.basename(image_path)}
        }
    if isinstance(predictor, str) and predictor.startswith("ERROR"):
        return {
            "status": "error",
            "model_name": "Eye CNN (Ocular Pathology)",
            "prediction": None,
            "confidence": None,
            "model_ready": False,
            "is_trained": False,
            "warnings": [predictor],
            "diagnostics": {"source": os.path.basename(image_path)}
        }

    try:
        raw = predictor.predict(image_path, return_features=True)
        if raw.get("status") == "ERROR":
            return {
                "status": "error",
                "model_name": "Eye CNN (Ocular Pathology)",
                "prediction": None,
                "confidence": None,
                "feature_vector": None,
                "model_ready": True,
                "is_trained": True,
                "warnings": [raw.get("error_message", "Unknown error")],
                "diagnostics": {"source": os.path.basename(image_path)}
            }

        pred_class = raw.get("predicted_class", "unknown").replace("_", " ").title()
        conf = raw.get("confidence", 0.0)

        # Extract 576-dim intermediate feature vector for downstream ViT fusion
        feat_info = raw.get("intermediate_features") or {}
        feature_vector = feat_info.get("embedding") if feat_info else None

        return {
            "status": "ok",
            "model_name": "Eye CNN (Ocular Pathology)",
            "prediction": pred_class,
            "confidence": round(conf, 4),
            "feature_vector": feature_vector,
            "model_ready": True,
            "is_trained": True,
            "probabilities": raw.get("probabilities", {}),
            "warnings": [],
            "diagnostics": {
                "source": os.path.basename(image_path),
                "original_shape": raw.get("input_details", {}).get("original_dimensions"),
                "inference_time_ms": raw.get("input_details", {}).get("inference_time_ms")
            }
        }
    except Exception as exc:
        return {
            "status": "error",
            "model_name": "Eye CNN (Ocular Pathology)",
            "prediction": None,
            "confidence": None,
            "feature_vector": None,
            "model_ready": False,
            "is_trained": True,
            "warnings": [f"Inference failure: {str(exc)}"],
            "diagnostics": {"source": os.path.basename(image_path)}
        }


# =============================================================================
# 2. Skin CNN Adapter
# =============================================================================

def run_skin_analysis(image_path: str) -> Dict[str, Any]:
    # Check if local checkpoint exists
    possible_ckpts = [
        os.path.join(_PROJECT_ROOT, "skincnn", "checkpoints", "best_skin_model.pth"),
        os.path.join(_PROJECT_ROOT, "skincnn", "best_model.pth"),
        os.path.join(_PROJECT_ROOT, "model_pipeline", "2_cnn_skin_classifier", "best_model.pth")
    ]
    ckpt_path = None
    for p in possible_ckpts:
        if os.path.exists(p):
            ckpt_path = p
            break

    if ckpt_path is None:
        return {
            "status": "unavailable",
            "model_name": "Skin CNN (Dermatological Pathology)",
            "prediction": "Trained Checkpoint Not Present Locally",
            "confidence": None,
            "model_ready": False,
            "is_trained": False,
            "classes": [
                "1_Fungal_Infections", "2_Allergic_Dermatitis", "3_Demodicosis_Mange",
                "4_Bacterial_Dermatosis", "5_Healthy_Control", "6_Ringworm"
            ],
            "warnings": [
                "Skin CNN architecture is implemented (EfficientNet-V2-S / ResNet-50) and dataset split exists in skincnn/cnn1_denoised_split.",
                "Training history exists (colab_training_history.json), but .pth weight file was not downloaded into local workspace.",
                "Inference is reported as unavailable to prevent reporting fabricated diagnoses."
            ],
            "diagnostics": {"source": os.path.basename(image_path)}
        }

    # If checkpoint exists in future, inference can be executed here
    return {
        "status": "ok",
        "model_name": "Skin CNN (Dermatological Pathology)",
        "prediction": "Checkpoint detected",
        "confidence": None,
        "model_ready": True,
        "is_trained": True,
        "warnings": [],
        "diagnostics": {"source": os.path.basename(image_path)}
    }


# =============================================================================
# 3. YOLOv8 Wound Detection Adapter
# =============================================================================

def run_wound_detection(image_path: str) -> Dict[str, Any]:
    try:
        from yolov8.yolo_interface import detect_wounds
        weights_path = os.path.join(_PROJECT_ROOT, "yolov8", "weights", "best.pt")
        if not os.path.exists(weights_path):
            return {
                "status": "unavailable",
                "model_name": "YOLOv8 Wound Detector",
                "prediction": "Weights File Missing",
                "confidence": None,
                "model_ready": False,
                "is_trained": False,
                "detections": [],
                "warnings": ["yolov8/weights/best.pt not found."],
                "diagnostics": {"source": os.path.basename(image_path)}
            }

        dets = detect_wounds(image_path, weights=weights_path, conf=0.25)

        # Generate annotated preview image
        annotated_filename = f"yolo_{uuid.uuid4().hex[:8]}_{os.path.basename(image_path)}"
        annotated_path = os.path.join(OUTPUT_DIR, annotated_filename)
        
        try:
            with Image.open(image_path) as im:
                draw_img = im.convert("RGB")
                draw = ImageDraw.Draw(draw_img)
                for d in dets:
                    box = [d["x1"], d["y1"], d["x2"], d["y2"]]
                    draw.rectangle(box, outline="#ff3366", width=4)
                    draw.text((d["x1"] + 4, max(0, d["y1"] - 14)), f"Wound {d['conf']:.2f}", fill="#ff3366")
                draw_img.save(annotated_path, "JPEG")
                viz_url = f"/static/outputs/{annotated_filename}"
        except Exception:
            viz_url = None

        count = len(dets)
        top_conf = max([d["conf"] for d in dets]) if count > 0 else None
        label = f"{count} Wound{'s' if count != 1 else ''} Detected" if count > 0 else "No Acute Wounds Detected"

        return {
            "status": "ok",
            "model_name": "YOLOv8 Wound Detector",
            "prediction": label,
            "confidence": top_conf,
            "detection_count": count,
            "detections": dets,
            "model_ready": True,
            "is_trained": True,
            "visualization_url": viz_url,
            "warnings": [],
            "diagnostics": {
                "source": os.path.basename(image_path),
                "threshold": 0.25
            }
        }
    except Exception as exc:
        return {
            "status": "error",
            "model_name": "YOLOv8 Wound Detector",
            "prediction": None,
            "confidence": None,
            "model_ready": False,
            "is_trained": True,
            "detections": [],
            "warnings": [f"YOLOv8 execution failed: {str(exc)}"],
            "diagnostics": {"source": os.path.basename(image_path)}
        }


# =============================================================================
# 4. U-Net Wound Segmentation Adapter
# =============================================================================

def run_wound_segmentation(image_path: str) -> Dict[str, Any]:
    try:
        from unet.medipaw_unet_api import segment_wounds
        yolo_weights = os.path.join(_PROJECT_ROOT, "yolov8", "weights", "best.pt")
        unet_weights = os.path.join(_PROJECT_ROOT, "unet", "checkpoints", "best_model.pt")
        output_dir = os.path.join(_BACKEND_DIR, "static", "outputs")

        raw = segment_wounds(
            image_path=image_path,
            yolo_weights=yolo_weights,
            unet_weights=unet_weights,
            output_dir=output_dir
        )

        is_trained = raw.get("trained_model", False)
        status = "ok" if is_trained else "untrained_fallback"
        warnings = []
        if not is_trained:
            warnings.append(
                "U-Net checkpoint ('unet/checkpoints/best_model.pt') is missing. "
                "Pipeline ran with untrained random weights as a fallback demonstration."
            )
        warnings.append(
            "Wound dataset contains bounding-box annotations rather than genuine pixel-level masks. "
            "Segmentation percentages should be interpreted with clinical caution."
        )

        stats = raw.get("segmentation_stats", [])
        total_pixels = sum(s.get("wound_pixels", 0) for s in stats)
        avg_pct = round(sum(s.get("coverage_pct", 0.0) for s in stats) / len(stats), 2) if stats else 0.0

        overlay_url = None
        if raw.get("overlay_path") and os.path.exists(raw["overlay_path"]):
            overlay_url = f"/static/outputs/{os.path.basename(raw['overlay_path'])}"

        mask_url = None
        if raw.get("mask_path") and os.path.exists(raw["mask_path"]):
            mask_url = f"/static/outputs/{os.path.basename(raw['mask_path'])}"

        return {
            "status": status,
            "model_name": "U-Net + YOLOv8 Wound Segmenter",
            "prediction": f"Estimated Wound Area: {avg_pct}% of ROI",
            "confidence": None,
            "wound_surface_area_pct": avg_pct,
            "total_wound_pixels": total_pixels,
            "segmentation_stats": stats,
            "model_ready": is_trained,
            "is_trained": is_trained,
            "overlay_url": overlay_url,
            "mask_url": mask_url,
            "warnings": warnings,
            "diagnostics": {"source": os.path.basename(image_path)}
        }
    except Exception as exc:
        return {
            "status": "error",
            "model_name": "U-Net Wound Segmenter",
            "prediction": None,
            "confidence": None,
            "model_ready": False,
            "is_trained": False,
            "warnings": [f"U-Net pipeline error: {str(exc)}"],
            "diagnostics": {"source": os.path.basename(image_path)}
        }


# =============================================================================
# 5. Thoracic CNN Adapter
# =============================================================================

def run_thoracic_analysis(image_path: str) -> Dict[str, Any]:
    """Run Thoracic CNN with feature extraction enabled for ViT fusion."""
    try:
        from thoraciccnn.thoraciccnn_api import predict_thoracic
        # Return features=True so the 576-dim embedding is available for ViT fusion
        res = predict_thoracic(image_path, return_features=True)
        return res
    except Exception as exc:
        return {
            "status": "error",
            "model_name": "Thoracic CNN",
            "prediction": None,
            "confidence": None,
            "feature_vector": None,
            "model_ready": False,
            "is_trained": False,
            "warnings": [f"Thoracic CNN error: {str(exc)}"],
            "diagnostics": {"source": os.path.basename(image_path)}
        }


# =============================================================================
# 6. Multi-Modal ViT Fusion Adapter
# =============================================================================

def run_vit_fusion(model_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fuses feature embeddings from available CNN models via the Multi-Modal ViT.

    Args:
        model_results: List of standardized model result dicts. Dicts that include
                       a 'feature_vector' key with a 576-dim list participate in fusion.

    Returns:
        JSON-serializable fusion result dict.
    """
    try:
        from multimodal_vit.multimodal_api import fuse_model_results
        return fuse_model_results(model_results)
    except Exception as exc:
        return {
            "status": "error",
            "model_name": "Multi-Modal ViT (Fusion Layer)",
            "prediction": None,
            "urgency_score": None,
            "triage_label": None,
            "fused_cls_features": None,
            "active_modalities": [],
            "is_trained": False,
            "model_ready": False,
            "warnings": [f"ViT fusion adapter error: {str(exc)}"],
            "diagnostics": {"modality_count": len(model_results)}
        }
