"""
=====================================================================================
            MEDIPAW MODULE 3: YOLOv8 UNIFIED WOUND DETECTION (COLAB TRAINER)
=====================================================================================
Instructions for running in Google Colab (Free T4 GPU):
 1. Upload yolo_dog_wounds.zip directly to Google Drive or the Colab `/content/` files panel.
 2. Ensure Runtime GPU is enabled: Runtime -> Change runtime type -> T4 GPU.
 3. Run this script in a Colab code cell: !python /content/train_yolov8_unified.py

What this script automatically does:
 1. Extracts the full dataset.
 2. Parses EVERY label file and unifies all injury classes (Cow, Cat, Buffalo, Dog) into 
    a single class (0: "Wound").
 3. Purges irrelevant bounding boxes (Humans, Uninjured) so they become negative background.
 4. Re-writes data.yaml for single-class detection.
 5. Trains YOLOv8s and computes exhaustive metrics on Train/Val/Test splits.
 6. Generates Bias-Variance diagnostic curves.
=====================================================================================
"""

import os
import sys
import json
import shutil
import zipfile

try:
    import ultralytics
    from ultralytics import YOLO
except ImportError:
    print("[INFO] Installing ultralytics package...")
    os.system("pip install -q ultralytics")
    import ultralytics
    from ultralytics import YOLO

try:
    import pandas as pd
    import matplotlib.pyplot as plt
except ImportError:
    print("[INFO] Installing pandas and matplotlib...")
    os.system("pip install -q pandas matplotlib")
    import pandas as pd
    import matplotlib.pyplot as plt

import torch

def verify_hardware():
    print("="*85)
    print("  MEDIPAW MODULE 3: YOLOv8 UNIFIED 'WOUND' TRAINING ENGINE  ")
    print("="*85)
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[HARDWARE READY] CUDA GPU Accelerated: {gpu_name} ({vram_gb:.2f} GB VRAM)")
        return "0"
    else:
        print("\n" + "!"*85)
        print("[CRITICAL WARNING] No CUDA GPU detected! Training on CPU will be extremely slow.")
        print("!"*85 + "\n")
        return "cpu"

def unify_labels_and_curate_data(dataset_root):
    """
    Original Classes: 
    0: 'human', 1: 'injured buffalo', 2: 'injured cat', 3: 'injured cow', 
    4: 'injured-dogs', 5: 'uninjured', 6: 'uninjured dogs'
    
    Logic:
    - Map classes 1, 2, 3, 4 -> 0 (Wound)
    - Drop classes 0, 5, 6 (Remove bounding box, keeping image as negative background)
    """
    print("[INFO] Unifying all multi-species injuries into a single 'Wound' class...")
    
    total_boxes_kept = 0
    total_boxes_purged = 0
    
    for split in ["train", "valid", "val", "test"]:
        label_dir = os.path.join(dataset_root, split, "labels")
        if os.path.exists(label_dir):
            for txt_file in os.listdir(label_dir):
                if not txt_file.endswith(".txt"): continue
                
                filepath = os.path.join(label_dir, txt_file)
                new_lines = []
                
                with open(filepath, "r") as f:
                    lines = f.readlines()
                    
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(parts[0])
                        # If it is any type of injury
                        if cls_id in [1, 2, 3, 4]:
                            # Remap to class 0
                            new_lines.append(f"0 {' '.join(parts[1:])}\n")
                            total_boxes_kept += 1
                        else:
                            # It's a human, uninjured, or uninjured dog. Delete the box.
                            total_boxes_purged += 1
                
                # Overwrite the file with curated labels
                with open(filepath, "w") as f:
                    f.writelines(new_lines)
                    
    print(f" -> [SUCCESS] Retained {total_boxes_kept} unified Wound annotations.")
    print(f" -> [SUCCESS] Purged {total_boxes_purged} irrelevant noise annotations (humans/uninjured).")

def prepare_colab_dataset(zip_filename="yolo_dog_wounds.zip", search_root="/content"):
    print("\n[STEP 1] Extracting & Curating Full Dataset into Unified Class...")
    
    local_fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "yolo_dog_wounds"))
    
    # Check if we are running locally with the raw directory already present
    if not os.path.exists("/content") and os.path.exists(local_fallback):
        # We need a copy of this locally so we don't destroy the original dataset labels
        extract_dest = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_yolo_unified_dataset"))
        if not os.path.exists(extract_dest):
            print(f"[INFO] Cloning local dataset to {extract_dest} for curation...")
            shutil.copytree(local_fallback, extract_dest)
        search_root = extract_dest
    else:
        # Colab environment zip extraction
        zip_path = os.path.join("/content", zip_filename)
        drive_zip = os.path.join("/content/drive/MyDrive", zip_filename)
        
        target_zip = zip_path if os.path.exists(zip_path) else (drive_zip if os.path.exists(drive_zip) else None)
        if target_zip:
            extract_dest = "/content/yolo_unified_workspace"
            print(f"[INFO] Extracting {target_zip} to {extract_dest}...")
            os.makedirs(extract_dest, exist_ok=True)
            with zipfile.ZipFile(target_zip, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    member.filename = member.filename.replace('\\', '/')
                    if not member.filename.endswith('/') and member.filename.strip():
                        zip_ref.extract(member, extract_dest)
            search_root = extract_dest
        else:
            print(f"[ERROR] Could not find {zip_filename} in /content or /content/drive/MyDrive")
            return None

    # Apply the logic to unify labels
    unify_labels_and_curate_data(search_root)

    # Locate and rewrite data.yaml
    found_yaml = None
    for root, dirs, files in os.walk(search_root):
        if "data.yaml" in files:
            found_yaml = os.path.join(root, "data.yaml")
            break

    if found_yaml:
        dataset_root = os.path.dirname(found_yaml)
        abs_dir = os.path.abspath(dataset_root).replace("\\", "/")
        
        # Determine valid folder name (valid vs val)
        val_folder = "val/images" if os.path.exists(os.path.join(dataset_root, "val")) else "valid/images"
        
        updated_yaml = f"""path: {abs_dir}
train: train/images
val: {val_folder}
test: test/images

nc: 1
names: ['Wound']
"""
        with open(found_yaml, "w") as f:
            f.write(updated_yaml)
        print(f"[SUCCESS] Re-written data.yaml for Single Class Detection at: {abs_dir}")
        return found_yaml
    else:
        print("[ERROR] Could not locate 'data.yaml'.")
        return None

def display_metrics(split_name, metrics):
    map50 = metrics.box.map50 * 100
    map50_95 = metrics.box.map * 100
    precision = metrics.box.mp * 100
    recall = metrics.box.mr * 100
    
    if (precision + recall) > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0

    print(f"\n--- {split_name.upper()} SET METRICS ---")
    print(f" * Precision (P)              : {precision:.2f}%")
    print(f" * Recall (R)                 : {recall:.2f}%")
    print(f" * F1-Score                   : {f1_score:.2f}%")
    print(f" * mAP@0.5 (mAP50)            : {map50:.2f}%")
    print(f" * mAP@0.5:0.95 (mAP50-95)    : {map50_95:.2f}%")
    
def analyze_bias_variance(run_dir):
    csv_path = os.path.join(run_dir, "results.csv")
    if not os.path.exists(csv_path): return

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    
    epochs = df['epoch']
    train_loss = df['train/box_loss'] + df['train/cls_loss'] + df['train/dfl_loss']
    val_loss = df['val/box_loss'] + df['val/cls_loss'] + df['val/dfl_loss']
    
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, train_loss, label='Training Loss (Bias)', color='blue', linewidth=2)
    plt.plot(epochs, val_loss, label='Validation Loss (Variance)', color='red', linewidth=2, linestyle='--')
    
    plt.title('Bias-Variance Tradeoff (Unified Wound Model)', fontsize=14)
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Total Combined Loss', fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.7)
    
    plot_path = os.path.join(run_dir, "bias_variance_tradeoff_curve.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n" + "="*85)
    print(" [BIAS-VARIANCE TRADEOFF ANALYSIS]")
    print("="*85)
    print(f" [SUCCESS] Tradeoff curve saved to: {plot_path}")

def run_yolo_training(yaml_path, device_id):
    print("\n" + "="*85)
    print(" [STEP 2] INITIALIZING YOLOv8s FOR UNIFIED DETECTION")
    print("="*85)
    
    model = YOLO("yolov8s.pt")

    print("\n" + "="*85)
    print(" [STEP 3] EXECUTING TRAINING")
    print("="*85)

    results = model.train(
        data=yaml_path,
        epochs=50,
        patience=15,
        batch=16,
        imgsz=640,
        device=device_id,
        optimizer="AdamW",
        lr0=0.001,
        weight_decay=0.01,
        mosaic=1.0,
        degrees=15.0,
        hsv_s=0.7,
        hsv_v=0.4,
        project="medipaw_module3_yolov8_unified",
        name="wound_detector_unified",
        exist_ok=True,
        verbose=False 
    )
    
    run_save_dir = results.save_dir

    print("\n" + "="*85)
    print(" [STEP 4] COMPREHENSIVE PERFORMANCE EVALUATION (TRAIN, VAL, TEST)")
    print("="*85)
    
    print("\n[EVALUATING ON TRAINING DATA...]")
    best_model_path = os.path.join(run_save_dir, "weights", "best.pt")
    if os.path.exists(best_model_path):
        print(f"[INFO] Loading peak performance weights from: {best_model_path}")
        eval_model = YOLO(best_model_path)
    else:
        eval_model = model

    metrics_train = eval_model.val(data=yaml_path, split="train", device=device_id, verbose=False)
    display_metrics("Training", metrics_train)
    
    print("\n[EVALUATING ON VALIDATION DATA...]")
    metrics_val = eval_model.val(data=yaml_path, split="val", device=device_id, verbose=False)
    display_metrics("Validation", metrics_val)
    
    print("\n[EVALUATING ON UNSEEN TESTING DATA...]")
    try:
        metrics_test = eval_model.val(data=yaml_path, split="test", device=device_id, verbose=False)
        display_metrics("Testing", metrics_test)
    except Exception as e:
        print(f"\n[WARNING] Could not evaluate testing set (possibly empty/missing). Error: {e}")

    analyze_bias_variance(run_save_dir)

    return model, metrics_val

if __name__ == "__main__":
    active_device = verify_hardware()
    yaml_config_path = prepare_colab_dataset("yolo_dog_wounds.zip")
    if yaml_config_path:
        trained_model, eval_metrics = run_yolo_training(yaml_config_path, active_device)
