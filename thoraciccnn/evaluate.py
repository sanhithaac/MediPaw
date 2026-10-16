"""
Evaluation Module for MediPaw Thoracic CNN.

Computes task-appropriate metrics for Vertebral Heart Score (VHS) regression:
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)
- Mean Absolute Error (MAE)
- Coefficient of Determination (R²)

Adheres to scientific reporting standards:
- Does not report training metrics as test metrics.
- Does not report fake evaluation numbers when ground-truth labels are absent.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

import torch
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from dataset_loader import get_dataloaders
from model import build_thoracic_model


def evaluate_checkpoint(
    checkpoint_path: str,
    data_dir: str,
    annotations_path: Optional[str] = None,
    output_dir: str = "eval_outputs",
    device_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates a saved checkpoint on the held-out test split.
    """
    device = torch.device(device_str if device_str else ("cuda" if torch.cuda.is_available() else "cpu"))
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(checkpoint_path):
        return {
            "status": "error",
            "message": f"Checkpoint not found at: {checkpoint_path}",
            "evaluated": False
        }

    checkpoint = torch.load(checkpoint_path, map_location=device)
    trained = checkpoint.get("trained", False)
    backbone = checkpoint.get("backbone", "mobilenet_v3_small")

    if not trained:
        msg = (
            "Checkpoint is marked as unvalidated (no supervised ground-truth training). "
            "Evaluation metrics cannot be legitimately reported without verified clinical labels."
        )
        print(f"[EVALUATION BLOCKED] {msg}")
        return {
            "status": "unvalidated",
            "message": msg,
            "evaluated": False,
            "metrics": None
        }

    # Load annotations
    labels = {}
    if annotations_path and os.path.exists(annotations_path):
        from train import load_annotation_file
        labels = load_annotation_file(annotations_path)

    if not labels:
        msg = "No ground-truth labels available for test evaluation."
        print(f"[EVALUATION BLOCKED] {msg}")
        return {
            "status": "blocked",
            "message": msg,
            "evaluated": False,
            "metrics": None
        }

    _, _, test_loader, meta = get_dataloaders(
        data_dir=data_dir,
        labels=labels,
        batch_size=8,
        task="vhs_regression"
    )

    model = build_thoracic_model(backbone_name=backbone, pretrained=False, device=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in test_loader:
            images = batch["image"].to(device)
            target = batch["label"].to(device)
            has_labels = batch["has_label"]

            valid_mask = torch.tensor(has_labels, dtype=torch.bool, device=device)
            if not valid_mask.any():
                continue

            preds = model(images)
            all_preds.extend(preds[valid_mask].cpu().numpy().tolist())
            all_targets.extend(target[valid_mask].cpu().numpy().tolist())

    if not all_preds:
        return {
            "status": "empty",
            "message": "No test samples had valid labels.",
            "evaluated": False
        }

    p = np.array(all_preds)
    t = np.array(all_targets)

    mse = float(np.mean((p - t) ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(np.mean(np.abs(p - t)))
    ss_res = np.sum((t - p) ** 2)
    ss_tot = np.sum((t - np.mean(t)) ** 2)
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    metrics = {
        "num_test_samples": len(p),
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4)
    }

    report_path = os.path.join(output_dir, "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print("=" * 60)
    print("THORACIC CNN TEST SET EVALUATION RESULTS")
    print("=" * 60)
    print(f"Test samples: {metrics['num_test_samples']}")
    print(f"MSE:          {metrics['mse']}")
    print(f"RMSE:         {metrics['rmse']}")
    print(f"MAE:          {metrics['mae']}")
    print(f"R² Score:     {metrics['r2']}")
    print(f"Report saved to: {report_path}")

    return {
        "status": "success",
        "evaluated": True,
        "metrics": metrics
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate MediPaw Thoracic CNN")
    parser.add_argument("--checkpoint", type=str, default=os.path.join(_THIS_DIR, "checkpoints", "best_thoracic_model.pth"))
    parser.add_argument("--data_dir", type=str, default=os.path.join(_THIS_DIR, "data"))
    parser.add_argument("--annotations", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default=os.path.join(_THIS_DIR, "eval_outputs"))
    args = parser.parse_args()

    evaluate_checkpoint(args.checkpoint, args.data_dir, args.annotations, args.output_dir)
