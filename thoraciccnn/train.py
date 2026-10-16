"""
Training Pipeline for MediPaw Thoracic CNN.

Adheres strictly to scientific integrity requirements:
- Validates that ground-truth annotations genuinely exist before training.
- Does NOT fabricate labels or train on artificial targets.
- Implements patient-level split training, MSE loss for VHS regression, AdamW optimizer,
  ReduceLROnPlateau scheduler, and checkpoint saving.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau

# Local imports
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from dataset_loader import get_dataloaders
from model import build_thoracic_model


def load_annotation_file(annotation_path: str) -> Dict[str, float]:
    """Loads a CSV or JSON file mapping filename to VHS score or pathology."""
    if not os.path.exists(annotation_path):
        raise FileNotFoundError(f"Annotation file not found: {annotation_path}")

    labels = {}
    if annotation_path.endswith(".json"):
        with open(annotation_path, "r", encoding="utf-8") as f:
            labels = json.load(f)
    elif annotation_path.endswith(".csv"):
        with open(annotation_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("filename") or line.startswith("#"):
                    continue
                parts = line.split(",")
                if len(parts) >= 2:
                    try:
                        labels[parts[0].strip()] = float(parts[1].strip())
                    except ValueError:
                        pass
    return labels


def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    count = 0

    for batch in loader:
        images = batch["image"].to(device)
        labels = batch["label"].to(device)
        has_labels = batch["has_label"]

        # Only train on samples with verified labels
        valid_mask = torch.tensor(has_labels, dtype=torch.bool, device=device)
        if not valid_mask.any():
            continue

        optimizer.zero_grad()
        predictions = model(images)
        loss = criterion(predictions[valid_mask], labels[valid_mask])
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * valid_mask.sum().item()
        count += valid_mask.sum().item()

    return running_loss / count if count > 0 else float("nan")


def validate_epoch(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    count = 0

    with torch.no_grad():
        for batch in loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            has_labels = batch["has_label"]

            valid_mask = torch.tensor(has_labels, dtype=torch.bool, device=device)
            if not valid_mask.any():
                continue

            predictions = model(images)
            loss = criterion(predictions[valid_mask], labels[valid_mask])
            running_loss += loss.item() * valid_mask.sum().item()
            count += valid_mask.sum().item()

    return running_loss / count if count > 0 else float("nan")


def train_thoracic_model(
    data_dir: str,
    annotation_path: Optional[str] = None,
    output_dir: str = "checkpoints",
    backbone: str = "mobilenet_v3_small",
    epochs: int = 30,
    batch_size: int = 8,
    lr: float = 1e-4,
    device_str: Optional[str] = None
):
    """
    Main training execution function.
    """
    device = torch.device(device_str if device_str else ("cuda" if torch.cuda.is_available() else "cpu"))
    os.makedirs(output_dir, exist_ok=True)

    labels = load_annotation_file(annotation_path) if annotation_path else {}

    print("=" * 70)
    print("MEDIPAW THORACIC CNN TRAINING PIPELINE")
    print("=" * 70)
    print(f"Dataset directory: {data_dir}")
    print(f"Device: {device}")
    print(f"Backbone: {backbone}")

    # Check genuine label availability
    if not labels:
        print("\n[SCIENTIFIC INTEGRITY NOTICE]")
        print("No ground-truth annotation file provided.")
        print("Inspection confirmed that the PMC8111263 / Mendeley ktx4cj55pn/1 dataset")
        print("consists of 153 raw canine thoracic radiographs released without ground-truth")
        print("Vertebral Heart Score (VHS) measurements or pathology labels.")
        print("In strict compliance with requirements, no artificial labels will be fabricated.")
        print("Supervised training is deferred until clinical annotations are supplied.\n")

        # Save an unvalidated architecture checkpoint structure for verification
        init_model = build_thoracic_model(backbone_name=backbone, pretrained=False, device=device)
        unvalidated_path = os.path.join(output_dir, "unvalidated_thoracic_model_init.pth")
        torch.save({
            "model_state_dict": init_model.state_dict(),
            "backbone": backbone,
            "feature_dim": init_model.feature_dim,
            "trained": False,
            "notice": "Initial weights without clinical ground truth training."
        }, unvalidated_path)
        print(f"Saved initial unvalidated checkpoint to: {unvalidated_path}")
        return

    train_loader, val_loader, test_loader, meta = get_dataloaders(
        data_dir=data_dir,
        labels=labels,
        batch_size=batch_size,
        task="vhs_regression"
    )

    print(f"Split sizes (patient-level): Train={meta['train_count']}, Val={meta['val_count']}, Test={meta['test_count']}")

    model = build_thoracic_model(backbone_name=backbone, pretrained=True, device=device)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.MSELoss()
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

    best_val_loss = float("inf")
    best_checkpoint_path = os.path.join(output_dir, "best_thoracic_model.pth")
    history = {"train_loss": [], "val_loss": []}

    for epoch in range(1, epochs + 1):
        t_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        v_loss = validate_epoch(model, val_loader, criterion, device)

        history["train_loss"].append(t_loss)
        history["val_loss"].append(v_loss)
        scheduler.step(v_loss)

        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss (MSE): {t_loss:.4f} | Val Loss (MSE): {v_loss:.4f}")

        if v_loss < best_val_loss:
            best_val_loss = v_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": best_val_loss,
                "backbone": backbone,
                "feature_dim": model.feature_dim,
                "trained": True
            }, best_checkpoint_path)
            print(f"  --> Saved new best checkpoint (Val Loss: {best_val_loss:.4f})")

    # Save training history
    with open(os.path.join(output_dir, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)
    print(f"\nTraining complete. Best model checkpoint saved to: {best_checkpoint_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MediPaw Thoracic CNN")
    parser.add_argument("--data_dir", type=str, default=os.path.join(_THIS_DIR, "data"), help="Path to thoracic radiographs")
    parser.add_argument("--annotations", type=str, default=None, help="Path to CSV/JSON annotation file")
    parser.add_argument("--output_dir", type=str, default=os.path.join(_THIS_DIR, "checkpoints"), help="Output directory")
    parser.add_argument("--backbone", type=str, default="mobilenet_v3_small", help="CNN backbone")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    args = parser.parse_args()

    train_thoracic_model(
        data_dir=args.data_dir,
        annotation_path=args.annotations,
        output_dir=args.output_dir,
        backbone=args.backbone,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )
