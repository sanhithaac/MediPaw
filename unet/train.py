"""
=============================================================================
MEDIPAW MODULE 4: U-Net — Training Script
=============================================================================

IMPORTANT: Real segmentation masks are required for valid training.
If you train without real masks, the metrics are NOT meaningful.
See dataset_loader.py for full explanation.

Usage (PowerShell)
------------------
  cd MediPaw_Code
  python unet/train.py --images_dir skincnn/yolo_canine_wounds/train/images
                       --labels_dir skincnn/yolo_canine_wounds/train/labels
                       --val_images skincnn/yolo_canine_wounds/val/images
                       --val_labels skincnn/yolo_canine_wounds/val/labels
                       --epochs 30 --batch 4 --img_size 256

  # If you have real masks:
  python unet/train.py --images_dir path/to/train/images
                       --mask_dir   path/to/train/masks
                       --val_images path/to/val/images
                       --val_masks  path/to/val/masks
                       --epochs 50 --batch 8

Checkpoints are saved to:  unet/checkpoints/best_model.pt
Training log:              unet/checkpoints/training_history.json
=============================================================================
"""

import argparse
import json
import os
import warnings
from pathlib import Path

import torch
import torch.optim as optim
from torch.utils.data import DataLoader

from dataset_loader import WoundSegmentationDataset
from evaluate_metrics import compute_metrics
from losses import CombinedLoss
from model_architecture import UNet


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_device() -> torch.device:
    if torch.cuda.is_available():
        dev = torch.device("cuda")
        print(f"[GPU] Using: {torch.cuda.get_device_name(0)}")
    else:
        dev = torch.device("cpu")
        print("[CPU] No GPU found; training on CPU (will be slow for large datasets).")
    return dev


def _save_checkpoint(state: dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(state, path)
    print(f"  [Checkpoint] Saved → {path}")


def _run_epoch(
    model: UNet,
    loader: DataLoader,
    criterion: CombinedLoss,
    optimiser: optim.Optimizer | None,
    device: torch.device,
    training: bool,
) -> tuple[float, dict]:
    """Run one train or validation epoch. Returns (avg_loss, metrics_dict)."""
    model.train(training)
    total_loss = 0.0
    all_preds, all_targets = [], []

    ctx = torch.enable_grad() if training else torch.no_grad()
    with ctx:
        for images, masks in loader:
            images = images.to(device)
            masks  = masks.to(device)

            logits = model(images)
            loss   = criterion(logits, masks)

            if training:
                optimiser.zero_grad()
                loss.backward()
                optimiser.step()

            total_loss += loss.item()

            preds = (torch.sigmoid(logits) >= 0.5).float()
            all_preds.append(preds.cpu())
            all_targets.append(masks.cpu())

    avg_loss = total_loss / len(loader)
    metrics  = compute_metrics(
        torch.cat(all_preds, 0), torch.cat(all_targets, 0)
    )
    return avg_loss, metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def train(args: argparse.Namespace):
    device = _get_device()

    # ---- Datasets --------------------------------------------------------
    print("\n[Loading datasets...]")
    train_ds = WoundSegmentationDataset(
        images_dir=args.images_dir,
        labels_dir=args.labels_dir,
        mask_dir=args.mask_dir,
        img_size=args.img_size,
        augment=True,
    )

    val_mask_dir = args.val_masks if args.val_masks else None
    val_lbl_dir  = args.val_labels if args.val_labels else None
    val_ds = WoundSegmentationDataset(
        images_dir=args.val_images,
        labels_dir=val_lbl_dir,
        mask_dir=val_mask_dir,
        img_size=args.img_size,
        augment=False,
    )

    train_loader = DataLoader(
        train_ds, batch_size=args.batch, shuffle=True,
        num_workers=0, pin_memory=torch.cuda.is_available()
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch, shuffle=False,
        num_workers=0, pin_memory=torch.cuda.is_available()
    )

    print(f"  Train samples : {len(train_ds)}")
    print(f"  Val   samples : {len(val_ds)}")

    # ---- Model -----------------------------------------------------------
    model = UNet(in_channels=3, base_filters=args.base_filters).to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n[Model] U-Net — {total_params:,} trainable parameters")

    # ---- Loss and optimiser ----------------------------------------------
    criterion = CombinedLoss(bce_weight=0.5, dice_weight=0.5)
    optimiser = optim.AdamW(model.parameters(), lr=args.lr,
                             weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimiser, mode="min", factor=0.5, patience=5, verbose=True
    )

    # ---- Training loop ---------------------------------------------------
    checkpoint_path = "unet/checkpoints/best_model.pt"
    history_path    = "unet/checkpoints/training_history.json"
    os.makedirs("unet/checkpoints", exist_ok=True)

    best_val_dice = -1.0
    history: list[dict] = []

    print("\n" + "=" * 72)
    print(f"  Training for {args.epochs} epoch(s)  |  img_size={args.img_size}"
          f"  batch={args.batch}  lr={args.lr}")
    print("=" * 72)

    for epoch in range(1, args.epochs + 1):
        train_loss, train_metrics = _run_epoch(
            model, train_loader, criterion, optimiser, device, training=True
        )
        val_loss, val_metrics = _run_epoch(
            model, val_loader, criterion, None, device, training=False
        )

        scheduler.step(val_loss)

        val_dice = val_metrics["dice"]
        print(
            f"  Epoch {epoch:03d}/{args.epochs:03d} | "
            f"Train loss={train_loss:.4f}  dice={train_metrics['dice']:.4f} | "
            f"Val loss={val_loss:.4f}  dice={val_dice:.4f}  "
            f"iou={val_metrics['iou']:.4f}"
        )

        row = {
            "epoch": epoch,
            "train_loss": round(train_loss, 5),
            "val_loss":   round(val_loss,   5),
            "train_dice": round(train_metrics["dice"], 5),
            "val_dice":   round(val_metrics["dice"],   5),
            "val_iou":    round(val_metrics["iou"],    5),
            "val_prec":   round(val_metrics["precision"], 5),
            "val_recall": round(val_metrics["recall"],    5),
        }
        history.append(row)

        # Save best checkpoint
        if val_dice > best_val_dice:
            best_val_dice = val_dice
            _save_checkpoint(
                {
                    "epoch":    epoch,
                    "state_dict": model.state_dict(),
                    "val_dice": val_dice,
                    "val_iou":  val_metrics["iou"],
                    "args":     vars(args),
                },
                checkpoint_path,
            )

    # ---- Save history ----------------------------------------------------
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\n[Done] Best val Dice = {best_val_dice:.4f}")
    print(f"       Checkpoint  → {checkpoint_path}")
    print(f"       History     → {history_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train MediPaw U-Net wound segmentation")

    # Data
    p.add_argument("--images_dir",  required=True,
                   help="Path to training images directory")
    p.add_argument("--labels_dir",  default=None,
                   help="Path to YOLO label .txt files (for synthetic mask fallback)")
    p.add_argument("--mask_dir",    default=None,
                   help="Path to real binary PNG mask directory (preferred)")
    p.add_argument("--val_images",  required=True,
                   help="Path to validation images directory")
    p.add_argument("--val_labels",  default=None,
                   help="Path to YOLO label .txt files for validation")
    p.add_argument("--val_masks",   default=None,
                   help="Path to real binary PNG mask directory for validation")

    # Model
    p.add_argument("--base_filters", type=int, default=32,
                   help="Base filter count for U-Net (doubles each level)")
    p.add_argument("--img_size",     type=int, default=256,
                   help="Square resize target (must be divisible by 16)")

    # Training
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch",  type=int, default=4)
    p.add_argument("--lr",     type=float, default=1e-3)

    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)
