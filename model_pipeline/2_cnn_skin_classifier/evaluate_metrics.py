import os
import torch
import numpy as np
import argparse

from dataset_loader import get_dataloaders
from model_architecture import MediPawSkinClassifier

def evaluate_model(backbone="efficientnet_v2_s", filter_duplicates=True):
    print("="*85)
    print("        MEDIPAW REVIEW 2: UNTOUCHED TEST SET CLINICAL EVALUATION MATRIX        ")
    print("="*85)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Evaluation] Execution Device: {device}")
    print(f"[Evaluation] Active Model Backbone: {backbone}\n")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset_dir = os.path.join(base_dir, "datasets", "cnn1_denoised_split")
    weights_path = os.path.join(os.path.dirname(__file__), "best_cnn1_weights.pth")

    if not os.path.exists(weights_path):
        print(f"[ERROR] Trained model weights missing at: {weights_path}")
        print("Please run train_cnn.py to conclude model training before running evaluation metrics.")
        return

    _, _, test_loader, classes = get_dataloaders(dataset_dir, batch_size=32, num_workers=0, filter_duplicates=filter_duplicates)
    num_classes = len(classes)

    model = MediPawSkinClassifier(num_classes=num_classes, backbone_type=backbone).to(device)
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()

    print("\n[INFO] Model checkpoint loaded successfully. Running evaluation across untouched Test partition...")

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    conf_matrix = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(all_targets, all_preds):
        conf_matrix[t][p] += 1

    print("\n" + "="*85)
    print("1. CONFUSION MATRIX (Predicted vs. Actual Ground Truth)")
    print("="*85)
    header_cols = " | ".join([f"{c[:6]:>6}" for c in classes])
    print(f"{'Actual vs Pred':<22} | {header_cols}")
    print("-" * 85)
    for i, row in enumerate(conf_matrix):
        row_cols = " | ".join([f"{val:>6}" for val in row])
        print(f"{classes[i]:<22} | {row_cols}")
    print("-" * 85)

    print("\n" + "="*85)
    print("2. CLINICAL RELIABILITY AUDIT: PRECISION, RECALL & F1-SCORE")
    print("="*85)
    print(f"{'Class Name':<28} | {'Precision':<12} | {'Recall':<12} | {'F1-Score':<12} | {'Sample Count':<12}")
    print("-" * 85)

    precisions, recalls, f1s = [], [], []
    
    for i, cls_name in enumerate(classes):
        tp = conf_matrix[i][i]
        fp = np.sum(conf_matrix[:, i]) - tp
        fn = np.sum(conf_matrix[i, :]) - tp

        prec = float(tp) / float(max(tp + fp, 1))
        rec = float(tp) / float(max(tp + fn, 1))
        f1 = (2.0 * prec * rec) / float(max(prec + rec, 1e-5))

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

        count = np.sum(conf_matrix[i, :])
        print(f"{cls_name:<28} | {prec*100:<11.2f}% | {rec*100:<11.2f}% | {f1*100:<11.2f}% | {count:<12}")

    print("-" * 85)
    macro_prec = np.mean(precisions) * 100
    macro_rec = np.mean(recalls) * 100
    macro_f1 = np.mean(f1s) * 100
    total_acc = (np.trace(conf_matrix) / max(np.sum(conf_matrix), 1)) * 100

    print(f"{'MACRO AVERAGE':<28} | {macro_prec:<11.2f}% | {macro_rec:<11.2f}% | {macro_f1:<11.2f}% | {len(all_targets):<12}")
    print("-" * 85)
    print(f"\n[KEY METRIC] Total Test Partition Accuracy: {total_acc:.2f}%")
    print("="*85)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediPaw Review 2 Evaluation Suite")
    parser.add_argument("--backbone", type=str, default="efficientnet_v2_s", help="Model backbone architecture")
    parser.add_argument("--filter_dups", action="store_true", default=True, help="Toggle MD5 duplicate filtering (default True)")
    args = parser.parse_args()
    
    evaluate_model(backbone=args.backbone, filter_duplicates=args.filter_dups)
