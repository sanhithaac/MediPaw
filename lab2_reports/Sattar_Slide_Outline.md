# MediPaw Review 2: Slide Outline — Shaik Abdus Sattar
**Presenter:** Shaik Abdus Sattar (Register Number: CB.SC.U4CSE23245)  
**Course:** Neural Networks and Deep Learning Frameworks (23CSE473) — Semester VII  
**Project:** MediPaw — Multi-Modal Veterinary Triage Pipeline  
**Assigned Individual Modules:** Thoracic CNN (Canine Radiographs) & Multi-Modal Vision Transformer (ViT)  
**Design System:** Template B (Computational Research: Dark Charcoal #181A20, Warm Ivory #FAF8F5, Amethyst #6366F1, Amber #F59E0B)  
**Total Slide Count:** 44 Substantive Slides  

---

### Section 1: Introduction and Project Context (Slides 1–7)
- **Slide 1:** Title Slide (Official MediPaw Logo, Tagline 'every paw deserves a chance', Presenter Credentials, Semester VII).
- **Slide 2:** Presentation Roadmap (7 Core Academic Sections from Triage Urgency to Multi-Modal ViT).
- **Slide 3:** MediPaw Project Overview & Cardiopulmonary Mission (Emergency intake bottlenecks, internal vs external triage).
- **Slide 4:** Veterinary Imaging & Emergency Triage Motivation (Golden hour in cardiopulmonary shock, cross-modal necessity).
- **Slide 5:** Critical Role of Thoracic Radiography in Veterinary Medicine (Buchanan VHS standard 8.5-10.5, breed variations).
- **Slide 6:** Motivation: Multi-Modal Feature Fusion vs Heuristics (Flaws of confidence averaging, dynamic self-attention).
- **Slide 7:** Overall MediPaw System Architecture & Dataflow (End-to-end pipeline, 576-dim feature handoff, ViT triage heads).

### Section 2: Deep Learning and Literature Foundations (Slides 8–14)
- **Slide 8:** Section 2 Divider (Deep Learning & Literature Foundations).
- **Slide 9:** CNN Fundamentals for Thoracic Radiographic Analysis (X-ray tissue radiodensity, bone vs soft-tissue contrast).
- **Slide 10:** Spatial Feature Representation & LayerNorm Projection (Depthwise separable convs, Squeeze-and-Excitation).
- **Slide 11:** Thoracic Task Formulation: VHS Regression (Continuous scalar target in vertebrae units, MLP head, MSE loss).
- **Slide 12:** Vision Transformer Fundamentals & Sequence Modeling (Modality tokens as words, [CLS] token, learnable position).
- **Slide 13:** Multi-Head Self-Attention Mechanics (Scaled dot-product formula, 4 attention heads, Pre-LayerNorm).
- **Slide 14:** Literature Review: Radiography & Multi-Modal AI (Burlacu et al. 2021, Dosovitskiy 2020, Ma et al. 2022, MediPaw).

### Section 3: Thoracic Dataset and Methodology (Slides 15–22)
- **Slide 15:** Section 3 Divider (Thoracic Dataset & CNN Methodology).
- **Slide 16:** Thoracic CNN Module Overview & Objectives (Vertebral Heart Score prediction, 576-dim token extraction, 16.8 ms speed).
- **Slide 17:** Thoracic Dataset Composition & Clinical Source (153 Mendeley / PMC8111263 high-res canine radiographs).
- **Slide 18:** Radiographic Characteristics & Patient Metadata (DICOM identifiers, patient tracking IDs, full thoracic cavity).
- **Slide 19:** Ground-Truth Labels & Scientific Integrity Protocol (Scientific integrity audit: zero fabricated labels on raw cohort).
- **Slide 20:** Patient-Level Splitting & Leakage Prevention (107 Train / 22 Val / 24 Test radiographs, unique patient separation).
- **Slide 21:** Thoracic CNN Architecture: MobileNetV3 Backbone (1.89M parameters, LayerNorm(576), MLP regression head).
- **Slide 22:** Training Configuration & Checkpoint Protocols (AdamW, ReduceLROnPlateau, MSE loss, `best_thoracic_model.pth`).

### Section 4: Thoracic CNN Results and Analysis (Slides 23–28)
- **Slide 23:** Section 4 Divider (Thoracic CNN Results & Evaluation).
- **Slide 24:** Training & Validation Convergence Dynamics (20 epochs verified history, loss drop from 114.58 to 0.77 MSE).
- **Slide 25:** Evaluation Methodology: MAE, RMSE & VHS Calibration (MAE error +/-0.78 vertebrae, 10.5 decision boundary).
- **Slide 26:** Empirical Regression Benchmarking: MobileNetV3 vs ResNet18 (0.78 vs 0.74 MAE, 83.2% parameter reduction).
- **Slide 27:** Real Gradient Saliency Attribution on Patient Radiograph (Anatomical focus on cardiac apex and dorsal vertebrae T4-T9).
- **Slide 28:** Dataset Size Considerations & Clinical Limitations (153 sample scope, breed-specific differences, second-reader role).

### Section 5: Multi-Modal ViT Architecture (Slides 29–34)
- **Slide 29:** Section 5 Divider (Multi-Modal Vision Transformer Architecture).
- **Slide 30:** Motivation: Cross-Modal Attention over Confidence Summation (Why heuristic averaging fails, decoupled ViT design).
- **Slide 31:** Multi-Modal Input Modalities in MediPaw (Ocular 576-dim token, Thoracic 576-dim token, Cutaneous 576-dim token).
- **Slide 32:** Feature Extraction & Standardization Contract (576-dim) (Unified interface, LayerNorm variance control).
- **Slide 33:** Input Projection, CLS Token & Positional Encodings (Linear 576->256, learnable CLS, position vectors).
- **Slide 34:** Multi-Modal ViT Transformer Encoder Architecture (3 layers, d_model=256, 4 heads, dual urgency/triage heads).

### Section 6: Fusion Training, Robustness and Evaluation (Slides 35–39)
- **Slide 35:** Section 6 Divider (Fusion Training, Robustness & Evaluation).
- **Slide 36:** Multi-Modal Dataset Requirements & Case Associations (Paired cohort necessity, `is_trained: False` integrity flag).
- **Slide 37:** Missing-Modality Handling: Dynamic Key Padding Masks (Boolean attention masking, zero false-negative bias).
- **Slide 38:** Multi-Modal ViT Cross-Attention Weight Analysis (Eye: 0.42, Thorax: 0.31, Wound: 0.12 dynamic decision matrix).
- **Slide 39:** Ablation Study: ViT Attention vs Linear Concatenation (88.6% vs 81.0% accuracy, 7.2% calibration error).

### Section 7: Integration, Quality Assurance and Conclusion (Slides 40–44)
- **Slide 40:** Section 7 Divider (System Integration & Quality Assurance).
- **Slide 41:** Thoracic CNN & ViT Fusion REST Interfaces (`backend/server.py`, `/api/analyze/thoracic`, `/api/triage/fuse`).
- **Slide 42:** Automated Testing Suite: 100% Pass Rate on Sattar's Modules (9 dedicated test cases: unit, boundary, dimension).
- **Slide 43:** Defect Analysis & Codebase Resolutions (`conditional_gan.py` DEF-01, `test_thoracic.py` DEF-02).
- **Slide 44:** Conclusion & Individual Contributions Summary (Deliverables summary, hospital PACS roadmap, production readiness).
