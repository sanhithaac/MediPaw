# MediPaw — Module 4: U-Net Wound Segmentation

## Overview

This module implements a **U-Net encoder-decoder** network for pixel-level
wound segmentation. It is designed as **Module 4** in the MediPaw pipeline,
following the YOLOv8 wound detector (Module 3, Uha's work).

The pipeline flow is:

```
Input image (skin/body photo)
       │
       ▼
YOLOv8 Wound Detector  ──►  Bounding box(es)  [x1,y1,x2,y2]
       │
       ▼  (each ROI cropped and resized to 256×256)
U-Net Segmentation      ──►  Per-pixel sigmoid mask
       │
       ▼  (mask stitched back to full-image canvas)
Full-image binary mask  +  colour overlay  +  JSON result
```

---

## Source Branch & Commit (Uha's work reused)

| Item | Value |
|---|---|
| Repository | `https://github.com/sanhithaac/MediPaw.git` |
| Branch | `unified-yolo-wound-detector` |
| Commit | `e7838fe050fcc58391e93bfd7c047fdfb39d0f84` |
| Author | Uhashini (uhashininithilan@gmail.com) |
| YOLOv8 script | `model_pipeline/3_yolo_wound_detection_only/train_yolov8_unified.py` |
| YOLOv8 weights | `model_pipeline/3_yolo_wound_detection_only/weights/best.pt` |
| Predict script | `model_pipeline/3_yolo_wound_detection_only/predict_new_image.py` |

These files have been copied to `yolov8/` in the project root.

---

## YOLOv8 Model Performance (Uha's results — reused as-is)

| Metric | Score |
|---|---|
| Precision | 83.93% |
| Recall | 87.12% |
| F1-Score | 85.49% |
| mAP@50 | 82.62% |

Class: single unified `Wound` class (any species).  
Weights: `yolov8/weights/best.pt` — 22.5 MB YOLOv8s checkpoint.

---

## ⚠ Annotation Reality Check (IMPORTANT)

The `skincnn/yolo_canine_wounds/` dataset contains **41 YOLO bounding-box
label files** (5 tokens: `class cx cy w h`).

**There are NO pixel-level segmentation masks in the current dataset.**

This means:
- The U-Net architecture and pipeline are complete and ready to train.
- **Real training requires proper binary PNG masks** (one per image, same stem).
- Until masks exist, the dataset loader falls back to **synthetic masks**
  generated from the YOLO bounding boxes (filled rectangles).
- Synthetic masks are adequate only for verifying the pipeline runs.
- **Dice, IoU, precision, and recall computed on synthetic masks are NOT
  valid segmentation metrics and must not be reported as real results.**

To provide real masks, annotate the wound images using a tool such as
[CVAT](https://www.cvat.ai/) or [Roboflow](https://roboflow.com/) in
polygon/instance-mask format, then export binary PNGs.

---

## Project Structure

```
unet/
├── model_architecture.py   # U-Net (encoder-decoder, skip connections)
├── losses.py               # CombinedLoss (BCE + Dice)
├── dataset_loader.py       # WoundSegmentationDataset (real + synthetic modes)
├── train.py                # Training script with CLI
├── evaluate_metrics.py     # Dice, IoU, Precision, Recall
├── inference.py            # YOLOv8 → U-Net pipeline (full inference)
├── medipaw_unet_api.py     # Backend-callable interface
├── visualise.py            # Overlay and diagnostic figure helpers
├── requirements.txt        # Python dependencies
├── checkpoints/            # Saved model checkpoints (created at training)
│   └── best_model.pt
└── outputs/                # Inference output artefacts
    ├── <stem>_detection.jpg
    ├── <stem>_mask.png
    ├── <stem>_overlay.jpg
    └── <stem>_result.json
```

---

## Setup (PowerShell)

```powershell
# From the MediPaw_Code root
cd "c:\Users\Sunny-Cherry\Desktop\NN & DL\MediPaw_Code"

# Install dependencies (use your virtual environment)
pip install -r unet/requirements.txt
```

---

## Training

### With real masks (recommended)

Provide a directory of binary PNG masks where each file shares its stem
with the corresponding image:

```
masks/train/
    dog001.png    # 255 = wound, 0 = background
    dog002.png
    ...
```

```powershell
cd "c:\Users\Sunny-Cherry\Desktop\NN & DL\MediPaw_Code"
python unet/train.py `
    --images_dir path/to/train/images `
    --mask_dir   path/to/train/masks `
    --val_images path/to/val/images `
    --val_masks  path/to/val/masks `
    --epochs 50 --batch 8 --img_size 256
```

### With synthetic masks (pipeline verification only)

```powershell
cd "c:\Users\Sunny-Cherry\Desktop\NN & DL\MediPaw_Code"
python unet/train.py `
    --images_dir skincnn/yolo_canine_wounds/train/images `
    --labels_dir skincnn/yolo_canine_wounds/train/labels `
    --val_images skincnn/yolo_canine_wounds/val/images `
    --val_labels skincnn/yolo_canine_wounds/val/labels `
    --epochs 5 --batch 4
```

> **Warning:** Metrics from synthetic-mask training are not meaningful.

---

## Inference (YOLOv8 → U-Net)

```powershell
cd "c:\Users\Sunny-Cherry\Desktop\NN & DL\MediPaw_Code"
python unet/inference.py `
    --image path/to/dog_photo.jpg `
    --yolo_weights yolov8/weights/best.pt `
    --unet_weights unet/checkpoints/best_model.pt `
    --output_dir   unet/outputs
```

Output files:
| File | Description |
|---|---|
| `<stem>_detection.jpg` | Image with YOLOv8 bounding boxes |
| `<stem>_mask.png` | Full-resolution binary wound mask |
| `<stem>_overlay.jpg` | Original image with translucent mask overlay |
| `<stem>_result.json` | Structured JSON for backend consumption |

---

## Syntax Verification

```powershell
cd "c:\Users\Sunny-Cherry\Desktop\NN & DL\MediPaw_Code"
python -m py_compile unet/model_architecture.py
python -m py_compile unet/losses.py
python -m py_compile unet/dataset_loader.py
python -m py_compile unet/train.py
python -m py_compile unet/evaluate_metrics.py
python -m py_compile unet/inference.py
python -m py_compile unet/medipaw_unet_api.py
python -m py_compile unet/visualise.py
```

---

## Backend Integration

```python
# In your backend (Flask / FastAPI / etc.)
import sys
sys.path.insert(0, "unet")
from medipaw_unet_api import segment_wounds

result = segment_wounds(
    image_path   = "uploads/dog001.jpg",
    yolo_weights = "yolov8/weights/best.pt",
    unet_weights = "unet/checkpoints/best_model.pt",
)

# result["status"]             → "ok" | "no_detections" | "error"
# result["detections"]         → list of YOLO bbox dicts
# result["segmentation_stats"] → list of per-detection wound coverage dicts
# result["mask_path"]          → path to full-res PNG mask
# result["overlay_path"]       → path to overlay JPEG
# result["trained_model"]      → True = real checkpoint loaded
```

---

## U-Net Architecture

```
Input (B, 3, 256, 256)
  │
  ├─ enc1  DoubleConv  →  (B, 32, 256, 256)   ─── skip s1
  ├─ enc2  MaxPool+DC  →  (B, 64, 128, 128)   ─── skip s2
  ├─ enc3  MaxPool+DC  →  (B, 128, 64, 64)    ─── skip s3
  ├─ enc4  MaxPool+DC  →  (B, 256, 32, 32)    ─── skip s4
  │
  ├─ bottleneck        →  (B, 512, 16, 16)
  │
  ├─ dec4  Up+DC       ←  cat(b, s4)  →  (B, 256, 32, 32)
  ├─ dec3  Up+DC       ←  cat(d4, s3) →  (B, 128, 64, 64)
  ├─ dec2  Up+DC       ←  cat(d3, s2) →  (B, 64, 128, 128)
  ├─ dec1  Up+DC       ←  cat(d2, s1) →  (B, 32, 256, 256)
  │
  └─ head  Conv1×1    →  (B, 1, 256, 256)  [raw logit]

                       sigmoid → probability mask
                       ≥0.5    → binary wound mask
```

**Trainable parameters: ~7.7 million** (base_filters=32)

---

## Loss Function

Combined loss: `L = 0.5 × BCE + 0.5 × Dice`

- **BCEWithLogitsLoss** — numerically stable per-pixel cross-entropy
- **Soft Dice Loss** — directly maximises mask overlap metric

---

## Remaining Limitations & Next Steps

| Limitation | Status |
|---|---|
| Real pixel-level wound masks | ❌ **Missing** — must be annotated |
| Meaningful Dice/IoU metrics | ❌ Blocked by missing masks |
| Multi-class severity segmentation | Future (requires labelled data) |
| Thoracic CNN | Not started (out of scope for this task) |
| Multi-Modal ViT | Not started (future module) |
| Backend routing | Not implemented (documented API ready) |
| Frontend wiring to U-Net API | Not implemented (frontend restored) |

---

## Module Integration Map (Full MediPaw)

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│              frontend/   — restored from branch      │
└─────────────────────┬───────────────────────────────┘
                       │  HTTP POST /analyse
                       ▼
┌─────────────────────────────────────────────────────┐
│                    Backend API                       │
│   (to be implemented — routes to model modules)      │
└─────┬──────────┬───────────────┬────────────────────┘
      │          │               │
      ▼          ▼               ▼
  eyecnn/    skincnn/          yolov8/
  Eye CNN   Skin CNN          YOLOv8 Detector
                                  │
                                  ▼
                               unet/   ← THIS MODULE
                          U-Net Segmentation
                                  │
                                  ▼
                         medipaw_unet_api.py
                         (backend callable)
```
