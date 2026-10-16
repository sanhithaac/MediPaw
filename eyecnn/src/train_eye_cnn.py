"""
Training Script for MediPaw Eye CNN Ocular Abnormality Classifier.

Features:
- PyTorch transfer learning with MobileNetV3-Small (default) or EfficientNet-B0
- Data augmentations applied strictly to training data:
    RandomHorizontalFlip, RandomRotation, ColorJitter, RandomAffine
- 224x224 input sizing and ImageNet normalization
- Cost-sensitive class-weighted Cross-Entropy Loss to handle class imbalance
- AdamW optimizer with cosine annealing learning rate scheduler
- Early stopping based on validation macro F1-score and validation loss
- Saves the best checkpoint, class mapping, and model hyperparameters in models/eye_cnn/
- Logs epoch metrics and history to outputs/training_history.csv
"""

import os
import sys
# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import time
import json
import random
import argparse
from pathlib import Path
from typing import Dict, Tuple, List, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from tqdm import tqdm

# Import EyeCNN model builder
from eye_model import build_eye_model


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def parse_args():
    parser = argparse.ArgumentParser(description="Train Eye CNN on cropped ocular dataset.")
    parser.add_argument("--data_dir", type=str, default="datasets/eye", help="Path to cropped dataset root containing train/valid/test")
    parser.add_argument("--output_dir", type=str, default="outputs", help="Directory for logs and metrics")
    parser.add_argument("--model_dir", type=str, default="models/eye_cnn", help="Directory to save checkpoints")
    parser.add_argument("--backbone", type=str, default="mobilenet_v3_small", choices=["mobilenet_v3_small", "efficientnet_b0"], help="Backbone model")
    parser.add_argument("--epochs", type=int, default=15, help="Maximum training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="DataLoader batch size")
    parser.add_argument("--lr", type=float, default=3e-4, help="Initial learning rate")
    parser.add_argument("--weight_decay", type=float, default=1e-4, help="Weight decay for optimizer")
    parser.add_argument("--dropout", type=float, default=0.2, help="Classifier dropout rate")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience (epochs without validation improvement)")
    parser.add_argument("--num_workers", type=int, default=0, help="DataLoader workers (default 0 for Windows compatibility)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--no_class_weights", action="store_true", help="Disable training class weights")
    return parser.parse_args()


def get_data_transforms() -> Tuple[transforms.Compose, transforms.Compose]:
    """
    Returns training and validation/test transformation pipelines.
    Input size is 224x224 with ImageNet standard normalization.
    """
    imagenet_mean = [0.485, 0.456, 0.406]
    imagenet_std = [0.229, 0.224, 0.225]

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
        transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),
        transforms.ToTensor(),
        transforms.Normalize(mean=imagenet_mean, std=imagenet_std)
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=imagenet_mean, std=imagenet_std)
    ])

    return train_transform, eval_transform


def compute_class_weights(dataset: datasets.ImageFolder, num_classes: int, device: torch.device) -> torch.Tensor:
    """
    Computes inverse-frequency class weights for cost-sensitive Cross-Entropy loss.
    """
    targets = [sample[1] for sample in dataset.samples]
    class_counts = np.bincount(targets, minlength=num_classes)
    total_samples = len(targets)
    weights = total_samples / (num_classes * class_counts.astype(np.float32))
    weight_tensor = torch.tensor(weights, dtype=torch.float32, device=device)
    print(f"Computed Class Weights: { {cls_idx: round(float(w), 4) for cls_idx, w in enumerate(weights)} }")
    return weight_tensor


def run_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: Optional[torch.optim.Optimizer],
    device: torch.device,
    is_training: bool = True
) -> Tuple[float, float, float, float, float]:
    """
    Executes a single epoch (training or validation).
    Returns (loss, accuracy, macro_precision, macro_recall, macro_f1).
    """
    if is_training:
        model.train()
    else:
        model.eval()

    running_loss = 0.0
    all_preds = []
    all_targets = []

    with torch.set_grad_enabled(is_training):
        for inputs, targets in dataloader:
            inputs = inputs.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            if is_training:
                optimizer.zero_grad()

            outputs = model(inputs)
            loss = criterion(outputs, targets)

            if is_training:
                loss.backward()
                optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            preds = torch.argmax(outputs, dim=1).detach().cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.cpu().numpy())

    total_samples = len(all_targets)
    epoch_loss = running_loss / total_samples

    acc = accuracy_score(all_targets, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_targets, all_preds, average="macro", zero_division=0
    )

    return epoch_loss, acc, precision, recall, f1


def main():
    args = parse_args()
    set_seed(args.seed)

    # Directories
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(base_dir, args.data_dir) if not os.path.isabs(args.data_dir) else args.data_dir
    output_dir = os.path.join(base_dir, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir
    model_dir = os.path.join(base_dir, args.model_dir) if not os.path.isabs(args.model_dir) else args.model_dir

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    print("=" * 70)
    print("MediPaw Eye CNN: Training Pipeline")
    print("=" * 70)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device:          {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'System CPU'})")
    print(f"Dataset Root:    {data_dir}")
    print(f"Backbone:        {args.backbone}")
    print(f"Batch Size:      {args.batch_size}")
    print(f"Learning Rate:   {args.lr}")
    print(f"Weight Decay:    {args.weight_decay}")
    print(f"Max Epochs:      {args.epochs}")
    print(f"Early Stopping:  {args.patience} epochs patience")

    # Data loaders
    train_transform, eval_transform = get_data_transforms()
    train_path = os.path.join(data_dir, "train")
    valid_path = os.path.join(data_dir, "valid")

    if not os.path.exists(train_path) or not os.path.exists(valid_path):
        raise FileNotFoundError(f"Prepared dataset splits not found in {data_dir}. Run prepare_eye_dataset.py first.")

    train_dataset = datasets.ImageFolder(root=train_path, transform=train_transform)
    valid_dataset = datasets.ImageFolder(root=valid_path, transform=eval_transform)

    class_names = train_dataset.classes
    num_classes = len(class_names)
    print(f"Verified Classes ({num_classes}): {class_names}")
    print(f"Training Samples:   {len(train_dataset)}")
    print(f"Validation Samples: {len(valid_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda")
    )
    valid_loader = DataLoader(
        valid_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda")
    )

    # Class-to-index mapping
    class_to_idx = train_dataset.class_to_idx
    idx_to_class = {v: k for k, v in class_to_idx.items()}

    # Save class mapping
    class_map_path = os.path.join(model_dir, "class_mapping.json")
    with open(class_map_path, "w", encoding="utf-8") as f:
        json.dump({
            "classes": class_names,
            "class_to_idx": class_to_idx,
            "idx_to_class": idx_to_class,
            "num_classes": num_classes
        }, f, indent=2)

    # Loss Criterion
    if not args.no_class_weights:
        weights = compute_class_weights(train_dataset, num_classes, device)
        criterion = nn.CrossEntropyLoss(weight=weights)
    else:
        criterion = nn.CrossEntropyLoss()

    # Model
    model = build_eye_model(
        num_classes=num_classes,
        backbone_name=args.backbone,
        pretrained=True,
        dropout_rate=args.dropout,
        device=device
    )

    # Optimizer & Scheduler
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.epochs,
        eta_min=1e-6
    )

    # Training Loop with Early Stopping
    best_val_f1 = -1.0
    best_val_loss = float("inf")
    best_epoch = 0
    patience_counter = 0
    best_model_path = os.path.join(model_dir, "best_eye_model.pth")
    history: List[Dict[str, Any]] = []

    start_time = time.time()

    print("\nStarting training loop...")
    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()

        train_loss, train_acc, train_prec, train_rec, train_f1 = run_epoch(
            model, train_loader, criterion, optimizer, device, is_training=True
        )

        val_loss, val_acc, val_prec, val_rec, val_f1 = run_epoch(
            model, valid_loader, criterion, optimizer=None, device=device, is_training=False
        )

        scheduler.step()
        epoch_duration = time.time() - epoch_start
        current_lr = scheduler.get_last_lr()[0]

        print(
            f"Epoch [{epoch:02d}/{args.epochs:02d}] "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} F1: {train_f1:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} F1: {val_f1:.4f} | "
            f"LR: {current_lr:.6f} ({epoch_duration:.1f}s)"
        )

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "train_precision": train_prec,
            "train_recall": train_rec,
            "train_f1": train_f1,
            "val_loss": val_loss,
            "val_accuracy": val_acc,
            "val_precision": val_prec,
            "val_recall": val_rec,
            "val_f1": val_f1,
            "lr": current_lr,
            "duration_sec": epoch_duration
        })

        # Early stopping condition based on val_f1
        if val_f1 > best_val_f1 or (val_f1 == best_val_f1 and val_loss < best_val_loss):
            best_val_f1 = val_f1
            best_val_loss = val_loss
            best_epoch = epoch
            patience_counter = 0

            # Save checkpoint
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_f1": val_f1,
                "val_loss": val_loss,
                "val_accuracy": val_acc,
                "backbone": args.backbone,
                "feature_dim": model.feature_dim,
                "class_names": class_names,
                "class_to_idx": class_to_idx
            }, best_model_path)
            print(f"  --> Saved new best checkpoint at epoch {epoch} (Val F1: {val_f1:.4f}, Val Acc: {val_acc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"\nEarly stopping triggered after {epoch} epochs (No improvement for {args.patience} epochs).")
                break

    total_training_time = time.time() - start_time
    print(f"\nTraining completed in {total_training_time / 60:.2f} minutes.")
    print(f"Best checkpoint at epoch {best_epoch} with Validation F1: {best_val_f1:.4f}, Val Loss: {best_val_loss:.4f}")

    # Save training history CSV
    df_history = pd.DataFrame(history)
    history_csv_path = os.path.join(output_dir, "training_history.csv")
    df_history.to_csv(history_csv_path, index=False)
    print(f"Saved training history to {history_csv_path}")

    # Save preprocessing and model config
    config_data = {
        "model_architecture": "EyeCNN",
        "backbone": args.backbone,
        "feature_dim": model.feature_dim,
        "num_classes": num_classes,
        "class_names": class_names,
        "class_to_idx": class_to_idx,
        "input_resolution": [224, 224],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        },
        "training_hyperparameters": {
            "epochs_trained": len(history),
            "best_epoch": best_epoch,
            "best_val_f1": best_val_f1,
            "best_val_loss": best_val_loss,
            "batch_size": args.batch_size,
            "initial_lr": args.lr,
            "weight_decay": args.weight_decay,
            "dropout": args.dropout,
            "seed": args.seed,
            "total_time_seconds": round(total_training_time, 2)
        },
        "downstream_vit_integration": {
            "feature_tensor_name": "intermediate_pooled_features",
            "feature_dimension": model.feature_dim,
            "how_to_extract": "call model.forward_features(tensor_224x224) or model.forward_with_features(tensor_224x224)[1]"
        }
    }

    config_path = os.path.join(model_dir, "model_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    print(f"Saved model configuration to {config_path}")


if __name__ == "__main__":
    main()
