# CDAO Test & Evaluation (T&E) Framework for YOLOv8 Wound Detection

This document maps the CDAO (Chief Digital and AI Office) Test & Evaluation Framework directly to the **YOLOv8 Wound Detection Model** in the **MediPaw** pipeline.

---

## 1. Applicable T&E Focus Areas & Methods for YOLOv8

| CDAO Dimension | Specific Test / Method | Implementation in YOLOv8 Wound Pipeline | Status / Feasibility |
| :--- | :--- | :--- | :--- |
| **1. Framework Focus** | **AI Model T&E** | Evaluating detection accuracy ($mAP@50$, $mAP@50-95$, Precision, Recall, F1-Score). | **Completed** |
| | **Systems Integration (SI) T&E** | Verifying YOLO bounding box output correctly crops input images before feeding to CNN classifier. | **Applicable** |
| **2. Test Types** | **A/B Testing (Differential)** | Comparing Multi-class (7-class) vs. Unified Single-Class (`Wound`) YOLO models. | **Completed** |
| | **Metamorphic Testing** | Checking if image transforms (rotation, flip, scale, brightness) preserve bounding box output. | **Feasible (Augmentation)** |
| | **Adversarial / Perturbation** | Adding synthetic noise, motion blur, and low-light distortions to test detection resilience. | **Feasible** |
| | **Load & Stress Testing** | Benchmarking inference time (ms/frame) and memory usage across CPU, GPU, and edge devices. | **Applicable** |
| **3. Test Design** | **Holdout & Cross-Validation** | Data split ($70\%$ Train, $20\%$ Val, $10\%$ Test) + $k$-fold cross-validation across animal species. | **Completed / Feasible** |
| | **Edge Case Testing** | Testing low-density regions (tiny lesions, dense fur, severe shadows, rare species). | **Applicable** |
| **4. Implementation** | **Automated Black-Box Testing** | Scripted validation (`train_yolov8_academic.py`) measuring IoU without inspecting feature maps. | **Completed** |
| | **White-Box Loss Analysis** | Tracking Box Loss (CIoU/GIoU), Distribution Focal Loss (DFL), and BCE Loss. | **Completed** |
| **5. Performance** | **Correctness Testing** | Evaluating Object Detection metrics ($mAP@50$: 82.6%, Precision: 83.9%, Recall: 87.1%). | **Completed** |
| | **Robustness Testing** | Evaluating natural robustness against blur, angle variations, and lighting shifts. | **Feasible** |
| | **Latency & Throughput** | Profiling pre-processing, inference execution, and NMS post-processing times (ms). | **Completed** |
| | **Representativeness** | Verifying label coverage across various domestic and farm species. | **Completed** |
| **6. Data V&V** | **Data Verification & Validation** | Automated checks for normalized bounding boxes $[x, y, w, h]$, unannotated images, and label integrity. | **Completed** |

---

## 2. Executive Summary of T&E Execution on YOLOv8

1. **Model Correctness & A/B Validation:**
   - **Unified Single-Class YOLOv8** outperformed the initial multi-class model: Precision increased from **26.0% to 83.9%** ($+57.9\%$), and $mAP@50$ reached **82.6%**.

2. **White-Box Loss Convergence & Bias-Variance Analysis:**
   - Smooth convergence across Box Loss (CIoU), Class Loss (BCE), and DFL Loss. Optimal checkpoint (`best.pt`) captured around Epoch 35 to prevent tail-end overfitting.

3. **Inference Latency & Triage Readiness:**
   - Ultra-fast real-time inference ($~5-15 \text{ ms}$ per image on GPU), enabling instantaneous triage cropping before passing data to the secondary skin disease classifier.

---

## 3. Recommended Next Steps for Complete T&E Coverage

1. **Metamorphic & Perturbation Suite:** Run an automated script applying Gaussian noise, contrast adjustments, and rotations to validate box stability.
2. **Edge Hardware Latency Profiling:** Measure inference speeds on low-power mobile/edge hardware (Raspberry Pi / Android CPU).
3. **Downstream Integration Testing:** End-to-end integration test verifying crop handoff from YOLOv8 to the CNN skin classifier.
