# YOLOv8 Hyperparameter Tuning for Wound Detection

**Objective:** Optimize YOLOv8s for real-time emergency triage (< 15ms) while maintaining high detection precision across varying wound sizes, species, and clinical lighting conditions.

## ⚙️ Optimization & Automated Tuning Strategy
* **Automated Genetic Algorithm Tuning:** Before final training, the model underwent an automated hyperparameter tuning phase (30 generations). This process utilized genetic algorithms to systematically mutate parameters (Learning Rate, Momentum, Weight Decay) to mathematically find the optimal configuration for maximum mAP.
* **Epochs & Early Stopping:** Final training capped at `50` epochs with a patience of `15`. This prevents the model from overfitting to specific clinical data.
* **Optimizer Setup:** Utilized **AdamW** with an optimized Learning Rate of `0.001` and Weight Decay of `0.01` to effectively navigate complex loss landscapes and combat overfitting.
* **Batch & Resolution:** Batch size `16` on `640x640` images. This preserves the spatial integrity of wounds (no squishing) while optimizing 16GB T4 GPU VRAM usage.

## 🎨 Data Augmentations (Clinical Simulation)
* **Mosaic (100%):** Combines 4 images into 1. Teaches the model to detect micro-abrasions in unexpected spatial locations.
* **Rotation (±15°):** Simulates a veterinarian or rescuer holding a camera at a slight angle during an active emergency.
* **Color Space (HSV):** High variance in Saturation (`0.7`) and Brightness (`0.4`). Forces the model to learn the structural *texture* of wounds rather than relying solely on the red color of blood or bright operating room lights.
