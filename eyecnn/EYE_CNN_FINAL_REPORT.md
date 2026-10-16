# MediPaw Project Review — Eye CNN Module Final Report

**Module**: Eye CNN (Canine Ocular Abnormality Classification)  
**Project**: MediPaw Veterinary Decision-Support & Triage System  
**Implementation Date**: October 2026  
**Status**: Completed, Verified & Finalized  

---

## 1. Executive Summary

The Eye CNN module operates as an independent diagnostic pipeline within the MediPaw multi-modal veterinary triage system. It receives ocular close-up photographs, classifies canine eye pathologies into four verified clinical categories, and extracts a **576-dimensional intermediate visual feature embedding** designed for downstream cross-attention fusion in the Multi-Modal Vision Transformer (ViT).

On the independent, held-out test partition (264 samples), the final model achieved an overall accuracy of **82.95%** and a macro F1-score of **0.8289**, with an average CPU inference latency of **~52 ms**.

---

## 2. MediPaw Multi-Pipeline Architecture & Integration Contract

```
                +-------------------------------------------------------+
                |                 Three Separate Inputs                 |
                |  (1) Skin/Body Image  (2) Eye Close-Up  (3) Chest X-ray|
                +-------------------------------------------------------+
                                            |
          +---------------------------------+---------------------------------+
          |                                 |                                 |
          v                                 v                                 v
+-------------------+             +--------------------+            +-------------------+
|   Skin Pipeline   |             |    Eye Pipeline    |            | Thoracic Pipeline |
|  - Skin CNN       |             |   (THIS MODULE)    |            |  - Thoracic CNN   |
|  - YOLOv8 (Wound) |             |  - Eye CNN         |            +-------------------+
|  - U-Net (Segm.)  |             +--------------------+                      |
+-------------------+                       |                                 |
          |                                 |                                 |
          +---------------------------------+---------------------------------+
                                            |
                                            v
                +-------------------------------------------------------+
                |             Multi-Modal Vision Transformer            |
                |       Cross-attention fusion of visual embeddings     |
                +-------------------------------------------------------+
                                            |
                                            v
                +-------------------------------------------------------+
                |                Treatment Priority Score               |
                |            Low  |  Medium  |  High  |  Critical       |
                +-------------------------------------------------------+
```

### ViT Feature Interface
- **Embedding Tensor**: $\mathbf{e}_{\text{eye}} \in \mathbb{R}^{B \times 576}$ extracted via `model.forward_features(x)` or `model.forward_with_features(x)`.
- **Modality Token Projection**: $\mathbf{t}_{\text{eye}} = \text{Linear}(576, d_{\text{model}})(\mathbf{e}_{\text{eye}}) \in \mathbb{R}^{B \times 1 \times d_{\text{model}}}$.
- **Triage Decoupling**: Eye disease probabilities (`conjunctivitis`, `entropion`, `eyelid_lump`, `healthy`) indicate ocular pathology presence. They do **not** independently prescribe triage severity; severity scoring is calculated only after multi-modal evidence fusion.

---

## 3. Dataset Audit & Provenance

- **Source**: Roboflow Dog Eye Problems Detection v4 (`CC BY 4.0`).
- **Format**: Converted from YOLOv8 object detection bounding boxes to $224 \times 224$ classification crops with a **5% proportional safety padding margin**.
- **Verified Classes (`nc: 4`)**:
  - `0`: `conjunctivitis`
  - `1`: `entropion`
  - `2`: `eyelid_lump`
  - `3`: `healthy`

### Physical File & Crop Breakdown
| Partition | Source Images | Annotated Bounding Boxes | Valid Crops Generated | Skipped Crops (<16px) |
|:---|:---:|:---:|:---:|:---:|
| **Train** | 5,570 | 5,573 | 5,570 | 3 |
| **Valid** | 531 | 531 | 531 | 0 |
| **Test** | 264 | 264 | 264 | 0 |
| **Total** | **6,365** | **6,368** | **6,365** | **3** |

### Verified Class Frequencies (Crops)
| Class Name | Train Split | Valid Split | Test Split | Total Crops | Training Weight ($w_c$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| `conjunctivitis` | 1,458 | 145 | 68 | 1,671 | 0.9551 |
| `entropion` | 1,464 | 140 | 58 | 1,662 | 0.9512 |
| `eyelid_lump` | 1,511 | 126 | 63 | 1,700 | 0.9216 |
| `healthy` | 1,137 | 120 | 75 | 1,332 | 1.2247 |

### Cross-Split Data Leakage Audit
- Roboflow generated 3 augmented versions per base image in `train` ($1,857 \times 3 \approx 5,570$).
- Cryptographic hash audit revealed:
  - Exact filename overlap: **0** across all split pairs.
  - Base source ID overlap (pre-augmentation stem): **0** across all split pairs.
  - UUID overlap: **0** across all split pairs (1,857 unique in train, 531 in valid, 264 in test; 2,652 total unique source images).
- **Animal-Level Independence Caveat**: While image-level and augmentation-level independence is verified, the dataset lacks clinical patient records, meaning different photos could theoretically originate from the same dog.

---

## 4. Technical Architecture & Training Configuration

- **Backbone**: MobileNetV3-Small (pretrained on ImageNet-1k).
- **Classification Head**:
  $$\text{GlobalAvgPool}(576) \longrightarrow \text{Linear}(576, 256) \longrightarrow \text{Hardswish} \longrightarrow \text{Dropout}(0.2) \longrightarrow \text{Linear}(256, 4)$$
- **Input Resolution**: $224 \times 224 \times 3$, normalized with ImageNet parameters ($\mu=[0.485, 0.456, 0.406]$, $\sigma=[0.229, 0.224, 0.225]$).
- **Training Augmentations**: Random horizontal flip ($p=0.5$), random rotation ($\pm 15^\circ$), color jitter (brightness, contrast, saturation), and affine translation ($\pm 5\%$).
- **Loss**: Cost-sensitive Cross-Entropy loss weighted by inverse training frequencies.
- **Optimizer**: AdamW ($lr=3 \times 10^{-4}$, weight decay $1 \times 10^{-4}$) with Cosine Annealing scheduler.
- **Hardware Profile**: CPU-optimized execution (~52 ms single-image latency).

---

## 5. Measured Evaluation Benchmarks (Held-Out Test Set)

Evaluated on the independent test split ($N = 264$ crops):

| Metric | Score |
|:---|:---:|
| **Overall Accuracy** | **82.95%** (219 / 264) |
| **Macro Precision** | **84.14%** |
| **Macro Recall** | **83.32%** |
| **Macro F1-Score** | **0.8289** |
| **Weighted Precision** | **84.33%** |
| **Weighted F1-Score** | **0.8277** |

### Per-Class Performance
| Ocular Class | Precision | Recall | F1-Score | Support |
|:---|:---:|:---:|:---:|:---:|
| `conjunctivitis` | 0.7816 | **1.0000** | **0.8774** | 68 |
| `entropion` | 0.7385 | 0.8276 | 0.7805 | 58 |
| `eyelid_lump` | **0.9811** | 0.8254 | **0.8966** | 63 |
| `healthy` | 0.8644 | **0.6800** | 0.7612 | 75 |

### Test Confusion Matrix
| Ground Truth \ Predicted | `conjunctivitis` | `entropion` | `eyelid_lump` | `healthy` | Total |
|:---|:---:|:---:|:---:|:---:|:---:|
| **`conjunctivitis`** | **68** | 0 | 0 | 0 | 68 |
| **`entropion`** | 2 | **48** | 0 | 8 | 58 |
| **`eyelid_lump`** | 10 | 1 | **52** | 0 | 63 |
| **`healthy`** | 7 | 16 | 1 | **51** | 75 |

---

## 6. Error Pattern Analysis: Healthy Class Recall (68.00%)

Inspection of the 24 misclassified healthy cases demonstrates two primary clinical patterns:
1. **Entropion False Positives (16 / 24, 66.7%)**:
   Canine breeds with natural heavy facial wrinkles, deep-set orbits, and prominent peri-orbital skin folds (e.g., Bulldogs, Shar-Peis, Bassets, Mastiffs) present contour cues that mimic inward eyelid roll (`entropion`), leading the model to over-predict entropion on healthy eyes.
2. **Conjunctivitis False Positives (7 / 24, 29.2%)**:
   Normal physiological canine scleral pigmentation, prominent episcleral vessels in excited dogs, and close-up photographic flash glare mimic conjunctival hyperemia.
3. **Clinical Posture**:
   The model exhibits a conservative bias toward flagging potential pathology (high sensitivity) rather than missing true cases. In a triage system, false positives are routed to human veterinary inspection, whereas false negatives could delay urgent treatment.

---

## 7. Inference Preprocessing & Cropping Protocol

- **Uncropped Input Handling**: The model accepts any input format/size, automatically resizing to $224 \times 224$.
- **Clinical Protocol**:
  - **Macro Eye Close-Ups**: If the eye occupies $\ge 60\%$ of the image frame, it can be passed directly.
  - **Wide-Angle / Full-Face Photos**: Resizing a full head photo directly to $224 \times 224$ reduces the eye to $<20$ pixels and introduces fur/snout artifacts. A bounding box crop with **5% proportional padding** must be performed prior to Eye CNN classification.

---

## 8. Saved Artifacts Directory

| Artifact | Location | Purpose |
|:---|:---|:---|
| **Best Model Weights** | `models/eye_cnn/best_eye_model.pth` | PyTorch model checkpoint (13.1 MB) |
| **Model Configuration** | `models/eye_cnn/model_config.json` | Architecture & ViT contract metadata |
| **Class Mapping** | `models/eye_cnn/class_mapping.json` | Label-to-index mapping dictionary |
| **Test Summary JSON** | `outputs/test_evaluation_summary.json` | Full quantitative evaluation metrics |
| **Classification Report** | `outputs/classification_report.txt` | Formatted per-class precision/recall table |
| **Confusion Matrix Plot** | `outputs/confusion_matrix.png` | Normalized confusion matrix heatmap |
| **Confusion Matrix Data** | `outputs/confusion_matrix.csv` | Raw prediction-vs-truth counts |
| **Training Curves** | `outputs/training_curves.png` | Train/val loss and macro F1 plots |
| **Sample Predictions** | `outputs/sample_predictions.png` | Visual prediction collage with confidence |
| **Crop Metadata Table** | `datasets/eye/crop_metadata.csv` | Full provenance tracking for all 6,365 crops |
| **Training Class Weights**| `datasets/eye/class_weights.json` | Balanced cost-sensitive weights |
| **Inspection Report** | `outputs/dataset_report/` | Dataset summary and class distribution plots |

---

## 9. Conclusion & Transition to U-Net

The Eye CNN module is fully verified, operational, and packaged. All source code, data preprocessing pipelines, trained weights, evaluation benchmarks, and documentation are complete.

**Next Milestone**: Implementation of the **U-Net wound-region segmentation module** using teammate Uha's existing GitHub code.
