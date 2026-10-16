"""
Evaluation and Metrics Generation Script for MediPaw Eye CNN Classifier.

Evaluates the best checkpoint on the held-out test dataset:
- Computes overall Accuracy, Macro Precision, Recall, and F1-Score
- Computes Per-Class Precision, Recall, F1-Score, and Support counts
- Generates and plots the Confusion Matrix (normalized & raw)
- Plots training and validation loss/metric curves from training_history.csv
- Visualizes sample test predictions with true/predicted labels and confidence
- Saves all artifacts cleanly in outputs/:
    - confusion_matrix.png, confusion_matrix.csv
    - classification_report.txt
    - training_curves.png
    - sample_predictions.png
    - test_evaluation_summary.json
"""

import os
import sys
# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)

# Import EyeCNN builder
from eye_model import build_eye_model


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate best Eye CNN model on test split.")
    parser.add_argument("--data_dir", type=str, default="datasets/eye", help="Path to cropped dataset root")
    parser.add_argument("--model_path", type=str, default="models/eye_cnn/best_eye_model.pth", help="Path to trained checkpoint")
    parser.add_argument("--config_path", type=str, default="models/eye_cnn/model_config.json", help="Path to model config")
    parser.add_argument("--history_csv", type=str, default="outputs/training_history.csv", help="Path to training history CSV")
    parser.add_argument("--output_dir", type=str, default="outputs", help="Directory to save evaluation artifacts")
    parser.add_argument("--batch_size", type=int, default=32, help="Evaluation batch size")
    parser.add_argument("--num_samples_plot", type=int, default=8, help="Number of test samples to display in collage")
    return parser.parse_args()


def plot_training_curves(history_csv: str, output_path: str):
    """Plots training and validation loss and F1-score across epochs."""
    if not os.path.exists(history_csv):
        print(f"Warning: History file {history_csv} not found. Skipping curve plotting.")
        return

    df = pd.read_csv(history_csv)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    sns.set_theme(style="whitegrid")

    epochs = df["epoch"]

    # 1. Loss curves
    ax1.plot(epochs, df["train_loss"], marker="o", label="Train Loss", color="#1f77b4", linewidth=2)
    ax1.plot(epochs, df["val_loss"], marker="s", label="Val Loss", color="#d62728", linewidth=2)
    ax1.set_title("Loss Trajectory per Epoch", fontsize=13, weight="bold")
    ax1.set_xlabel("Epoch", fontsize=11)
    ax1.set_ylabel("Cross-Entropy Loss", fontsize=11)
    ax1.legend(loc="upper right")

    # 2. Macro F1 & Accuracy curves
    ax2.plot(epochs, df["train_f1"], marker="o", label="Train Macro F1", color="#2ca02c", linewidth=2)
    ax2.plot(epochs, df["val_f1"], marker="s", label="Val Macro F1", color="#ff7f0e", linewidth=2)
    ax2.plot(epochs, df["val_accuracy"], marker="^", linestyle="--", label="Val Accuracy", color="#9467bd", linewidth=1.5)
    ax2.set_title("Validation Metric Trajectory", fontsize=13, weight="bold")
    ax2.set_xlabel("Epoch", fontsize=11)
    ax2.set_ylabel("Score [0.0 - 1.0]", fontsize=11)
    ax2.legend(loc="lower right")

    plt.suptitle("MediPaw Eye CNN: Training and Validation Dynamics", fontsize=15, weight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved training curves plot to: {output_path}")


def plot_confusion_matrix(cm: np.ndarray, class_names: List[str], output_path: str, csv_path: str):
    """Plots normalized confusion matrix heatmap and saves CSV table."""
    # Save CSV
    df_cm = pd.DataFrame(cm, index=class_names, columns=class_names)
    df_cm.to_csv(csv_path)

    # Plot normalized heatmap
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
    sns.heatmap(
        cm_norm,
        annot=True,
        fmt=".2%",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=True,
        ax=ax,
        annot_kws={"size": 11, "weight": "bold"}
    )

    ax.set_title("MediPaw Eye CNN: Test Set Confusion Matrix (Normalized)", fontsize=13, weight="bold", pad=12)
    ax.set_xlabel("Predicted Class", fontsize=11, weight="bold")
    ax.set_ylabel("Ground Truth Class", fontsize=11, weight="bold")
    plt.xticks(rotation=25, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved confusion matrix plot to: {output_path}")
    print(f"Saved confusion matrix CSV to:  {csv_path}")


def plot_sample_predictions(samples: List[Dict[str, Any]], output_path: str):
    """Creates a visual grid of test predictions with actual and predicted labels."""
    num_samples = len(samples)
    cols = 4
    rows = int(np.ceil(num_samples / cols))

    fig, axes = plt.subplots(rows, cols, figsize=(16, 4 * rows), dpi=300)
    axes = np.array(axes).reshape(-1)

    for idx, sample in enumerate(samples):
        ax = axes[idx]
        img = Image.open(sample["img_path"]).convert("RGB")
        ax.imshow(img)

        correct = (sample["true_class"] == sample["pred_class"])
        title_color = "#2e7d32" if correct else "#c62828"
        status = "CORRECT" if correct else "MISCLASSIFIED"

        title_text = (
            f"True: {sample['true_class']}\n"
            f"Pred: {sample['pred_class']} ({sample['confidence']:.1%})\n"
            f"[{status}]"
        )
        ax.set_title(title_text, fontsize=10, weight="bold", color=title_color)
        ax.axis("off")

    # Turn off unused subplots
    for idx in range(num_samples, len(axes)):
        axes[idx].axis("off")

    plt.suptitle("MediPaw Eye CNN: Sample Test Predictions & Confidence", fontsize=15, weight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved sample test predictions to: {output_path}")


def main():
    args = parse_args()
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(base_dir, args.data_dir) if not os.path.isabs(args.data_dir) else args.data_dir
    model_path = os.path.join(base_dir, args.model_path) if not os.path.isabs(args.model_path) else args.model_path
    output_dir = os.path.join(base_dir, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir
    history_csv = os.path.join(base_dir, args.history_csv) if not os.path.isabs(args.history_csv) else args.history_csv

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("MediPaw Eye CNN: Model Evaluation & Test Benchmarking")
    print("=" * 70)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Checkpoint not found at {model_path}. Train the model first.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading checkpoint: {model_path}")
    checkpoint = torch.load(model_path, map_location=device)

    class_names = checkpoint.get("class_names", [])
    num_classes = len(class_names)
    backbone = checkpoint.get("backbone", "mobilenet_v3_small")
    best_epoch = checkpoint.get("epoch", "N/A")
    val_f1 = checkpoint.get("val_f1", 0.0)

    print(f"Loaded Backbone:     {backbone}")
    print(f"Best Training Epoch: {best_epoch} (Val Macro F1: {val_f1:.4f})")
    print(f"Evaluated Classes:   {class_names}")

    # Build model and load weights
    model = build_eye_model(
        num_classes=num_classes,
        backbone_name=backbone,
        pretrained=False,
        device=device
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Test transforms and loader
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    test_path = os.path.join(data_dir, "test")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test split directory not found at {test_path}")

    test_dataset = datasets.ImageFolder(root=test_path, transform=eval_transform)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)

    print(f"\nEvaluating on held-out test split ({len(test_dataset)} samples)...")

    all_preds = []
    all_targets = []
    all_probs = []

    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs = inputs.to(device)
            logits = model(inputs)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            all_preds.extend(preds)
            all_targets.extend(targets.numpy())
            all_probs.extend(probs)

    all_targets = np.array(all_targets)
    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)

    # 1. Overall Metrics
    accuracy = accuracy_score(all_targets, all_preds)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        all_targets, all_preds, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        all_targets, all_preds, average="weighted", zero_division=0
    )

    # 2. Per-class metrics
    per_class_p, per_class_r, per_class_f1, support = precision_recall_fscore_support(
        all_targets, all_preds, labels=range(num_classes), zero_division=0
    )

    report_str = classification_report(
        all_targets,
        all_preds,
        target_names=class_names,
        digits=4,
        zero_division=0
    )

    print("\n" + "=" * 70)
    print("Test Set Classification Report")
    print("=" * 70)
    print(report_str)

    # Save classification report text
    report_path = os.path.join(output_dir, "classification_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("MediPaw Eye CNN - Held-Out Test Set Classification Report\n")
        f.write("=" * 65 + "\n")
        f.write(f"Backbone: {backbone} | Checkpoint Epoch: {best_epoch}\n\n")
        f.write(report_str)
    print(f"Saved classification report to: {report_path}")

    # 3. Confusion Matrix
    cm = confusion_matrix(all_targets, all_preds, labels=range(num_classes))
    cm_plot_path = os.path.join(output_dir, "confusion_matrix.png")
    cm_csv_path = os.path.join(output_dir, "confusion_matrix.csv")
    plot_confusion_matrix(cm, class_names, cm_plot_path, cm_csv_path)

    # 4. Training and validation curves
    curves_plot_path = os.path.join(output_dir, "training_curves.png")
    plot_training_curves(history_csv, curves_plot_path)

    # 5. Visual sample predictions
    sample_records = []
    # Pick diverse samples (e.g. from each class + some misclassified if available)
    rng = np.random.RandomState(42)
    sample_indices = rng.choice(len(test_dataset), size=min(args.num_samples_plot, len(test_dataset)), replace=False)
    for idx in sample_indices:
        img_path, true_lbl = test_dataset.samples[idx]
        pred_lbl = all_preds[idx]
        conf = float(all_probs[idx][pred_lbl])
        sample_records.append({
            "img_path": img_path,
            "true_class": class_names[true_lbl],
            "pred_class": class_names[pred_lbl],
            "confidence": conf
        })

    sample_plot_path = os.path.join(output_dir, "sample_predictions.png")
    plot_sample_predictions(sample_records, sample_plot_path)

    # 6. Save comprehensive JSON summary
    summary_data = {
        "model_architecture": "EyeCNN",
        "backbone": backbone,
        "best_epoch": int(best_epoch) if isinstance(best_epoch, (int, np.integer)) else best_epoch,
        "test_metrics": {
            "test_samples": int(len(test_dataset)),
            "accuracy": round(float(accuracy), 4),
            "macro_precision": round(float(macro_p), 4),
            "macro_recall": round(float(macro_r), 4),
            "macro_f1": round(float(macro_f1), 4),
            "weighted_precision": round(float(weighted_p), 4),
            "weighted_recall": round(float(weighted_r), 4),
            "weighted_f1": round(float(weighted_f1), 4)
        },
        "per_class_metrics": {
            class_names[i]: {
                "precision": round(float(per_class_p[i]), 4),
                "recall": round(float(per_class_r[i]), 4),
                "f1_score": round(float(per_class_f1[i]), 4),
                "support": int(support[i])
            }
            for i in range(num_classes)
        },
        "confusion_matrix": cm.tolist(),
        "generated_artifacts": {
            "classification_report": "outputs/classification_report.txt",
            "confusion_matrix_plot": "outputs/confusion_matrix.png",
            "confusion_matrix_csv": "outputs/confusion_matrix.csv",
            "training_curves_plot": "outputs/training_curves.png",
            "sample_predictions_plot": "outputs/sample_predictions.png"
        }
    }

    test_json_path = os.path.join(output_dir, "test_evaluation_summary.json")
    with open(test_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved test metrics JSON summary to: {test_json_path}")

    print("\n" + "=" * 70)
    print("Test Evaluation Complete.")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Macro F1:  {macro_f1:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
