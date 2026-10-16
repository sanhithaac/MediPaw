# MediPaw Module 5: Thoracic CNN

## 1. Overview & Problem Definition
Canine cardiomegaly (cardiac enlargement) and thoracic abnormalities are vital indicators in veterinary emergency triage. The Vertebral Heart Score (VHS) provides an objective, breed-standardized metric measuring cardiac length and width against thoracic vertebrae (T4 onwards).

This module implements the **Thoracic CNN** component for MediPaw, designed to extract visual features from canine latero-lateral thoracic radiographs, calculate feature embeddings for cross-modal Vision Transformer (ViT) fusion, and predict VHS scores when supervised ground truth is supplied.

---

## 2. Dataset Investigation & Provenance
* **Dataset Source:** [Mendeley Data `ktx4cj55pn/1`](https://data.mendeley.com/datasets/ktx4cj55pn/1)
* **Associated Article:** Flores Dueñas et al., *"Canine thoracic radiographic images as an educational dataset for distance learning and research on vertebral heart score"*, *Data in Brief* (2021), [PMC8111263](https://pmc.ncbi.nlm.nih.gov/articles/PMC8111263/).
* **Acquisition:** Universal AV Choice X-Ray System & Rayence XMARU 1417PGA-PCA DR cassette detector at Autonomous University of Baja California Small Animal Veterinary Teaching Hospital.
* **Cohort Characteristics:**
  * Selected 153 latero-lateral radiographs from 153 mature canine patients (2 to 11 years, 5–35 kg, 83 males, 69 females).
  * DICOM SOP Instance UID analysis confirms 151 distinct patient IDs (`1.2.410.200028.100.3...`), with 2 patients having repeat views (`15990` and `296`).

### Scientific & Clinical Integrity Finding
The PMC8111263 publication explicitly states:
> *"The original VHS measurement was not included in the image because it may affect the output results of the training process."*
> *"All images contain confidential patient information not relevant for the overall educational purpose, the data was anonymized by removing all fields that would enable patient identification."*

**Verified Conclusion:** The public dataset consists exclusively of unannotated thoracic radiographs intended as a practice bank for manual student measurement. Neither clinical VHS values nor verified pathology diagnoses are included in the archive. In accordance with ethical standards, **no artificial targets are fabricated**. The module implements complete loading, patient-level splitting, feature extraction, and guarded training/evaluation pipelines that activate upon receiving verified veterinary annotations.

---

## 3. Architecture & Methodology

### Backbone
* **Primary:** `mobilenet_v3_small` (lightweight, mobile-deployable, optimal for small veterinary image sets).
* **Alternative:** `resnet18`.

### Heads & Multi-Modal Readiness
* **Feature Extraction Head:** Extracts a 576-dimensional LayerNorm-stabilized embedding vector (`forward_with_features()`), enabling downstream cross-attention fusion in MediPaw's multi-modal triage model.
* **VHS Regression Head:** Multi-layer projection with GELU activation and dropout predicting continuous VHS values.
* **Pathology Classifier Head (Optional):** Extensible multi-class diagnostic head.

### Patient-Level Splitting
* Uses `parse_patient_id_from_filename()` to group images by genuine canine subject.
* 70% Train / 15% Validation / 15% Held-Out Test split.
* Guarantees images from multi-view patients (e.g. `15990`) never cross split boundaries.

---

## 4. Module Structure

```
thoraciccnn/
├── data/                  # Directory junction to downloaded 153 radiographs
├── checkpoints/           # Saved model weights
├── dataset_loader.py      # Patient-level splitting, DICOM parsing, transforms
├── model.py               # MobileNetV3 / ResNet-18 architecture with ViT feature head
├── train.py               # Supervised training loop with integrity guards
├── evaluate.py            # MSE, RMSE, MAE, R² metrics on held-out test split
├── inference.py           # ThoracicPredictor class
├── thoraciccnn_api.py     # Documented callable predict_thoracic() interface
├── requirements.txt       # Dependencies
└── README.md              # Technical documentation
```

---

## 5. API Usage

```python
from thoraciccnn.thoraciccnn_api import predict_thoracic

result = predict_thoracic("path/to/radiograph.png", return_features=True)

# Example Response (when awaiting ground-truth annotations):
# {
#   "status": "unvalidated_prototype",
#   "model_name": "Thoracic CNN (Canine Radiograph)",
#   "task": "Vertebral Heart Score (VHS) Regression / Feature Extraction",
#   "prediction": "Awaiting Clinical Ground-Truth Annotations",
#   "confidence": null,
#   "vhs_score": null,
#   "feature_vector": null,
#   "is_trained": false,
#   "model_ready": false,
#   "warnings": [
#     "Thoracic dataset (PMC8111263) consists of 153 unannotated canine radiographs...",
#     "No artificial labels have been fabricated."
#   ],
#   "diagnostics": {
#     "source": "1.2.410.200028.100.3.20190920.1208500638.12380.1.5.png",
#     "patient_id": "12380",
#     "dimensions": [2276, 1692],
#     "inference_time_ms": 38.4
#   }
# }
```

---

## 6. Regulatory & Decision-Support Notice
This module is a **research and clinical decision-support prototype**. Until clinical ground-truth annotations are trained and evaluated on an independent benchmark, all outputs must be reviewed by a licensed veterinary professional.
