# MediPaw Review 2: Deep Learning Hyperparameters & Architecture Tables
**Systemic Veterinary Skin Disease Classifier (CNN 1 — EfficientNet-V2)**
*Tabular Presentation Slides (Formatted exclusively as tables for PowerPoint / Marp slides)*

---

# Slide 1: Input, Normalization & Data Augmentation
### Category: Input Processing & Dataset Diversity

| Category / Feature | Hyperparameter | Our Config Value | Clinical & Engineering Justification |
| :--- | :--- | :--- | :--- |
| **Input** | **Input Image Size** | **`224 × 224 × 3` (RGB Tensors)** | Standardizes clinical dermatological photographs into a uniform aspect ratio without VRAM overflow. |
| **Input** | **Batch Size** | **`64` Tensors per batch** | Optimizes computational occupancy on Tesla T4 GPUs while generating smooth parameter gradient updates. |
| **Normalization** | **Input Tensor Norm** | **`Custom Veterinary Norm`** <br> *(Mean: `[0.526, 0.453, 0.424]`)* | Replaces ImageNet defaults with statistics computed directly across veterinary fur coats to enhance Erythema (redness) contrast. |
| **Augmentation** | **Scale Bounds (Zoom/Crop)** | **`RandomResizedCrop (0.8–1.0)`** | Exposes the CNN to lesion appearances at varied field-of-view magnifications (80% to 100% scale). |
| **Augmentation** | **Rotation Bound** | **`RandomRotation (±15°)`** | Enforces rotation-invariant lesion detection regardless of mobile or clinical camera orientation. |
| **Augmentation** | **Color & Brightness** | **`ColorJitter (±20%)`** | Rendered immune to lighting variance ($\sigma=38.4$), overexposed clinical flash, or shadowy exam rooms. |
| **Augmentation** | **Horizontal Flip** | **`RandomHorizontalFlip (p=0.5)`** | Doubles functional epidermal orientation variety without altering underlying pathology semantics. |

---

# Slide 2: Convolutional & Backbone Architecture
### Category: Hierarchical Feature Extraction & Convolution Layers

| Category / Feature | Hyperparameter | Our Config Value | Clinical & Engineering Justification |
| :--- | :--- | :--- | :--- |
| **Convolution Layer** | **Number of Convolution Layers** | **`100+ Layers`** <br> *(`EfficientNet-V2-Small` Backbone)* | Provides deep hierarchical abstraction capable of capturing low-level fur texture up to complex annular ringworm plaques. |
| **Convolution Layer** | **Number of Filters** | **`24 to 256 Filters`** <br> *(Dynamic Stage Scaling)* | Progressively expands channel depth across 6 feature extraction stages while avoiding parameter inflation in early layers. |
| **Convolution Layer** | **Filter (Kernel) Size** | **`3×3` and `5×5` kernels** <br> *(Fused-MBConv Blocks)* | Leverages mixed kernel receptivity to capture fine scaling crusts (`3×3`) as well as broader ringworm margins (`5×5`). |
| **Convolution Layer** | **Stride** | **`1` (Inside blocks)** <br> **`2` (For spatial downsampling)** | Stride 1 preserves lesion feature resolution; Stride 2 accomplishes clean downsampling without feature loss. |
| **Convolution Layer** | **Padding** | **`Zero-Padding (value=0)`** with Center Crop | Prevents anatomical pet geometry and circular lesion boundaries from suffering aspect-ratio distortion during resizing. |
| **Convolution Layer** | **Dilation Rate** | **`1` (Standard dense receptive fields)** | Maintained continuous receptive fields without atrous convolution gaps so microscopic fur structures aren't missed. |
| **Convolution Layer** | **Groups (Grouped & Depthwise)** | **`Fused-MBConv`** <br> *(Depthwise & Inverted Bottlenecks)* | Replaced classical full-channel convolutions with depthwise inverted bottlenecks, allowing specialized extraction for micro-texture lesions. |

---

# Slide 3: Initializations, Activations & Pooling
### Category: Initialization Algorithms, Nonlinearities & Downsampling

| Category / Feature | Hyperparameter | Our Config Value | Clinical & Engineering Justification |
| :--- | :--- | :--- | :--- |
| **Weight Initialization**| **Weight Initialization Algorithm** | **`He-Normal / Kaiming Normal`** <br> *(mode=`fan_out`, `leaky_relu`)* | Maintains stable forward gradient variance across deep classification linear heads without vanishing/exploding signals. |
| **Bias Initialization** | **Starting Bias Values** | **`0.0` (Zero Initialization)** | All dense classifier head biases and BatchNorm offsets initialize directly at zero, eliminating bias drift before convergence. |
| **Activation** | **Activation Function** | **`SiLU / Swish` (Backbone)** <br> **`LeakyReLU` (Diagnostic Head)** | SiLU enhances smooth gradient propagation across residual layers; LeakyReLU ensures responsive gradients in our custom head. |
| **Activation** | **Negative Slope (Activation Alpha)**| **`0.01` (`negative_slope=0.01`)** | Prevents dead neuron state collapse in the 512-dense representation feature bottleneck during aggressive backward loss propagation. |
| **Pooling Layer** | **Pooling Type** | **`Global Average Pooling (GAP)`** <br> *(`AdaptiveAvgPool2d((1, 1))`)* | Condenses $7 \times 7$ spatial dimensions into a uniform feature vector without parameter-heavy flattening layers that trigger memorization. |
| **Pooling Layer** | **Pool Size** | **`(1, 1)` (Global Spatial Mapping)** | Dynamically maps complex 2D spatial features into clear scalar descriptive values per channel. |
| **Pooling Layer** | **Pool Stride** | **`1` (Global single-step aggregation)**| Synchronized with global pooling to output exactly one summarized descriptor per learned feature channel. |

---

# Slide 4: Normalization & Dense Classifier Head
### Category: Normalization Layers, Fully Connected Projection & Output Targets

| Category / Feature | Hyperparameter | Our Config Value | Clinical & Engineering Justification |
| :--- | :--- | :--- | :--- |
| **Normalization** | **Batch Normalization** | **`Enabled`** <br> *(Active in Backbone & Custom Head)* | Applied after convolutional stages and before linear head activations, maintaining constant representation statistics across varying batches. |
| **Normalization** | **Batch Normalization Momentum** | **`0.99` (`momentum=0.99`)** | Stabilizes running mean and variance distribution scaling inside our 512-dense classification head across shuffling mini-batches. |
| **Normalization** | **Batch Normalization Epsilon** | **`1e-5` (`eps=1e-5`)** | Maintains mathematical stability during variance normalization across high-contrast animal fur boundaries. |
| **Fully Connected** | **Number of Dense Layers** | **`2 Dense Layers`** <br> *(`in_features → 512 → 6`)* | Two-step linear mapping breaks down raw feature tensors before making final clinical diagnostic assertions. |
| **Fully Connected** | **Number of Neurons (Hidden Units)** | **`512 Neurons / Units`** | Provides sufficient representational capacity to resolve complex overlaps between fungal and allergic dermatitis without parameter bloat. |
| **Output Layer** | **Output Activation** | **`Linear Logits`** <br> *(Trained via Softmax CrossEntropy)* | Raw logits produced by the final dense layer are transformed cleanly into normalized probabilities during cross-entropy optimization and inference. |
| **Output Layer** | **Number of Output Units** | **`6 Units / Diagnostic Classes`** | Exactly matches our systemic ontology: Fungal Infections, Allergic Dermatitis, Demodicosis Mange, Bacterial Dermatosis, Healthy Control, and Ringworm. |

---

# Slide 5: Loss Function, Optimization & Regularization
### Category: Objective Criteria & Parameter Update Dynamics

| Category / Feature | Hyperparameter | Our Config Value | Clinical & Engineering Justification |
| :--- | :--- | :--- | :--- |
| **Loss Function** | **Loss Function Type & Weights** | **`Class-Weighted Cross-Entropy`** <br> *(Bacterial Loss Weight = **`8.0×`**)* | Resolves our **11.7:1** class imbalance by applying an **8× gradient loss multiplier (`7.9939`)** whenever rare bacterial anomalies are misclassified! |
| **Loss Function** | **Label Smoothing Factor** | **`0.05` (5% Target Softening)** | Softens one-hot target vectors by 5%, discouraging extreme output logit overconfidence when classifying ambiguous triage cases. |
| **Optimizer** | **Optimizer Type** | **`AdamW` (Decoupled Weight Decay)** | Separates L2 weight decay penalties from adaptive gradient acceleration, preventing premature weight stagnation in deeper network layers. |
| **Optimizer** | **Base Learning Rate (LR)** | **`0.0001` (`1e-4`)** | Delivers stable convergence when fine-tuning pretrained Fused-MBConv depthwise convolutions without triggering gradient explosion. |
| **Optimizer** | **Momentum Equivalent** | **`Not Applicable for SGD`** <br> *(Managed via AdamW $\beta_1 = 0.9$)* | Since AdamW optimization is deployed, momentum velocity is governed algorithmically by exponential moving average first-moment parameters. |
| **Optimizer** | **Adam Beta 1 ($\beta_1$) & Beta 2 ($\beta_2$)**| **$\beta_1 = 0.9$ \| $\beta_2 = 0.999$** | $\beta_1$ maintains acceleration momentum; $\beta_2$ dampens noisy gradient step variance from inconsistent clinical room lighting. |
| **Optimizer** | **Optimizer Epsilon ($\epsilon$)** | **`1e-8` (`eps=1e-8`)** | Guarantees numerical stability during infinitesimal learning rate updates near phase convergence. |
| **Regularization** | **Dropout Rate (Head Dropout)** | **`0.4` (`40%` applied dually)** | Dual 40% dropout checkpoints before and after the 512-dense bottleneck ensure the model does not memorize exam table grain or camera flash glare. |

---

# Slide 6: Regularization, Scheduling & Early Stopping
### Category: Weight Penalties, Learning Schedules & Cutoff Thresholds

| Category / Feature | Hyperparameter | Our Config Value | Clinical & Engineering Justification |
| :--- | :--- | :--- | :--- |
| **Regularization** | **L1 Regularization (Sparsity)** | **`Disabled / 0.0`** | Avoided aggressive parameter zeroing to retain delicate visual feature detectors across similar rash presentations; relied on Decoupled L2 Decay instead. |
| **Regularization** | **L2 Regularization (Weight Decay)**| **`0.01` (`weight_decay=0.01`)** | Decouples weight decay from gradient updates, strictly suppressing overfitting on dominant classes (like Ringworm) while keeping weights generalized. |
| **Training Schedule**| **Learning Rate Scheduler** | **`CosineAnnealingLR` ($T_{max}=30$)**| Follows a smooth half-cosine decay trajectory over 30 epochs, suppressing late-stage loss oscillations and driving test accuracy to **`91.45%`**. |
| **Training Schedule**| **Two-Stage Warmup Protocol** | **`3 Epochs Frozen` (Warmup)** $\rightarrow$ <br> **`Unfreezing at Epoch 4`** | Isolates pretrained feature extractors while our custom Kaiming-initialized diagnostic head settles during Epochs 1–3, preventing catastrophic forgetting. |
| **Regularization** | **Early Stopping Status & Patience**| **`Enabled` (Patience = `10` Epochs)** | Permitted full feature refinement across 6,410 training photos while embedding automatic shutdown protection to guard against overtraining. |
| **Regularization** | **Gradient Clipping Threshold** | **`1.0` (`max_norm=1.0` L2 Norm)** | Prevents numerical divergence and destructive weight steps instantly after unfreezing the full EfficientNet backbone at Epoch 4. |

---

# Slide 7: Training Infrastructure, Hardware & Evaluation
### Category: Execution Limits, Precision, Device Infrastructure & Benchmarks

| Category / Feature | Hyperparameter | Our Config Value | Clinical & Engineering Justification |
| :--- | :--- | :--- | :--- |
| **Training** | **Number of Epochs** | **`30 Epochs` (Max Runtime Cutoff)** | Provided ample iterative runtime for Cosine Annealing decay while early stopping actively guarded against overfitting. |
| **Training** | **Shuffle Data** | **`True` (Train) \| `False` (Val/Test)** | Shuffling training batches breaks consecutive temporal class clustering; static evaluation loaders ensure repeatable clinical metric benchmarking. |
| **Training** | **Mixed Precision Training** | **`Disabled` (Standard FP32 High-Precision)**| Maintained complete 32-bit floating point precision to guarantee zero underflow across extreme class-weighted gradient scalings (8× multiplier). |
| **Training** | **Random Seed** | **`42` (Fixed Integer Seed)** | Enforces identical dataset split behavior and deterministic experimental replication across Google Colab GPU runtimes. |
| **Validation** | **Validation Split & Deduplication**| **`70% Train / 15% Val / 15% Test`** <br> *(with **`100% MD5 Deduplication`**)* | Maintains proportional representation of minority conditions; blocked **1,143 duplicate clones** across splits to verify authentic generalization. |
| **Validation** | **Cross Validation Status** | **`Disabled` (Fixed Stratified Split)**| Prioritized strict zero-leakage deduplication over rotational folds to assure authentic out-of-distribution evaluation across 6,410 medical images. |
| **Evaluation** | **Evaluation Metric** | **`Accuracy (91.45%), F1 (84.91%), & CM`**| Evaluated beyond plain accuracy using clinical reliability metrics, proving **100% Recall on Mange & Healthy controls** to prevent triage errors. |
| **Hardware** | **Device & Worker Threads** | **`Tesla T4 GPU` (Colab CUDA Engine)** <br> *(with **`num_workers=2, pin_memory=True`**)*| Leveraged cloud tensor acceleration cores and asynchronous RAM streaming to complete full deep 30-epoch fine-tuning without CPU bottlenecks. |

---
*Generated for MediPaw Veterinary Skin Diagnostic System — Tabular Presentation Slides.*
