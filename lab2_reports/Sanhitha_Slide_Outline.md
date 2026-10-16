# MediPaw Review 2: Slide Outline — A.C Sanhitha Reddy
**Presenter:** A.C Sanhitha Reddy (Register Number: CB.SC.U4CSE23206)  
**Course:** Neural Networks and Deep Learning Frameworks (23CSE473) — Semester VII  
**Project:** MediPaw — Multi-Modal Veterinary Triage Pipeline  
**Assigned Individual Modules:** Eye CNN (Ocular Pathology) & U-Net Wound Segmentation (YOLOv8 Integration)  
**Design System:** Template A (Clinical AI: Deep Navy #0C2340, Teal #0D9488, Cyan #0891B2, White #FFFFFF)  
**Total Slide Count:** 44 Substantive Slides  

---

### Section 1: Introduction and Motivation (Slides 1–7)
- **Slide 1:** Title Slide (Official MediPaw Logo, Tagline 'every paw deserves a chance', Presenter Credentials, Semester VII).
- **Slide 2:** Presentation Roadmap (7 Core Academic Sections from Clinical Need to Quality Assurance).
- **Slide 3:** MediPaw Project Overview & Triage Pipeline (Emergency intake crisis, superficial vs internal diagnostic branches).
- **Slide 4:** Veterinary Image Analysis Problem Statement (Fur occlusions, specular reflections, severe class imbalance).
- **Slide 5:** Motivation for Automated Eye & Wound Assessment (Preventing corneal perforation within 48h, ruler inaccuracies).
- **Slide 6:** Project Objectives & Formal Research Questions (Cost-sensitive loss, MobileNetV3 edge efficiency, combined Dice loss).
- **Slide 7:** Overall MediPaw System Architecture Diagram (End-to-end multi-modal dataflow and 576-dim feature handoff).

### Section 2: Background and Literature Review (Slides 8–13)
- **Slide 8:** Section 2 Divider (Background & Literature Foundations).
- **Slide 9:** CNN Fundamentals for Veterinary Image Classification (Local receptive fields, weight sharing, spatial downsampling).
- **Slide 10:** Feature Extraction Hierarchy in Deep Networks (Early edge primitives, mid-level tissue motifs, late pathology semantics).
- **Slide 11:** Task Formulation Spectrum: Classification vs Detection vs Semantic Segmentation (Granularity, outputs, metrics).
- **Slide 12:** Canine Ocular Pathology Classification Formulation (Discrete 4-class space, Softmax normalization).
- **Slide 13:** Literature Review: Veterinary AI & Ocular Diagnostics (Kim et al. 2020, Li et al. 2021, Howard et al. 2019, MediPaw).

### Section 3: Eye CNN Dataset and Methodology (Slides 14–21)
- **Slide 14:** Section 3 Divider (Eye CNN Dataset & Methodology).
- **Slide 15:** Eye CNN Module Overview & Design Philosophy (1.52M parameters, 14.2 ms CPU latency, 576-dim feature export).
- **Slide 16:** Ocular Dataset Source & Class Taxonomy (6,365 total crops: conjunctivitis, entropion, eyelid lump, healthy).
- **Slide 17:** Dataset Statistics & Patient-Level Split Distribution (5,570 Train / 531 Val / 264 Held-Out Test crops).
- **Slide 18:** Preprocessing & Bounding-Box Crop Extraction Pipeline (5% padding margin, 16x16 minimum filter, bilinear resize).
- **Slide 19:** Class-Balancing Strategy & Online Data Augmentation (Calculated inverse-frequency class weights, spatial/color jitter).
- **Slide 20:** Eye CNN Deep Architecture: MobileNetV3-Small (Depthwise separable convolutions, SE blocks, 576-dim head).
- **Slide 21:** Training Methodology & Hyperparameters (AdamW, CosineAnnealingLR, cost-sensitive loss, validation F1 checkpointing).

### Section 4: Eye CNN Results and Analysis (Slides 22–27)
- **Slide 22:** Section 4 Divider (Eye CNN Results & Analysis).
- **Slide 23:** Training and Validation Convergence Curves (Loss minimization to 0.423, validation F1 plateau at 84.38%).
- **Slide 24:** Held-Out Test-Set Evaluation Methodology (264 unseen canine crops, 82.95% accuracy, 82.89% macro F1).
- **Slide 25:** Per-Class Accuracy, Precision, Recall & F1 Scores (100% recall on conjunctivitis, 98.11% precision on eyelid lumps).
- **Slide 26:** Confusion Matrix Analysis & Misclassification Trends (Brachycephalic wrinkle confusion, surgical safety).
- **Slide 27:** Explainable AI: Real Grad-CAM Visual Attribution (Focal heatmap localization over eyelid folds and corneal margins).

### Section 5: U-Net Architecture and Implementation (Slides 28–34)
- **Slide 28:** Section 5 Divider (U-Net Wound Segmentation Architecture).
- **Slide 29:** Wound Segmentation Problem & Clinical Motivation (Canine bite trauma, non-convex boundaries, ruler errors).
- **Slide 30:** Task Distinction: YOLOv8 Detection vs U-Net Segmentation (Macro instance BBox vs micro sub-pixel contour).
- **Slide 31:** U-Net Architecture Overview & Parameter Budget (Symmetric U-topology, 32 base filters, 7.76M parameters).
- **Slide 32:** Contracting Path, Bottleneck & Skip Connections (Down blocks, 16x16 bottleneck, high-res skip concat).
- **Slide 33:** Dual Loss Formulations: BCE vs Soft Dice vs Combined Loss (Mathematical derivation, boundary sharpness trade-offs).
- **Slide 34:** Annotation Reality Check: Bounding Boxes vs Masks (Scientific integrity notice: 41 YOLO BBoxes, zero fabricated masks).

### Section 6: U-Net Inference and Evaluation (Slides 35–39)
- **Slide 35:** Section 6 Divider (U-Net Inference & Evaluation).
- **Slide 36:** U-Net Training Implementation & Checkpoint Protocols (DataLoader, loss optimization, defensive fallback flags).
- **Slide 37:** Inference Workflow & `segment_wounds()` Unified API (YOLO detection, ROI crop, 256x256 mask, JSON generation).
- **Slide 38:** Real Wound Detection & Segmentation Visual Evidence (YOLO BBox + U-Net green overlay contour, 12.4% area).
- **Slide 39:** Surface Area Calculation & Evaluation Status (Pixel counting formula, verified detection mAP@50: 82.62%).

### Section 7: Integration, Quality Assurance and Conclusion (Slides 40–44)
- **Slide 40:** Section 7 Divider (System Integration & Quality Assurance).
- **Slide 41:** Eye CNN & U-Net Backend Integration (FastAPI REST endpoints, JSON schemas, 576-dim ViT feature handoff).
- **Slide 42:** Automated Testing Suite: 100% Pass Rate on Sanhitha's Modules (8 dedicated test cases: unit, integration, boundary).
- **Slide 43:** Summary of Architectural Ablation Findings (MobileNetV3 vs EfficientNet, augmentation drop, class-weight necessity).
- **Slide 44:** Conclusion & Individual Contributions Summary (Deliverables summary, clinical limitations, production readiness).
