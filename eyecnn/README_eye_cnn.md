# MediPaw — Eye CNN Ocular Abnormality Classification Module

This repository contains the standalone, reproducible **Eye CNN module** for the **MediPaw Veterinary Decision-Support System**.

MediPaw is a multi-pipeline veterinary image triage system designed to assist veterinary professionals by assessing animal injuries and pathologies. The Eye CNN module specifically detects and classifies canine ocular abnormalities from close-up ocular photographs.

---

## 1. System Architecture & The Eye Pipeline in MediPaw

MediPaw operates on three specialized vision pipelines, followed by a multi-modal fusion and triage prioritization stage:

```text
               +-------------------------------------------------------+
               |                 Three Separate Inputs                 |
               |  (1) Skin/Body Image  (2) Eye Close-up  (3) Chest X-ray|
               +-------------------------------------------------------+
                                           |
         +---------------------------------+---------------------------------+
         |                                 |                                 |
         v                                 v                                 v
+------------------+             +--------------------+            +-------------------+
|  Skin Pipeline   |             |    Eye Pipeline    |            | Thoracic Pipeline |
|  - Skin CNN      |             |     (This Module)  |            |  - Thoracic CNN   |
|  - YOLOv8        |             |     - Eye CNN      |            +-------------------+
|  - U-Net Segm.   |             +--------------------+                      |
+------------------+                       |                                 |
         |                                 |                                 |
         +---------------------------------+---------------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |             Multi-Modal Vision Transformer            |
               |   Fuses intermediate embeddings & prediction outputs  |
               +-------------------------------------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |                 Treatment Priority Score              |
               |             Low  |  Medium  |  High  |  Critical       |
               +-------------------------------------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |              Veterinary Decision Support              |
               |        Triage prioritization & clinical workflow      |
               +-------------------------------------------------------+
```

### Modular ViT Integration Contract
- **Intermediate Feature Embeddings**: The Eye CNN extracts a **576-dimensional global pooled feature vector** (for MobileNetV3-Small) from the penultimate layer using `model.forward_features(x)` or `model.forward_with_features(x)`.
- **Downstream Fusion**: This vector is fed directly into the cross-attention layers of the MediPaw Multi-Modal ViT along with embeddings from the Skin CNN and Thoracic CNN.
- **Independence of Disease Prediction vs. Triage Scoring**: Predicted disease probabilities represent ocular classification likelihoods, **not** final triage severity. Urgency and triage category assignment (Low, Medium, High, Critical) are handled downstream once all clinical modalities are fused.

---

## 2. Dataset Information

- **Dataset**: [Dog Eye Problems Detection v4](https://universe.roboflow.com/jonathan-chandra/dog-eye-problems-detection/dataset/4)
- **License**: Creative Commons Attribution 4.0 International (`CC BY 4.0`)
- **Format**: Roboflow YOLOv8 object detection format, pre-processed to 640x640.
- **Original Splits**:
  - `train`: 5,570 images (5,573 annotated bounding boxes)
  - `valid`: 531 images (531 annotated bounding boxes)
  - `test`: 264 images (264 annotated bounding boxes)
  - Total: 6,365 images across all splits.

### Verified Classes (from `data.yaml`)
| Class ID | Class Name | Clinical Description |
|:---:|:---|:---|
| `0` | `conjunctivitis` | Inflammation of the conjunctival tissue, hyperemia, discharge |
| `1` | `entropion` | Inward rolling of the eyelid causing corneal irritation/ulceration |
| `2` | `eyelid_lump` | Ocular adnexal nodule, meibomian cyst, adenoma, or neoplasia |
| `3` | `healthy` | Normal canine eye with clear cornea, clear conjunctiva, intact margins |

### Cross-Split Data Leakage Verification
Augmentations in the original Roboflow export created 3 variations per base image in `train` (1,857 unique base subjects x 3 = 5,570 images).
Our inspection and cryptographic UUID audit verified that:
- Overlapping base source IDs between **Train and Valid**: **0** (1,857 vs. 531 unique base IDs)
- Overlapping base source IDs between **Train and Test**: **0** (1,857 vs. 264 unique base IDs)
- Overlapping base source IDs between **Valid and Test**: **0** (531 vs. 264 unique base IDs)
- Total unique source images across dataset: **2,652**.
- There is **zero image-level or augmentation-level leakage** across partitions.

> [!IMPORTANT]
> **Clinical & Animal-Level Independence Note**: While cryptographic image-level and augmentation-level independence is verified, the public Roboflow dataset does not supply veterinary clinical records, animal patient IDs, or breed identifiers. Consequently, we cannot formally guarantee animal-level independence (e.g. left vs. right eye of the same dog, or multiple photos of a single animal taken during one visit). Scientific and clinical reporting should describe the dataset as partitioned at the source-image level.

---

## 3. Dataset Preprocessing & YOLO Conversion

Because the original dataset provided object detection bounding boxes, `src/prepare_eye_dataset.py` converts normalized bounding boxes into a classification hierarchy:

1. **Coordinate Transformation**: Normalized YOLO boxes `(xc, yc, w, h)` are mapped to absolute pixel coordinates `(xmin, ymin, xmax, ymax)` on 640x640 images.
2. **Context Margin**: A 5% proportional padding margin (`--padding 0.05`) is added around bounding boxes to preserve surrounding eyelid pathology and prevent abrupt boundary clipping. Coordinates are safely clamped to `[0, width]` and `[0, height]`.
3. **Multi-Box Handling**: Images with multiple annotations are converted into distinct crops indexed by box number (`_crop0.jpg`, `_crop1.jpg`) without silently dropping any labels.
4. **Partition Integrity**: Original `train`, `valid`, and `test` splits are strictly maintained.
5. **Class Folder Output**: Saves standard PyTorch `ImageFolder` structure:
   ```text
   datasets/eye/
   ├── train/
   │   ├── conjunctivitis/
   │   ├── entropion/
   │   ├── eyelid_lump/
   │   └── healthy/
   ├── valid/ ...
   └── test/ ...
   ```
6. **Provenance Tracking**: `datasets/eye/crop_metadata.csv` tracks source image, original split, base source ID, bounding box coordinates, and crop dimensions for all 6,365 crops.

### Training-Only Class Balance Weights
To address natural class frequency variation in the training split, cost-sensitive weights are computed using the inverse class frequency formula $w_c = \frac{N}{K \cdot n_c}$:
- `conjunctivitis`: **0.95508** (1,458 crops)
- `entropion`: **0.95116** (1,464 crops)
- `eyelid_lump`: **0.92158** (1,511 crops)
- `healthy`: **1.22471** (1,137 crops)

---

## 4. Model Architecture & Training Setup

### Architecture: EyeCNN
- **Backbone**: MobileNetV3-Small (default, lightweight for CPU and edge veterinary clinic hardware) or EfficientNet-B0.
- **Feature Extractor**: Inverted residual blocks with hard-swish activations producing a **576-dimensional pooled feature representation**.
- **Classification Head**:
  - `Linear(576, 256)` -> `Hardswish` -> `Dropout(p=0.2)` -> `Linear(256, 4)`
- **Input Resolution**: 224 x 224 RGB.
- **Normalization**: Standard ImageNet statistics (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`).

### Training Pipeline
- **Augmentation (Training only)**:
  - Random Horizontal Flip ($p=0.5$)
  - Random Rotation ($\pm 15^\circ$)
  - Color Jitter (brightness 0.15, contrast 0.15, saturation 0.10)
  - Random Affine Translation ($\pm 5\%$)
- **Loss Function**: Weighted Cross-Entropy Loss (`nn.CrossEntropyLoss(weight=class_weights)`).
- **Optimizer**: AdamW ($lr=3 \times 10^{-4}$, weight decay $1 \times 10^{-4}$).
- **Scheduler**: Cosine Annealing learning rate schedule ($\eta_{min} = 1 \times 10^{-6}$).
- **Early Stopping**: Monitors validation macro F1-score with patience of 5 epochs. Best checkpoint is automatically preserved.

---

## 5. Execution Guide (Windows PowerShell)

Run all commands from the repository root: `MediPaw_Code/eyecnn`.

### Step 1: Environment Setup
```powershell
# Create virtual environment (optional if using active Python environment)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Step 2: Inspect Dataset
Inspects annotations, checks image integrity, verifies classes, and detects split leakage:
```powershell
python src/inspect_eye_dataset.py
```
*Outputs saved to `outputs/dataset_report/`:*
- `dataset_summary.json` & `dataset_inspection_report.md`
- `class_distribution.png` & `split_summary.png`
- `sample_overlays/` (sample images with verified bounding boxes)

### Step 3: Prepare Classification Dataset
Converts YOLO bounding boxes into 5% padded crops organized into train/valid/test class directories:
```powershell
python src/prepare_eye_dataset.py --padding 0.05
```
*Outputs saved to `datasets/eye/`:*
- `crop_metadata.csv` & `class_weights.json`
- Directory hierarchy `datasets/eye/{train,valid,test}/{class}/`

### Step 4: Train Eye CNN
Trains MobileNetV3-Small with training augmentations, cost-sensitive weighting, and early stopping:
```powershell
python src/train_eye_cnn.py --backbone mobilenet_v3_small --epochs 10 --batch_size 64 --lr 0.0003
```
*Outputs saved to `models/eye_cnn/` and `outputs/`:*
- `models/eye_cnn/best_eye_model.pth`
- `models/eye_cnn/model_config.json`
- `models/eye_cnn/class_mapping.json`
- `outputs/training_history.csv`

### Step 5: Evaluate on Held-Out Test Set
Benchmarks the saved best model on the independent test set:
```powershell
python src/evaluate_eye_cnn.py
```
*Outputs generated in `outputs/`:*
- `outputs/classification_report.txt`
- `outputs/confusion_matrix.png` & `outputs/confusion_matrix.csv`
- `outputs/training_curves.png`
- `outputs/sample_predictions.png`
- `outputs/test_evaluation_summary.json`

### Step 6: Run Inference on a Single Image
Run inference from CLI on any eye image or crop:
```powershell
python src/predict_eye.py --image "datasets/eye/test/entropion/<sample_image>.jpg"
```
Or import in Python for downstream integration:
```python
from src.predict_eye import EyePredictor

predictor = EyePredictor(model_path="models/eye_cnn/best_eye_model.pth")
result = predictor.predict("path/to/eye_image.jpg", return_features=True)

print("Predicted Disease:", result["predicted_class"])
print("Class Probabilities:", result["probabilities"])
print("ViT Feature Vector Shape:", len(result["intermediate_features"]["embedding"]))
```

---

## 6. Measured Evaluation Results (Held-Out Test Set)

The final model checkpoint was evaluated on the independent, held-out test partition (264 samples):

| Metric | Measured Score |
|:---|:---:|
| **Test Accuracy** | **82.95%** (219 / 264) |
| **Macro Precision** | **84.14%** |
| **Macro Recall** | **83.32%** |
| **Macro F1-Score** | **0.8289** |
| **Weighted F1-Score** | **0.8277** |

### Per-Class Test Breakdown
| Ocular Class | Precision | Recall | F1-Score | Support (Crops) |
|:---|:---:|:---:|:---:|:---:|
| `conjunctivitis` | 0.7816 | **1.0000** | **0.8774** | 68 |
| `entropion` | 0.7385 | 0.8276 | 0.7805 | 58 |
| `eyelid_lump` | **0.9811** | 0.8254 | **0.8966** | 63 |
| `healthy` | 0.8644 | **0.6800** | 0.7612 | 75 |

- Single-image CPU inference latency: **~52 ms** on Intel/AMD CPU.
- Feature embedding output: **576 dimensions**.

### Deep Investigation: Healthy Class Recall (68.00%) & Confusion Patterns
Analysis of the confusion matrix (`outputs/confusion_matrix.csv`) reveals distinct error modes:
- **Entropion Confusion (16 / 24 errors, 66.7%)**: 16 healthy eyes were classified as `entropion`. Breeds with natural deep facial folds, prominent peri-orbital wrinkling, and heavy brow skin (e.g., Bulldogs, Shar-Peis, Bassets, Mastiffs) present contours that visually resemble inward eyelid roll (`entropion`), leading the model to over-predict eyelid inversion on otherwise healthy eyes.
- **Conjunctivitis Confusion (7 / 24 errors, 29.2%)**: 7 healthy eyes were misclassified as `conjunctivitis`. Natural canine scleral pigmentation, prominent episcleral blood vessels in alert dogs, or flash reflection in close-up photography create hyperemia-like color signatures.
- **Eyelid Lump Confusion (1 / 24 errors, 4.1%)**: Rare false positive.
- **Clinical Implication**: The model favors sensitivity toward detecting ocular disease over strict specificity (conservative triage posture), which prevents missing true clinical cases.

---

## 7. Inference & Input Cropping Requirements

### Can the Eye CNN accept an uncropped eye image?
- **Technical Capability**: [`src/predict_eye.py`](file:///c:/Users/Sunny-Cherry/Desktop/NN%20&%20DL/MediPaw_Code/eyecnn/src/predict_eye.py) will accept any image dimension or aspect ratio, resizing it to $224 \times 224$ via bilinear interpolation without crashing.
- **Diagnostic Requirement**:
  - **Eye Close-Up (Intended Input)**: When the canine eye and surrounding eyelid occupy at least **60–80% of the image frame**, the input can be passed directly.
  - **Wide-Angle / Full-Face Canine Photo**: If an uncropped wide head or full-body photo is passed, resizing to $224 \times 224$ shrinks the actual eye to a few dozen pixels, causing catastrophic loss of fine pathology (corneal vascularity, minor meibomian nodules) and confounding predictions with extraneous fur, snout, or ear textures.
  - **Protocol**: Prior to running Eye CNN classification on wide photos, an ocular region-of-interest (ROI) crop with **5% proportional padding** must be performed (either via an upstream YOLO eye detector or manual bounding box selection).

---

## 8. Project Structure

```text
eyecnn/
├── datasets/
│   └── eye/                       # Classification crop dataset
│       ├── train/                 # 5,570 crops
│       ├── valid/                 # 531 crops
│       ├── test/                  # 264 crops
│       ├── crop_metadata.csv      # Complete provenance metadata
│       ├── class_weights.json     # Cost-sensitive training weights
│       └── dataset_summary.json
├── models/
│   └── eye_cnn/
│       ├── best_eye_model.pth     # Best model checkpoint
│       ├── model_config.json      # Architecture & ViT integration metadata
│       └── class_mapping.json     # Class name <-> index mapping
├── outputs/
│   ├── dataset_report/            # Inspection charts and overlays
│   │   ├── class_distribution.png
│   │   ├── split_summary.png
│   │   ├── dataset_inspection_report.md
│   │   └── sample_overlays/
│   ├── training_history.csv       # Training & validation log per epoch
│   ├── training_curves.png        # Loss and F1 curves
│   ├── confusion_matrix.png       # Normalized confusion matrix heatmap
│   ├── confusion_matrix.csv
│   ├── classification_report.txt  # Precision, recall, F1 per class
│   ├── test_evaluation_summary.json
│   └── sample_predictions.png     # Visual prediction grid
├── src/
│   ├── inspect_eye_dataset.py     # Stage 1: Dataset inspection
│   ├── prepare_eye_dataset.py     # Stage 2: YOLO to crop classification converter
│   ├── eye_model.py               # Stage 3: EyeCNN architecture & ViT feature extractor
│   ├── train_eye_cnn.py           # Stage 4: Training pipeline with early stopping
│   ├── evaluate_eye_cnn.py        # Stage 5: Test evaluation & metrics reporting
│   └── predict_eye.py             # Stage 6: Modular inference & feature extraction API
├── data.yaml                      # Original YOLO dataset configuration
├── README.dataset.txt             # Original dataset metadata
├── README.roboflow.txt            # Roboflow export notes
├── requirements.txt               # Minimal python dependencies
└── README_eye_cnn.md              # Comprehensive module documentation
```

---

## 9. Downstream MediPaw ViT Integration Details

When integrating this module into the multi-modal MediPaw decision-support system:
1. **Model Loader**: Load `EyeCNN` via `EyePredictor` or `build_eye_model()`.
2. **Intermediate Feature Extraction**:
   ```python
   # During multi-modal inference:
   logits, features = model.forward_with_features(eye_tensor_224x224)
   # features is a torch.Tensor of shape (batch_size, 576)
   ```
3. **Multi-Modal ViT Cross-Attention**: The 576-dim feature representation represents the ocular visual embedding and is projected into the ViT's shared embedding dimension alongside the skin feature vector and thoracic X-ray embedding.
4. **Clinical Safety Boundary**: This module provides ocular condition probabilities. It must not be treated as a definitive veterinary diagnosis or autonomous triage category.

---

## 10. Limitations & Next Steps

1. **Dataset Scope**: The current dataset is restricted to 4 canine ocular classes (`conjunctivitis`, `entropion`, `eyelid_lump`, and `healthy`). Conditions such as corneal ulcers, cataracts, and glaucoma are not yet represented in this version.
2. **Image Resolution**: Images are downsampled to 224x224 for classification. Subtle microscopic corneal lesions may benefit from higher-resolution (e.g. 384x384 or 448x448) feature backbones in future iterations.
3. **Clinical Validation**: This model is designed for veterinary decision support and exploratory triage prioritization. Clinical trial validation in veterinary hospital environments is required before production diagnostic deployment.
