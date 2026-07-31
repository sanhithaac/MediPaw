"""
=====================================================================================
            MEDIPAW REVIEW 2: HIGH-ACCURACY GOOGLE COLAB TRAINING SUITE
=====================================================================================
Features:
 - 2-Stage Transfer Learning Warmup (Freezes backbone for initial 3 epochs)
 - Square-Root Damping on Class Weights (Caps max weight at ~2.8x instead of 8.0x)
 - Gentle AdamW Fine-Tuning (lr=0.0001) with Cosine Annealing & Early Stopping

Upload this updated file (colab_trainer.py) into your Colab workspace and run:

  !python colab_trainer.py --data_dir ./data/cnn1_denoised_split --epochs 20 --batch 64
"""

import os
import glob
import time
import json
import hashlib
import math
import argparse
from PIL import Image
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision.models as models

# =====================================================================
# 1. REAL-TIME DEDUPLICATED DATALOADER MODULE
# =====================================================================
def compute_md5(image_path):
    try:
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

class ColabSkinDataset(Dataset):
    def __init__(self, root_dir, split="train", transform=None, ignore_hashes=None):
        self.split_dir = os.path.join(root_dir, split)
        self.transform = transform
        self.image_paths = []
        self.labels = []
        self.seen_hashes = set() if ignore_hashes is None else ignore_hashes
        
        if not os.path.exists(self.split_dir):
            raise FileNotFoundError(f"[ERROR] Split path missing: {self.split_dir}")

        self.classes = sorted([d for d in os.listdir(self.split_dir) if os.path.isdir(os.path.join(self.split_dir, d))])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}

        print(f"[DataLoader: {split.upper()}] Indexing split...")
        skipped = 0
        for cls_name in self.classes:
            cls_idx = self.class_to_idx[cls_name]
            cls_dir = os.path.join(self.split_dir, cls_name)
            files = []
            for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
                files.extend(glob.glob(os.path.join(cls_dir, ext)))
            
            for f in sorted(files):
                f_hash = compute_md5(f)
                if not f_hash or f_hash in self.seen_hashes:
                    skipped += 1
                    continue
                self.seen_hashes.add(f_hash)
                self.image_paths.append(f)
                self.labels.append(cls_idx)
        print(f"[DataLoader: {split.upper()}] Loaded {len(self.image_paths)} valid images (Filtered {skipped} duplicates via MD5).")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        try:
            image = Image.open(self.image_paths[idx]).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224), (128, 128, 128))
        if self.transform:
            image = self.transform(image)
        return image, self.labels[idx]

# =====================================================================
# 2. RESNET-50 VETERINARY TRIAGE ARCHITECTURE MODULE
# =====================================================================
class ColabSkinClassifier(nn.Module):
    def __init__(self, num_classes=6, dropout_rate=0.5):
        super(ColabSkinClassifier, self).__init__()
        weights = models.ResNet50_Weights.DEFAULT
        self.backbone = models.resnet50(weights=weights)
        in_features = self.backbone.fc.in_features
        
        # Replace dense head with Review 2 justified regularized head
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512, momentum=0.99, eps=1e-5),
            nn.LeakyReLU(negative_slope=0.01, inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(512, num_classes)
        )
        for m in self.backbone.fc.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='leaky_relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1.0)
                nn.init.constant_(m.bias, 0.0)

    def freeze_backbone(self, freeze=True):
        """Toggles freezing on interior convolutional layers for 2-Stage Warmup."""
        for name, param in self.backbone.named_parameters():
            if "fc" not in name: # Do not freeze our custom diagnostic head
                param.requires_grad = not freeze

    def forward(self, x):
        return self.backbone(x)

# =====================================================================
# 3. TRAINING & TEST EVALUATION ENGINE
# =====================================================================
def run_suite(data_dir, epochs=20, batch_size=64, lr=0.0001):
    print("="*85)
    print("    MEDIPAW REVIEW 2: HIGH-ACCURACY 2-STAGE COLAB T4 TRAINING & EVALUATION    ")
    print("="*85)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Hardware] Active Acceleration Device: {device} ({'Colab GPU Supported 🚀' if device.type=='cuda' else 'CPU Mode'})")

    custom_norm = transforms.Normalize(mean=[0.5263, 0.4534, 0.4237], std=[0.2104, 0.1994, 0.1972])
    
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        custom_norm
    ])
    eval_tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), custom_norm])

    workers = 2 if device.type == "cuda" else 0
    
    t_ds = ColabSkinDataset(data_dir, "train", transform=train_tf)
    v_ds = ColabSkinDataset(data_dir, "val", transform=eval_tf, ignore_hashes=t_ds.seen_hashes.copy())
    test_ds = ColabSkinDataset(data_dir, "test", transform=eval_tf, ignore_hashes=t_ds.seen_hashes.union(v_ds.seen_hashes))

    train_loader = DataLoader(t_ds, batch_size=batch_size, shuffle=True, num_workers=workers, pin_memory=True)
    val_loader = DataLoader(v_ds, batch_size=batch_size, shuffle=False, num_workers=workers, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=workers, pin_memory=True)

    classes = t_ds.classes
    num_classes = len(classes)
    model = ColabSkinClassifier(num_classes=num_classes, dropout_rate=0.4).to(device)

    # Square-Root Damping: Maps [1.15, 0.74, 0.88, 7.99, 0.93, 0.68] -> [1.07, 0.86, 0.94, 2.83, 0.97, 0.83]
    raw_weights = [1.1515, 0.7463, 0.8856, 7.9939, 0.9321, 0.6828]
    damped_weights = [round(math.sqrt(w), 4) for w in raw_weights]
    print(f"\n[Loss Weighting] Applied Square-Root Damping to prevent minority class dominating predictions:")
    print(f" -> Damped Weights Loaded: {damped_weights}")

    class_weights = torch.tensor(damped_weights[:num_classes], dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
    
    best_acc = 0.0
    patience_cnt = 0
    weights_path = "./best_cnn1_weights.pth"
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    print("\n" + "-" * 85)
    print(f"{'Epoch':<8} | {'Phase Status':<15} | {'Train Loss':<12} | {'Val Loss':<12} | {'Val Acc':<12} | {'Time (s)':<8}")
    print("-" * 85)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        
        # --- 2-STAGE WARMUP CONTROL ---
        if epoch <= 3:
            model.freeze_backbone(freeze=True)
            phase_name = "Stage1-Warmup"
            if epoch == 1:
                print(f"[Stage 1] Freezing ResNet backbone for first 3 epochs to stabilize new classifier head...")
        elif epoch == 4:
            model.freeze_backbone(freeze=False)
            phase_name = "Stage2-Finetune"
            print(f"\n[Stage 2] Unfreezing ResNet backbone! Entering full-network deep feature fine-tuning...")
        else:
            phase_name = "Stage2-Finetune"

        model.train()
        t_loss, t_corr, t_tot = 0.0, 0, 0
        
        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, lbls)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            t_loss += loss.item() * imgs.size(0)
            _, prd = torch.max(out, 1)
            t_corr += (prd == lbls).sum().item()
            t_tot += lbls.size(0)

        scheduler.step()
        
        model.eval()
        v_loss, v_corr, v_tot = 0.0, 0, 0
        with torch.no_grad():
            for imgs, lbls in val_loader:
                imgs, lbls = imgs.to(device), lbls.to(device)
                out = model(imgs)
                loss = criterion(out, lbls)
                v_loss += loss.item() * imgs.size(0)
                _, prd = torch.max(out, 1)
                v_corr += (prd == lbls).sum().item()
                v_tot += lbls.size(0)

        e_tl = t_loss / max(t_tot, 1)
        e_ta = (t_corr / max(t_tot, 1)) * 100
        e_vl = v_loss / max(v_tot, 1)
        e_va = (v_corr / max(v_tot, 1)) * 100
        dur = time.time() - t0

        history["train_loss"].append(round(e_tl, 4))
        history["val_loss"].append(round(e_vl, 4))
        history["train_acc"].append(round(e_ta, 2))
        history["val_acc"].append(round(e_va, 2))

        print(f"{epoch:02d}/{epochs:02d} | {phase_name:<15} | {e_tl:<12.4f} | {e_vl:<12.4f} | {e_va:<11.2f}% | {dur:<8.1f}")
        
        if e_va > best_acc:
            best_acc = e_va
            patience_cnt = 0
            torch.save(model.state_dict(), weights_path)
        else:
            if epoch >= 4: # Only start counting patience after unfreezing
                patience_cnt += 1
            if patience_cnt >= 8:
                print("\n[EARLY STOPPING] Triggered after 8 consecutive plateau epochs.")
                break

    with open("./colab_training_history.json", "w") as f:
        json.dump(history, f, indent=4)
    print(f"\n[SUCCESS] Training Complete! Best Validation Accuracy achieved: {best_acc:.2f}%")
    print(f"[SAVED] Optimal Model Checkpoint stored at: {weights_path}")

    # =================================================================
    # 4. UNTOUCHED TEST SET EVALUATION MATRIX
    # =================================================================
    print("\n" + "="*85)
    print("            EXECUTING FINAL EVALUATION ON UNTOUCHED 15% TEST PARTITION            ")
    print("="*85)
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()

    all_p, all_t = [], []
    with torch.no_grad():
        for imgs, lbls in test_loader:
            out = model(imgs.to(device))
            _, p = torch.max(out, 1)
            all_p.extend(p.cpu().numpy())
            all_t.extend(lbls.numpy())

    all_p, all_t = np.array(all_p), np.array(all_t)
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t_val, p_val in zip(all_t, all_p):
        cm[t_val][p_val] += 1

    print("\n[CONFUSION MATRIX]:")
    print(f"{'Actual vs Pred':<22} | " + " | ".join([f"{c[:6]:>6}" for c in classes]))
    print("-" * 85)
    for i, row in enumerate(cm):
        print(f"{classes[i]:<22} | " + " | ".join([f"{val:>6}" for val in row]))
    print("-" * 85)

    print("\n[CLINICAL RELIABILITY TABLE]:")
    print(f"{'Class Name':<28} | {'Precision':<12} | {'Recall':<12} | {'F1-Score':<12} | {'Count':<8}")
    print("-" * 85)
    precs, recs, f1s = [], [], []
    for i, cls_name in enumerate(classes):
        tp = cm[i][i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp
        pr = float(tp)/max(tp+fp, 1)
        re = float(tp)/max(tp+fn, 1)
        f1 = (2*pr*re)/max(pr+re, 1e-5)
        precs.append(pr); recs.append(re); f1s.append(f1)
        print(f"{cls_name:<28} | {pr*100:<11.2f}% | {re*100:<11.2f}% | {f1*100:<11.2f}% | {np.sum(cm[i,:]):<8}")
    print("-" * 85)
    print(f"{'MACRO AVERAGE':<28} | {np.mean(precs)*100:<11.2f}% | {np.mean(recs)*100:<11.2f}% | {np.mean(f1s)*100:<11.2f}% | {len(all_t):<8}")
    print("-" * 85)
    print(f"\n🏆 OVERALL UNTOUCHED TEST ACCURACY: {(np.trace(cm)/max(np.sum(cm),1))*100:.2f}%")
    print("="*85)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediPaw Review 2 High-Accuracy Colab Trainer")
    parser.add_argument("--data_dir", type=str, default="./data/cnn1_denoised_split", help="Path to preprocessed dataset")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs (20 recommended for Colab)")
    parser.add_argument("--batch", type=int, default=64, help="Batch size (64 runs fast on Colab T4 GPU)")
    parser.add_argument("--lr", type=float, default=0.0001, help="AdamW fine-tuning learning rate")
    args = parser.parse_args()
    
    run_suite(args.data_dir, epochs=args.epochs, batch_size=args.batch, lr=args.lr)
