"""
=====================================================================================
            MEDIPAW MODULE 3: YOLOv8 CANINE WOUND DETECTION (COLAB TRAINER)
=====================================================================================
Instructions for running in Google Colab (Free T4 GPU):
 1. Upload yolo_canine_wounds.zip directly to Google Drive or the Colab `/content/` files panel.
 2. Ensure Runtime GPU is enabled: Runtime -> Change runtime type -> T4 GPU.
 3. Run this script in a Colab code cell: !python /content/2_train_yolo_colab.py

What this script automatically does:
 1. Checks GPU CUDA availability (T4 / L4 acceleration).
 2. Unpack & automatically discovers data.yaml anywhere in the extraction path!
 3. Configures data.yaml absolute paths for Linux/Colab filesystem environment.
 4. Initializes Ultralytics YOLOv8s (Small) backbone with Path Aggregation FPN.
 5. Executes optimization with AdamW, Mosaic Augmentation, and Early Stopping.
=====================================================================================
"""

import os
import sys
import json
import shutil
import zipfile

# 1. Install & import Ultralytics YOLO framework automatically in Colab/Linux environment
try:
    import ultralytics
    from ultralytics import YOLO
except ImportError:
    print("[INFO] Installing ultralytics package...")
    os.system("pip install -q ultralytics")
    import ultralytics
    from ultralytics import YOLO

import torch

def verify_hardware():
    print("="*85)
    print("  MEDIPAW MODULE 3: YOLOv8 ACUTE TRAUMA & WOUND LOCALIZATION ENGINE  ")
    print("="*85)
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[HARDWARE READY] CUDA GPU Accelerated: {gpu_name} ({vram_gb:.2f} GB VRAM)")
        return "0"  # GPU device 0
    else:
        print("\n" + "!"*85)
        print("[CRITICAL WARNING] No CUDA GPU detected! Training on CPU will be extremely slow.")
        print("Please stop this cell, go to: Runtime -> Change runtime type -> Hardware accelerator -> T4 GPU")
        print("!"*85 + "\n")
        return "cpu"

def prepare_colab_dataset(zip_filename="yolo_canine_wounds.zip", search_root="/content"):
    """Unpack dataset and dynamically hunt for data.yaml regardless of extraction folder nesting."""
    print("\n[STEP 1] Checking and Configuring Curated Dataset...")
    
    # Check if running locally on workstation vs Colab
    local_fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "yolo_canine_wounds"))
    if not os.path.exists("/content") and os.path.exists(local_fallback):
        search_root = local_fallback
        print(f"[INFO] Running on Local Workstation. Searching in: {search_root}")
    else:
        # We are in Google Colab: Unzip if not already extracted
        zip_path = os.path.join("/content", zip_filename)
        drive_zip = os.path.join("/content/drive/MyDrive", zip_filename)
        
        target_zip = zip_path if os.path.exists(zip_path) else (drive_zip if os.path.exists(drive_zip) else None)
        if target_zip:
            print(f"[INFO] Extracting {target_zip} directly to /content/yolo_dataset_workspace...")
            extract_dest = "/content/yolo_dataset_workspace"
            os.makedirs(extract_dest, exist_ok=True)
            with zipfile.ZipFile(target_zip, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    # Transform Windows backslashes into Linux directory separators
                    member.filename = member.filename.replace('\\', '/')
                    if not member.filename.endswith('/') and member.filename.strip():
                        zip_ref.extract(member, extract_dest)
            search_root = extract_dest
        else:
            print("[INFO] Zip file not found in root; searching active directory for already extracted files...")

    # Robust Auto-Discovery: Walk filesystem to find data.yaml anywhere!
    found_yaml = None
    for root, dirs, files in os.walk(search_root):
        if "data.yaml" in files:
            found_yaml = os.path.join(root, "data.yaml")
            break
            
    if not found_yaml and os.path.exists(os.path.join("/content", "data.yaml")):
        found_yaml = "/content/data.yaml"

    if found_yaml:
        dataset_root = os.path.dirname(found_yaml)
        print(f"[SUCCESS] Discovered dataset configuration at: {found_yaml}")
        print(f"[SUCCESS] Dataset root folder located at    : {dataset_root}")

        # Update data.yaml with valid Linux absolute path
        abs_dir = os.path.abspath(dataset_root).replace("\\", "/")
        updated_yaml = f"""path: {abs_dir}
train: train/images
val: val/images
test: test/images

nc: 1
names: ['Dog_Wound']
"""
        with open(found_yaml, "w") as f:
            f.write(updated_yaml)
        print(f"[SUCCESS] Re-written data.yaml configured correctly pointing to: {abs_dir}")
        return found_yaml
    else:
        print(f"[ERROR] Could not locate 'data.yaml' anywhere under {search_root}.")
        print("        Please ensure 'yolo_canine_wounds.zip' is uploaded to Colab!")
        return None

def run_yolo_training(yaml_path, device_id):
    print("\n" + "="*85)
    print(" [STEP 2] INITIALIZING YOLOv8s (SMALL) WITH PATH AGGREGATION FPN BACKBONE")
    print("="*85)
    print(" * Architecture Choice : YOLOv8s (Small) - Optimized for < 15ms Emergency Triage")
    print(" * Pretrained Backbone : COCO Generalization Initialization")
    print(" * Target Class        : Class 0 -> 'Dog_Wound' (Lacerations, Bites, Burns)")
    
    # Load YOLOv8-small architecture
    model = YOLO("yolov8s.pt")

    print("\n" + "="*85)
    print(" [STEP 3] EXECUTING CLINICAL MODEL OPTIMIZATION & TRAINING")
    print("="*85)
    print(" * Optimizer          : AdamW (Learning Rate: 0.001, Weight Decay: 0.01)")
    print(" * Resolution (imgsz) : 640 x 640 px (Letterbox Aspect-Ratio Preserve)")
    print(" * Data Augmentations : Mosaic=1.0, HSV Jitter (Varying Clinic Lighting), Rotation=15 deg")
    print(" * Early Stopping     : Patience = 15 Epochs (Prevents Overfitting on Triage Photos)\n")

    # Execute training via Ultralytics high-performance optimization engine
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
        project="medipaw_module3_yolo",
        name="canine_wound_detector",
        exist_ok=True,
        verbose=True
    )

    print("\n" + "="*85)
    print(" [STEP 4] EVALUATING ON VALIDATION & UNTESTED CLINICAL SUITES")
    print("="*85)
    
    # Evaluate formal validation metrics
    metrics = model.val(data=yaml_path, split="val", device=device_id)
    
    map50 = metrics.box.map50 * 100
    map50_95 = metrics.box.map * 100
    precision = metrics.box.mp * 100
    recall = metrics.box.mr * 100

    print("-" * 85)
    print(f" FINAL CANINE WOUND LOCALIZATION METRICS (READY FOR EVALUATION REPORT)")
    print("-" * 85)
    print(f" * Mean Average Precision @ 0.5 IoU (mAP@50)     : {map50:.2f}%")
    print(f" * Mean Average Precision @ 0.5-0.95 (mAP@50-95) : {map50_95:.2f}%")
    print(f" * Precision (Box Boundary Accuracy)           : {precision:.2f}%")
    print(f" * Recall (True Wound Detection Rate)          : {recall:.2f}%")
    print("-" * 85)
    print(" [SUCCESS] Training curves, Confusion Matrices, and Bounding Box Checkpoints")
    print("           have been generated inside folder: medipaw_module3_yolo/canine_wound_detector")
    print("\n -> MODULE 4 (U-NET) HANDOFF READY:")
    print("    Predicted coordinates [x1, y1, x2, y2] will now crop open trauma boundaries")
    print("    to feed directly into U-Net for total epidermal damage % calculations!")
    print("="*85)

    return model, metrics

if __name__ == "__main__":
    active_device = verify_hardware()
    yaml_config_path = prepare_colab_dataset("yolo_canine_wounds.zip")
    if yaml_config_path:
        trained_model, eval_metrics = run_yolo_training(yaml_config_path, active_device)
