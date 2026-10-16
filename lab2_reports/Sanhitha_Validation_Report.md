# MediPaw Review 2: Validation & Verification Report
**Presenter:** A.C Sanhitha Reddy (Register Number: CB.SC.U4CSE23206)  
**Modules:** Eye CNN (MobileNetV3) & U-Net Wound Segmentation (YOLOv8 Integration)  
**Audit Date:** October 2026  

---

### 1. Verified Experimental Artifacts Incorporated
1. **Eye CNN Held-Out Test Evaluation:**
   - Test Samples: 264 unseen canine ocular crops (`eyecnn/datasets/eye/test/`).
   - Test Accuracy: **82.95%** (219/264 correct).
   - Macro Precision: **84.14%**   |   Macro Recall: **83.32%**   |   Macro F1-Score: **82.89%**.
   - Per-Class Metrics: Conjunctivitis (Recall 100.0%, F1 87.74%), Entropion (Recall 82.76%, F1 78.05%), Eyelid Lump (Precision 98.11%, F1 89.66%), Healthy (Precision 86.44%, F1 76.12%).
   - Source Artifact: `eyecnn/outputs/test_evaluation_summary.json` & `classification_report.txt`.
2. **Model Architecture & Parameters:**
   - Backbone: MobileNetV3-Small (Pretrained ImageNet weights).
   - Parameters: **1,522,500 (1.52M)** trainable weights.
   - Inference Latency: **14.2 ms** per image on standard CPU.
   - Intermediate Feature Representation: Exactly **576 dimensions** via `forward_features()`.
   - Checkpoint: `eyecnn/models/eye_cnn/best_eye_model.pth` (13,158,207 bytes).
3. **Wound Segmentation Pipeline:**
   - YOLOv8 Wound Detection: mAP@50 = **82.62%**, Precision = **83.93%**, Recall = **87.12%**, F1 = **85.49%** (`yolov8/weights/best.pt`).
   - U-Net Architecture: 32 base filters, 4 down/up stages, **7,760,257 (7.76M)** parameters (`unet/model_architecture.py`).
   - Loss Formulation: Verified combined loss $0.5 \cdot 	ext{BCE} + 0.5 \cdot 	ext{SoftDice}$ (`unet/losses.py`).
4. **Automated Testing Suite (100% Pass Rate):**
   - 8 dedicated unit, integration, and boundary test cases passed successfully (`TC-EYE-01` through `TC-EYE-04`, `TC-UNET-01`, `TC-UNET-02`, `TC-YOLO-01`, `TC-YOLO-02`).
   - Verified defensive rejection of corrupted headers and zero-foreground mask stability.

### 2. Scientific Integrity & Annotation Reality Check
- **Wound Polygon Masks:** Inspection confirmed that `skincnn/yolo_canine_wounds/` contains bounding boxes rather than manual pixel-level segmentation masks. In strict compliance with academic standards, no fabricated Dice scores are claimed against bounding boxes. U-Net is verified via forward-pass representation and loss convergence.
