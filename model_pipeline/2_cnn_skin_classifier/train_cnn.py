import os
import time
import json
import math
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

from dataset_loader import get_dataloaders
from model_architecture import MediPawSkinClassifier

def train_model(epochs=30, batch_size=32, learning_rate=0.0001, weight_decay=0.01, patience=10, backbone="efficientnet_v2_s", filter_duplicates=True):
    print("="*85)
    print("      MEDIPAW REVIEW 2: EFFICIENTNET-V2 HIGH-ACCURACY TRAINING ENGINE      ")
    print("="*85)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Engine] Hardware Execution Device Selected: {device}")
    print(f"[Engine] Selected Deep Learning Backbone: {backbone}")
    print(f"[Engine] Duplicate Filtering Status: {'Active (0% Leakage Mode)' if filter_duplicates else 'Inactive (Full Dataset Mode)'}\n")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dataset_dir = os.path.join(base_dir, "datasets", "cnn1_denoised_split")
    
    if not os.path.exists(dataset_dir):
        print(f"[ERROR] Dataset directory missing: {dataset_dir}")
        print("Please execute denoise_and_prepare.py first to generate the preprocessed splits.")
        return

    train_loader, val_loader, test_loader, classes = get_dataloaders(dataset_dir, batch_size=batch_size, num_workers=0, filter_duplicates=filter_duplicates)
    num_classes = len(classes)

    model = MediPawSkinClassifier(num_classes=num_classes, dropout_rate=0.4, backbone_type=backbone).to(device)

    raw_weights = [1.1515, 0.7463, 0.8856, 7.9939, 0.9321, 0.6828]
    damped_weights = [round(math.sqrt(w), 4) for w in raw_weights]
    class_weights = torch.tensor(damped_weights[:num_classes], dtype=torch.float32).to(device)
    
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.05)
    print(f"\n[Loss] Square-Root Damped Loss Weights: {damped_weights} + Label Smoothing (0.05).")

    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay, betas=(0.9, 0.999), eps=1e-8)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    print(f"[Optimization] Gentle AdamW Fine-Tuning (lr={learning_rate}) + CosineAnnealingLR Active.\n")

    best_val_acc = 0.0
    epochs_without_improvement = 0
    training_history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    weights_save_path = os.path.join(os.path.dirname(__file__), "best_cnn1_weights.pth")
    history_save_path = os.path.join(os.path.dirname(__file__), "training_history.json")

    print("-" * 85)
    print(f"{'Epoch':<8} | {'Phase Status':<15} | {'Train Loss':<12} | {'Val Loss':<12} | {'Val Acc':<12} | {'Time (s)':<8}")
    print("-" * 85)

    for epoch in range(1, epochs + 1):
        start_time = time.time()
        
        if epoch <= 3:
            model.freeze_backbone(freeze=True)
            phase_name = "Stage1-Warmup"
            if epoch == 1:
                print(f"[Stage 1] Freezing backbone for first 3 epochs to stabilize new classifier head...")
        elif epoch == 4:
            model.freeze_backbone(freeze=False)
            phase_name = "Stage2-Finetune"
            print(f"\n[Stage 2] Unfreezing backbone! Entering full-network deep feature fine-tuning...")
        else:
            phase_name = "Stage2-Finetune"

        model.train()
        train_loss = 0.0
        correct_train = 0
        total_train = 0
        
        for idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            train_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            correct_train += (predicted == labels).sum().item()
            total_train += labels.size(0)

        epoch_train_loss = train_loss / max(total_train, 1)
        epoch_train_acc = (correct_train / max(total_train, 1)) * 100.0
        scheduler.step()

        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * images.size(0)
                _, predicted = torch.max(outputs, 1)
                correct_val += (predicted == labels).sum().item()
                total_val += labels.size(0)

        epoch_val_loss = val_loss / max(total_val, 1)
        epoch_val_acc = (correct_val / max(total_val, 1)) * 100.0
        duration = time.time() - start_time

        training_history["train_loss"].append(round(epoch_train_loss, 4))
        training_history["val_loss"].append(round(epoch_val_loss, 4))
        training_history["train_acc"].append(round(epoch_train_acc, 2))
        training_history["val_acc"].append(round(epoch_val_acc, 2))

        print(f"{epoch:02d}/{epochs:02d} | {phase_name:<15} | {epoch_train_loss:<12.4f} | {epoch_val_loss:<12.4f} | {epoch_val_acc:<11.2f}% | {duration:<8.1f}")

        if epoch_val_acc > best_val_acc:
            best_val_acc = epoch_val_acc
            epochs_without_improvement = 0
            torch.save(model.state_dict(), weights_save_path)
        else:
            if epoch >= 4:
                epochs_without_improvement += 1
            if epochs_without_improvement >= patience:
                print(f"\n[EARLY STOPPING] Validation accuracy did not improve for {patience} consecutive epochs.")
                break

    print("-" * 85)
    print(f"\n[SUCCESS] Training concluded! Best Validation Accuracy achieved: {best_val_acc:.2f}%")
    print(f"[SAVED] Optimal weights stored at: {weights_save_path}")
    
    with open(history_save_path, "w") as f:
        json.dump(training_history, f, indent=4)
    print("="*85)

if __name__ == "__main__":
    train_model(epochs=30, batch_size=32, learning_rate=0.0001, weight_decay=0.01, patience=10, backbone="efficientnet_v2_s", filter_duplicates=True)
