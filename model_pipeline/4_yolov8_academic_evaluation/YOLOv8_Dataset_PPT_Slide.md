# Slide X: YOLOv8 Unified Dataset Engineering
### Category: Dataset Composition & Class Simplification

**Dataset Architecture:** We structurally merged two distinct veterinary trauma datasets to create the `yolo_merged_wounds` dataset, maximizing the volume of diverse clinical scenarios.

| Dataset Split | Total Images | Positive Images (+ve) | Negative Images (-ve) | Bounding Boxes |
| :--- | :--- | :--- | :--- | :--- |
| **Train Set** | 338 | 146 | 192 | 154 |
| **Validation Set** | 97 | 46 | 51 | 47 |
| **Test Set** | 48 | 19 | 29 | 19 |
| **TOTAL** | **483** | **211** | **272** | **220** |

---

# Slide Y: Noise Suppression & Negative Control
### Category: Mitigating False Positives via Dataset Curation

> **The Problem:** The AI was accidentally guessing that healthy fur and human hands were wounds.
> 
> **The Solution:** 
> * **Simplified the Goal:** We stopped separating wounds by animal type (dog, cat, cow) and just trained it to find "Wounds."
> * **Taught it what "Normal" looks like:** We showed the AI 272 pictures of perfectly healthy animals and vet clinics with zero wounds. This taught the AI to ignore background noise and eliminated false alarms.
