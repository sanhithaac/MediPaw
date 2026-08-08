# YOLOv8s Unified Wound Detection: Hyperparameters & Configuration

This document outlines the architectural configurations and hyperparameters used to train the YOLOv8s (Small) model on the unified "Wound" dataset (all species injuries mapped to Class 0). 

These parameters were explicitly chosen to balance real-time emergency triage speed (< 15ms inference) with complex spatial detection across varying lighting and trauma scales.

---

## 1. Architectural Parameters
| Parameter | Value | Justification for Triage |
| :--- | :--- | :--- |
| **Model Backbone** | YOLOv8s (Small) | Provides the optimal balance between high precision and ultra-fast inference speed suitable for mobile veterinary clinics. |
| **Anchor System** | Anchor-Free | Allows the model to detect micro-abrasions and massive traumas natively without being constrained by predefined box shapes. |
| **Feature Pyramid** | Path Aggregation (PAFPN) | Evaluates features across multiple spatial layers simultaneously, enabling robust detection across varying injury sizes. |
| **Number of Classes (`nc`)** | 1 (`Wound`) | All injuries (cow, cat, dog) unified to prevent classification confusion. Uninjured subjects act as negative controls (background). |

---

## 2. Optimization & Training Hyperparameters
| Hyperparameter | Value | Description & Impact |
| :--- | :--- | :--- |
| **Epochs** | 50 | Total maximum passes over the dataset. Capped at 50 to prevent overfitting on clinical data. |
| **Patience (Early Stopping)** | 15 | Halts training if Validation Loss does not improve for 15 consecutive epochs (prevents model degradation and overfitting). |
| **Batch Size** | 16 | The number of images processed simultaneously before a weight update. Optimal for T4 GPUs without causing VRAM bottlenecks. |
| **Image Resolution (`imgsz`)** | 640 x 640 | Standardized input size (Letterbox aspect-ratio preservation) to maintain spatial integrity of wounds without squishing them. |
| **Optimizer** | AdamW | Adaptive Moment Estimation with Weight Decay. Highly effective at navigating complex, sparse loss landscapes. |
| **Learning Rate (`lr0`)** | 0.001 | The initial step size for gradient descent. Fast enough to learn quickly but small enough to converge smoothly. |
| **Weight Decay** | 0.01 | Adds an L2 regularization penalty to the network's weights, explicitly fighting overfitting. |

---

## 3. Data Augmentation Hyperparameters
Data augmentations force the model to learn invariant features (the actual wound) rather than memorizing the orientation or lighting of a specific clinic room.

| Augmentation | Value | Clinical Relevance |
| :--- | :--- | :--- |
| **Mosaic** | 1.0 (100%) | Combines 4 images into 1 during training. Teaches the model to find wounds at smaller scales and in unexpected spatial locations. |
| **Degrees (Rotation)** | 15.0° | Randomly rotates images by up to 15 degrees. Simulates a veterinarian holding a camera at a slight angle during an emergency. |
| **HSV Saturation (`hsv_s`)** | 0.7 | Randomly alters image saturation. Prevents the model from relying solely on the "redness" of blood, forcing it to learn texture. |
| **HSV Value/Brightness (`hsv_v`)** | 0.4 | Randomly alters exposure. Simulates varying lighting conditions (bright clinic operating rooms vs dimly lit outdoor rescues). |

---

## 4. Hardware Configuration
| Component | Requirement |
| :--- | :--- |
| **Accelerator** | NVIDIA T4 GPU (or equivalent) |
| **VRAM Required** | ~16 GB (Batch 16 @ 640px) |
| **Mixed Precision** | FP16 (Automatic) |
