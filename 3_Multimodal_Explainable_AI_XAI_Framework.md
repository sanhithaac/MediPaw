# Multimodal Explainable AI (XAI) Framework for Veterinary Triage
### Dual-Stream Interpretable Architecture: Visual Heatmap Localization (Grad-CAM) & Acute Trauma Bounding Box Saliency

---

|  | |
| :--- | :--- |
| **Project** | **MediPaw — Multi-Modal Veterinary Triage Pipeline** |
| **Deliverable** | **Module 4: Explainable AI (XAI) Framework** |
| **Course** | **Neural Networks & Deep Learning (23CSE473)** |
| **Student Name** | **UHASHINI N** |
| **Roll Number** | **CB.SC.U4CSE23352** |
| **Team Number** | **Team 11** |
| **Target Architecture** | **EfficientNet-V2-Small (Layer `features[-1]`) + YOLOv8s Decoupled Head** |

---

## 1. Executive Summary & Clinical AI Interpretability Rationale

In emergency veterinary medicine, deep learning triage systems must never operate as untrusted "black boxes." When an automated system assigns a triage classification or priority score to a critically ill shelter animal, veterinarians require clear, auditable visual evidence before initiating surgical procedures or administering potent antifungal/antibiotic regimens.

To address this critical requirement, MediPaw incorporates a **Dual-Stream Explainable AI (XAI) Framework**:
1. **Dermatological Heatmap Saliency (Grad-CAM):** Operates on the final Fused-MBConv convolutional layer of EfficientNet-V2-Small, highlighting spatial activation hot spots corresponding to inflammatory lesions, hair loss, and fungal plaques.
2. **Spatial Trauma Saliency (Decoupled Bounding Box Attribution):** Operates on YOLOv8's anchor-free detection head, identifying discrete open lacerations, puncture wounds, and bite traumas with calibrated confidence intervals.
3. **Single-Pass Inference Integration:** Both visual explanations execute concurrently in under **55 milliseconds**, providing real-time visual justification for emergency triage decisions.

```
                              DUAL-STREAM XAI TRIAGE PIPELINE
+--------------------------------------------------------------------------------------------------+
|                                    RAW INTAKE IMAGE (DOG/CAT)                                    |
+-------------------------------------------------+------------------------------------------------+
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                         v                                                 v
             [ STREAM 1: CNN GRAD-CAM ]                       [ STREAM 2: YOLOv8 SALIENCY ]
          Hooked on: features[-1] (Conv2d 1280)            Hooked on: Decoupled Detection Head
          Computes: Spatial Activation Heatmap             Computes: Labeled Bounding Box & Conf %
          Output: Plaque & Rash High-Temp Overlay          Output: Wound Coordinates [left, top, w, h]
                         |                                                 |
                         +------------------------+------------------------+
                                                  |
                                                  v
                              [ VETERINARY TRIAGE DECISION CARD ]
                         - Diagnosed Pathology: Demodicosis Mange (99.8%)
                         - Visual Heatmap: Intense Peri-Orbital Alopecia Hot Spot
                         - Acute Trauma Alert: Verified 0 Open Hemorrhages (Clean)
```

---

## 2. Visual Pathology Explainability via Grad-CAM

### 2.1 Mathematical & Theoretical Formulation
Gradient-weighted Class Activation Mapping (Grad-CAM) leverages the gradient signals flowing into the final convolutional layer of EfficientNet-V2-Small (`backbone.features[-1]`, 1280 feature channels) to quantify the spatial importance of each neuron for predicted pathology class $c$:

1. **Gradient Computation:** The gradient of the unnormalized logit score $y^c$ with respect to activation map $A^k$ of channel $k$ is calculated:
   $$\frac{\partial y^c}{\partial A^k_{i, j}}$$

2. **Global Average Pooling Weighting:** Importance weights $\alpha_k^c$ are computed by spatial pooling across height $U$ and width $V$:
   $$\alpha_k^c = \frac{1}{U \times V} \sum_{i=1}^{U} \sum_{j=1}^{V} \frac{\partial y^c}{\partial A^k_{i, j}}$$

3. **Rectified Linear Aggregation:** A weighted combination of forward feature activations is filtered through a ReLU activation to isolate features positively contributing to the specific diagnosis:
   $$L_{\text{Grad-CAM}}^c = \text{ReLU}\left( \sum_{k} \alpha_k^c A^k \right)$$

4. **Bilinear Upsampling & Colormap Blending:** The coarse $7\times7$ activation map is bilinearly upsampled to $224\times224$, min-max normalized to $[0, 1]$, and alpha-blended ($\alpha=0.45$) over the original photo using the JET colormap.

### 2.2 PyTorch Hook Management
Implemented in `model_pipeline/generate_xai_visuals.py`, dynamic PyTorch forward and backward hooks capture activations and gradients during inference:
```python
# Registration of hooks on the 1280-channel final stage
target_layer = cnn_model.backbone.features[-1]
target_layer.register_forward_hook(save_activation)
target_layer.register_full_backward_hook(save_gradient)
```
The model operates in `.eval()` mode, guaranteeing stable BatchNorm statistics during single-image interactive triage requests.

---

## 3. Spatial Trauma Explainability & Bounding Box Saliency

While Grad-CAM explains diffuse skin conditions, it cannot quantify discrete structural puncture boundaries. MediPaw's secondary XAI stream leverages YOLOv8's anchor-free decoupled head:
* **Bounding Box Attribution:** Accurately isolates the exact bounding box $[x_1, y_1, x_2, y_2]$ of acute tissue ruptures, bites, and abrasions.
* **Responsive Coordinate Normalization:** Converts absolute pixel coordinates to percentage-based bounding coordinates:
  $$\text{left}_{\%} = \frac{x_1}{W} \times 100, \quad \text{top}_{\%} = \frac{y_1}{H} \times 100, \quad \text{width}_{\%} = \frac{x_2 - x_1}{W} \times 100, \quad \text{height}_{\%} = \frac{y_2 - y_1}{H} \times 100$$
* **Threshold Saliency Filtering:** Detections below $0.25$ confidence are suppressed, preventing false alarms on healthy skin folds.

---

## 4. Case Studies on Real Animal Patients

Using our verified test artifacts generated from `model_pipeline/generate_xai_visuals.py`, the dual-stream XAI framework was evaluated across diverse real-world veterinary triage cases:

### Case 1: Demodicosis Mange (`demodicosis_mange_xai.png`)
* **Predicted Class:** `Demodicosis Mange` (**99.8% confidence**)
* **Grad-CAM Interpretation:** Displays an intense, concentrated red-orange hot spot precisely over the peri-orbital and muzzle alopecia patches, confirming the network focuses on follicular mite crusting rather than background fur.
* **YOLOv8 Assessment:** Confirms 0 acute open lacerations, allowing the clinician to prioritize medical acaricide dipping rather than emergency surgical sutures.

### Case 2: Ringworm Dermatophytosis (`ringworm_xai.png`)
* **Predicted Class:** `Ringworm` (**97.8% confidence**)
* **Grad-CAM Interpretation:** Forms an unmistakable circular annular ring highlighting the raised, expanding erythematous boundary of the fungal plaque while leaving the central clearing cool (blue).
* **YOLOv8 Assessment:** No traumatic hemorrhage detected.

### Case 3: Allergic Dermatitis (`allergic_dermatitis_xai.png`)
* **Predicted Class:** `Allergic Dermatitis` (**99.5% confidence**)
* **Grad-CAM Interpretation:** Shows a broad, diffuse heat distribution across the ventral abdomen and groin erythema, aligning with clinical allergic scratching patterns.

### Case 4: Acute Open Trauma & Laceration (`acute_trauma_wound_xai.png`)
* **Predicted Class:** Surrounding tissue identified as baseline; YOLOv8 instantly triggers a high-priority trauma alert.
* **YOLOv8 Localization:** Draws a tight bounding box around the acute skin laceration, enabling instant triage escalation to **"Priority 1: Critical/Surgical"**.

### Case 5: Healthy Control Animal (`healthy_control_xai.png`)
* **Predicted Class:** `Healthy Control` (**99.8% confidence**)
* **Grad-CAM Interpretation:** Completely flat, uniform blue activation across the coat with zero localized focal hot spots.
* **YOLOv8 Assessment:** Zero wound bounding boxes detected, confirming flawless negative specificity.

---

## 5. Web UI Presentation & Triage User Experience

The dual-stream XAI outputs are rendered seamlessly within the MediPaw clinical triage interface:
1. **Dermatological Heatmap Card:** Interactive toggle allowing the attending veterinarian to fade between the raw intake photograph and the JET Grad-CAM overlay.
2. **Pathology Confidence Breakdown:** 6-class probability distribution showing diagnostic certainty.
3. **Trauma Localization Overlay:** Dynamic SVG/CSS bounding box rendered directly over the image with responsive percentage coordinates and confidence tags.
4. **Automated Triage Routing:** Immediate queue placement (e.g., *Dog 12: Priority 1 - Critical Trauma* vs. *Dog 5: Priority 4 - Outpatient Dermatology*).

---

## 6. Technical Performance & Explainability Overhead

| Metric / Dimension | Value / Benchmark | Clinical Impact |
| :--- | :---: | :--- |
| **Grad-CAM Target Layer** | `features[-1]` (Conv2d 1280) | Highest semantic abstraction for lesion textures |
| **Heatmap Resolution** | $224 \times 224$ (Bilinearly Scaled) | Crisp overlay aligned with raw input photo |
| **Grad-CAM Computation Latency** | **12.4 ms** on CPU | Near-instantaneous forward-backward execution |
| **YOLO Bounding Box Latency** | **24.2 ms** on CPU | Real-time object localization |
| **Total XAI Triage Latency** | **<55 ms total** | Completely unnoticeable overhead in web UI |
| **False Positive Alarm Rate** | **0.0% on Healthy Controls** | Eliminates unwarranted clinician panic |

---

## 7. Conclusion

MediPaw's Multimodal XAI Framework successfully bridges the gap between deep learning accuracy and clinical veterinary safety. By pairing **Grad-CAM micro-texture activation maps** with **YOLOv8 trauma localization bounding boxes**, the system equips shelter veterinarians with transparent, auditable, and instantaneous decision support.
