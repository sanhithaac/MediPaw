"""
Multi-Modal ViT Inference Module for MediPaw.

Collects feature embeddings from trained model adapters and runs them through
the Multi-Modal ViT fusion encoder.

Scientific status: The ViT model architecture is implemented and tested.
No supervised multi-modal clinical cohort training has yet been performed.
Outputs are transparently disclosed as architecture_prototype.
"""

from __future__ import annotations
import os
import sys
import time
from typing import Any, Dict, List, Optional, Union

import torch

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from multimodal_vit.model import MultiModalViT, build_multimodal_vit


# ─────────────────────────────────────────────────────────────────────────────
# Singleton model cache
# ─────────────────────────────────────────────────────────────────────────────

_VIT_MODEL: Optional[MultiModalViT] = None
_VIT_IS_TRAINED: bool = False


def _get_vit_model(model_path: Optional[str] = None) -> MultiModalViT:
    global _VIT_MODEL, _VIT_IS_TRAINED

    if _VIT_MODEL is not None:
        return _VIT_MODEL

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _VIT_MODEL = build_multimodal_vit(device=device)
    _VIT_IS_TRAINED = False

    # Attempt to load trained checkpoint
    if model_path is None:
        model_path = os.path.join(_THIS_DIR, "checkpoints", "best_vit_model.pth")

    if os.path.exists(model_path):
        try:
            ckpt = torch.load(model_path, map_location=device)
            _VIT_MODEL.load_state_dict(ckpt["model_state_dict"])
            _VIT_IS_TRAINED = ckpt.get("trained", False)
        except Exception as e:
            print(f"[MultiModalViT Warning] Checkpoint load failed: {e}")
            _VIT_IS_TRAINED = False

    _VIT_MODEL.eval()
    return _VIT_MODEL


# ─────────────────────────────────────────────────────────────────────────────
# Feature collection helper
# ─────────────────────────────────────────────────────────────────────────────

MODALITY_FEATURE_DIM = 576


def collect_features_from_results(
    model_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extracts feature vectors from model results that include a 'feature_vector' key.

    Returns a list of dicts: [{model_name, feature_vector}, ...]
    Only models that returned a valid 576-dim feature vector are included.
    """
    collected = []
    for res in model_results:
        fv = res.get("feature_vector")
        if fv is not None and isinstance(fv, list) and len(fv) == MODALITY_FEATURE_DIM:
            collected.append({
                "model_name": res.get("model_name", "Unknown"),
                "feature_vector": fv,
            })
    return collected


# ─────────────────────────────────────────────────────────────────────────────
# Main fusion inference function
# ─────────────────────────────────────────────────────────────────────────────

def run_fusion(
    feature_list: List[Dict[str, Any]],
    model_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fuses a list of modality feature vectors through the Multi-Modal ViT.

    Args:
        feature_list: List of {'model_name': str, 'feature_vector': List[float]}
                      Each feature_vector must be length 576.
        model_path:   Optional explicit checkpoint path.

    Returns:
        JSON-serializable result dict.
    """
    start = time.time()

    if not feature_list:
        return {
            "status": "skipped",
            "model_name": "Multi-Modal ViT (Fusion Layer)",
            "prediction": "No modality feature vectors available for fusion.",
            "urgency_score": None,
            "triage_label": None,
            "fused_features": None,
            "active_modalities": [],
            "is_trained": False,
            "model_ready": False,
            "warnings": [
                "None of the active models returned a 576-dim feature vector. "
                "Eye CNN and Thoracic CNN must be loaded with return_features=True to enable fusion."
            ],
            "diagnostics": {"modality_count": 0}
        }

    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = _get_vit_model(model_path=model_path)

        # Build tensor: (1, N, 576)
        tensors = []
        for fd in feature_list:
            t = torch.tensor(fd["feature_vector"], dtype=torch.float32)
            tensors.append(t)

        embedding_batch = torch.stack(tensors, dim=0).unsqueeze(0).to(device)  # (1, N, 576)

        with torch.no_grad():
            urgency, triage_logits, cls_feat = model(embedding_batch)

        urgency_val = float(urgency.item())
        triage_probs = torch.softmax(triage_logits, dim=-1).squeeze(0).cpu().tolist()
        triage_idx = int(torch.argmax(triage_logits, dim=-1).item())
        triage_label = MultiModalViT.TRIAGE_CLASSES[triage_idx]
        cls_features = cls_feat.squeeze(0).cpu().tolist()

        elapsed = time.time() - start
        modality_names = [fd["model_name"] for fd in feature_list]

        triage_prob_map = {
            MultiModalViT.TRIAGE_CLASSES[i]: round(triage_probs[i], 4)
            for i in range(len(MultiModalViT.TRIAGE_CLASSES))
        }

        status = "ok" if _VIT_IS_TRAINED else "architecture_prototype"
        warnings = []
        if not _VIT_IS_TRAINED:
            warnings.append(
                "Multi-Modal ViT fusion layer is not yet trained on a multi-modal clinical cohort. "
                "Urgency score and triage classification are from randomly-initialized weights "
                "and MUST NOT be used for clinical decision-making. "
                "The rule-based triage priority in the intake pipeline is the operational fallback."
            )

        return {
            "status": status,
            "model_name": "Multi-Modal ViT (Fusion Layer)",
            "task": "Cross-Modal Feature Fusion & Triage Urgency Estimation",
            "prediction": f"Fused Urgency Score: {urgency_val:.3f} → {triage_label}"
                          if _VIT_IS_TRAINED else "Architecture Prototype — Untrained Weights",
            "urgency_score": round(urgency_val, 4) if _VIT_IS_TRAINED else None,
            "triage_label": triage_label if _VIT_IS_TRAINED else None,
            "triage_probabilities": triage_prob_map if _VIT_IS_TRAINED else None,
            "fused_cls_features": cls_features,
            "active_modalities": modality_names,
            "is_trained": _VIT_IS_TRAINED,
            "model_ready": True,
            "warnings": warnings,
            "diagnostics": {
                "modality_count": len(feature_list),
                "feature_dim": MODALITY_FEATURE_DIM,
                "d_model": model.d_model,
                "inference_time_ms": round((time.time() - start) * 1000, 2),
            }
        }

    except Exception as exc:
        return {
            "status": "error",
            "model_name": "Multi-Modal ViT (Fusion Layer)",
            "prediction": None,
            "urgency_score": None,
            "triage_label": None,
            "fused_cls_features": None,
            "active_modalities": [fd["model_name"] for fd in feature_list],
            "is_trained": False,
            "model_ready": False,
            "warnings": [f"ViT fusion error: {str(exc)}"],
            "diagnostics": {"modality_count": len(feature_list)}
        }
