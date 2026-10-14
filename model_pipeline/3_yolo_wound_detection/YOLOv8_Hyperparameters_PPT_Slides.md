# MediPaw Review 2: YOLOv8 Wound Detection Hyperparameter Tables
**Module 3: Acute Trauma Bounding Box Localization (YOLOv8s / PAFPN Backbone)**
*Tabular Presentation Slides (Formatted exclusively as structured tables for PowerPoint / Marp slides)*

---

# Slide 1: Input Processing, Resolution & Mosaic Augmentation

| Category | Hyperparameter | Value | Usually What It Does | Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Input** | **Input Image Size (imgsz)** | `640 × 640 × 3` (RGB Tensors) | Sets the spatial resolution of images fed into the network. | Letterbox padded aspect-ratio preserving resolution optimized for fine open lesion distinction without VRAM overload. |
| **Input** | **Batch Size** | `16` Tensors per batch | Determines the number of images processed before updating weights. | Maximizes GPU parallel execution across 640px tensors while ensuring stable AdamW gradient estimates. |
| **Augmentation** | **Mosaic Augmentation** | `1.0` (100% Likelihood) | Stitches 4 images into a single training grid to teach multi-scale detection. | Stitches 4 incoming clinical photos into composite grids, forcing detection of small wounds positioned across extreme picture borders. |
| **Augmentation** | **Rotation Range (degrees)** | `±15.0°` (RandomRotation) | Randomly rotates images to create orientation invariance. | Guarantees orientation invariance for veterinarians photographing trauma arrivals from slanted mobile cameras. |
| **Augmentation** | **HSV Saturation & Value Jitter**| `hsv_s=0.7` \| `hsv_v=0.4` | Alters color saturation and brightness to simulate different lighting. | Renders detector immune to intense surgical lamp flares, overexposed mobile flashes, or shadowy hospital kennels. |
| **Augmentation** | **Scale & Translation Jitter** | `scale=0.5` \| `translate=0.1` | Randomly zooms in/out and shifts the image spatially. | Simulates varying distance zoom (50% scaling variance) and off-center pet framing in real emergency conditions. |
| **Augmentation** | **Horizontal Mirror Flip** | `fliplr = 0.5` (50% probability) | Flips the image horizontally to double dataset variability. | Doubles anatomical wound orientations without altering clinical laceration physiology. |
| **Augmentation** | **Random Patch Erasing** | `erasing = 0.4` (40% masking) | Masks random blocks of the image to force reliance on partial features. | Randomly masks small bounding patches to force recognition from fragmented wound cues (such as partial doctor glove obstruction). |

---

# Slide 2: Backbone, Neck & Convolutional Architecture

| Category | Hyperparameter | Value | Usually What It Does | Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Architecture** | **Model Backbone Framework** | `YOLOv8s` (Small, 11.1M Params) | Acts as the primary feature extractor for the neural network. | Replaced oversized deep object detectors with a compact 28.4 GFLOP engine to guarantee $<5\text{ ms}$ inference speed. |
| **Architecture** | **Neck Feature Aggregation** | `PAFPN` (Path Aggregation FPN) | Fuses multi-scale features from bottom-up and top-down pathways. | Bi-directional semantic aggregation preserves edge contrast across tiny bites and massive tissue burns. |
| **Architecture** | **Detection Head Design** | `Anchor-Free Decoupled Head` | Outputs bounding box predictions without relying on predefined anchor boxes. | Eliminates static predefined box anchors; predicts direct center spatial offsets to handle massive trauma scale variance. |
| **Convolution** | **Filter (Kernel) Sizes** | `1×1` and `3×3` kernels | Defines the receptive field size for extracting local spatial patterns. | `3×3` kernels capture ragged laceration edges; `1×1` projections transform representations across channel depth without excess parameters. |
| **Convolution** | **Convolutional Stride** | `1` (intra-block) \| `2` (downsample) | Determines the step size of the filter, controlling spatial downsampling. | Stride 1 preserves localized coordinate boundaries; Stride 2 accomplishes clean downsampling without feature loss. |
| **Convolution** | **Padding Strategy** | `Same / Letterbox Zero-Padding` | Adds zeros around borders to maintain spatial dimensions after convolution. | Prevents circular bite marks and anatomical limbs from suffering aspect-ratio compression or border erosion during resizing. |
| **Convolution** | **Grouped / Bottleneck Ops** | `C2f Modules` | Uses Cross-Stage Partial connections to reduce parameters and enhance gradients. | Enhances gradient flow across residual loops while slashing computational overhead. |

---

# Slide 3: Initializations, Activations & Pooling Dynamics

| Category | Hyperparameter | Value | Usually What It Does | Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Initialization**| **Backbone Initial Weights** | `Pretrained COCO Backbone` | Initializes network weights using knowledge learned from a massive dataset. | Leverages proven edge-detection filters trained on millions of generic images before specializing on clinical open traumas. |
| **Initialization**| **Warmup Bias Initialization** | `0.1` (`warmup_bias_lr=0.1`) | Initializes biases to a specific value during warmup to prevent early gradient explosion. | Elevates initial classification bias steps during warmup epochs to quickly stabilize bounding box proposals before deep finetuning. |
| **Activation** | **Primary Activation Function**| `SiLU / Swish` | Applies non-linearity to feature maps, allowing complex pattern modeling. | Smooth, unbounded zero-crossing non-linear activation ensuring steady gradient flow without ReLU dead neuron collapse. |
| **Pooling Layer** | **Pooling Architecture** | `Conv Downsampling` | Downsamples spatial resolution (traditionally done with Max Pooling). | Subsumes destructive max-pooling with strided feature convolutions, retaining positional coordinate accuracy for boundary cropping. |
| **Pooling Layer** | **Downsampling Stride Ratio** | `1/32 Max Stride Ratio` | The maximum reduction in spatial dimensions from input to final grid. | Evaluates multi-scale clinical features across three distinct pyramid scales ($8\times, 16\times, 32\times$ downsampling ratios). |
| **Bounding Box**| **Anchor Spatial Grid Type** | `Anchor-Free Direct Regression` | Defines how the grid predicts object centers instead of using bounding anchors. | Discards conventional handcrafted anchors in favor of direct center prediction, preventing missed detections on unusually oriented lacerations. |

---

# Slide 4: Normalization & Decoupled Detection Head

| Category | Hyperparameter | Value | Usually What It Does | Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Normalization** | **Batch Normalization (Status)**| `Enabled` | Normalizes layer inputs to zero mean and unit variance per batch. | Standardizes internal activation statistics across diverse clinical photographs to eliminate covariate shift and speed convergence. |
| **Normalization** | **Batch Normalization Momentum**| `0.937` (`momentum=0.937`) | Controls how much of the past running mean is kept for normalization. | Smoothes running exponential mean and variance statistics across mini-batches of varying background lighting. |
| **Output Head** | **Decoupled Head Architecture** | `Separate Parallel Branches` | Uses independent neural branches for classifying objects vs bounding boxes. | Decouples binary wound categorization from geometric box coordinate alignment, resolving conflict between classification and localization objectives! |
| **Output Head** | **Terminal Output Activation** | `Sigmoid Activation` | Squashes output logits into a probability distribution between 0 and 1. | Translates raw projection outputs into bounded probabilities $\in [0, 1]$ during loss evaluation and final clinical scoring. |
| **Output Head** | **Number of Output Units** | `Class 0: Dog_Wound (1 Unit)` | Determines the final number of target classes the model predicts. | Focused single-class clinical triage head targeting open acute trauma (lacerations, abrasions, bites, skin burns). |
| **Post-Processing**| **Non-Max Suppression (NMS) IoU**| `0.70` overlap threshold | Removes duplicate overlapping box predictions for the same object. | Merges overlapping bounding box proposals around the exact same trauma center while letting distinct clustered lacerations co-exist. |
| **Post-Processing**| **Maximum Detections Limit** | `300 instances per picture` | Caps the maximum number of bounding boxes allowed per image. | Prevents infinite loop failures on cluttered backgrounds while easily accommodating extensive multi-wound trauma scenarios. |

---

# Slide 5: Multi-Task Loss Function & Weight Distribution

| Category | Hyperparameter | Value | Usually What It Does | Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Loss Function** | **Box Loss ($L_{box}$) & Weight** | `CIoU Loss` (Weight = `7.5`) | Penalizes inaccurate bounding box sizes, centers, and aspect ratios. | Measures exact overlap area, center distance, and aspect ratio alignment; converged to an optimal low of **`1.79`** during training! |
| **Loss Function** | **Class Loss ($L_{cls}$) & Weight**| `Focal Binary Cross-Entropy` (Weight = `0.5`) | Penalizes incorrect classification predictions, heavily weighting hard examples. | Focuses hard classification learning on distinguishing open wounds from normal pet fur; converged to **`7.02`**. |
| **Loss Function** | **Distribution Focal Loss ($L_{dfl}$)**| `DFL Loss` (Weight = `1.5`) | Treats box regression as a classification task over continuous probabilities. | Regresses continuous bounding edge probability distributions to clean up ambiguous laceration margins; converged to **`2.53`**. |
| **Loss Strategy**| **Why Box Loss is 15× Higher** | `7.5 vs 0.5` | Balances the gradient impact of box regression versus classification. | Prioritizes localized coordinate boundary accuracy over basic classification to generate exact, clean open trauma crops for Module 4 U-Net! |
| **Data Imbalance**| **Negative Control Balance** | `48.8% Uninjured Balance` | The ratio of background-only images used to suppress false positives. | Forces background suppression representation inside the confidence loss head, guaranteeing our perfect **`100.00% Test Precision`**! |
| **Masking** | **Overlap Mask Ratio** | `mask_ratio = 4.0` | Controls resolution of instance masks (if segmentation was used). | Optimizes memory allocation across target segmentation boundaries during multi-scale bounding tensor projection. |

---

# Slide 6: Optimization, Regularization & Warmup Schedule

| Category | Hyperparameter | Value | Usually What It Does | Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Optimizer** | **Primary Optimizer Type** | `AdamW` | Adaptive gradient descent algorithm with decoupled weight decay. | Delivers decoupled parameter decay, preventing premature weight stagnation across heterogeneous veterinary wound textures. |
| **Optimizer** | **Base Learning Rate ($LR_0$)** | `0.001` (`1e-3`) | The initial step size used for updating neural network weights. | Foundational optimization step size calibrated to fine-tune pretrained COCO feature extractors without disrupting existing edge filters. |
| **Optimizer** | **Final LR Discount ($LR_f$)** | `0.01` (`1e-5` absolute LR) | The minimum learning rate reached via cosine annealing scheduling. | Cosine learning rate attenuation settling network parameters into sharp global optimization minima during convergence. |
| **Optimizer** | **Momentum Equivalent** | `0.937` (AdamW velocity decay) | Accelerates gradients in consistent directions to escape local minima. | Dampens trajectory oscillations across shuffling mini-batches of high-contrast exam table surfaces and surgical lighting. |
| **Regularization** | **Weight Decay (L2 Penalty)** | `0.01` (`weight_decay=0.01`) | Penalizes large weight values to prevent the model from memorizing data. | Regularization penalty punishing oversized weights, suppressing over-confidence on camera sensor ISO noise and fur glare. |
| **Warmup Schedule**| **Warmup Epochs & Momentum** | `3.0 Warmup Epochs` | Gradually increases the learning rate during the first few epochs. | Initiates training with lowered momentum and elevated bias steps to stabilize bounding box regressions before full optimization. |
| **Regularization** | **Dropout Rate** | `0.0` (Disabled) | Randomly zeroes out neurons during training to prevent overfitting. | Avoided explicit dropout in detection branches; relied on intense Mosaic data augmentation and AdamW decay for regularization. |
| **Regularization** | **Early Stopping Patience** | `Enabled` (`patience = 15`) | Stops training if validation metrics do not improve after $N$ epochs. | Automatically terminated training when validation plateaued, locking in maximum generalization before rote memorization began. |

---

# Slide 7: Training Infrastructure, Hardware & Clinical Benchmarks

| Category | Hyperparameter | Value | Usually What It Does | Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Training** | **Number of Epochs** | `50 Epochs` (Max Limit) | The total number of times the network sees the entire dataset. | Provided ample iterative runtime for bounding coordinate optimization while early stopping prevented clinical overfitting. |
| **Training** | **Mixed Precision (AMP)** | `Enabled (amp = True)` | Uses half-precision (FP16) math to speed up training and save memory. | Leveraged Automatic Mixed Precision to double VRAM capacity and computation throughput without loss of bounding coordinate fidelity. |
| **Training** | **Deterministic Random Seed**| `Seed = 0` (`deterministic = True`) | Fixes the random number generator so experiments are reproducible. | Enforces strictly reproducible dataset shuffle routines and deterministic experimental convergence across Colab runs. |
| **Hardware** | **Device Acceleration & VRAM**| `NVIDIA Tesla T4 GPU` | The physical compute hardware executing tensor math operations. | Executed complex anchor-free bounding box regression under rapid timelines without local CPU computational bottlenecks. |
| **Hardware** | **Parallel DataLoader Workers**| `workers = 8` | The number of CPU threads preparing and loading data into the GPU. | Streams loaded 640px image tensors asynchronously into active CUDA RAM caches without CPU image unpacking lag. |
| **Validation** | **Dataset Integrity & Splitting**| `Stratified Train/Val/Test` | How the dataset is divided into sets for learning vs evaluation. | Removed duplicate compressed photos across partitions to ensure authentic out-of-distribution trauma evaluations. |
| **Evaluation** | **Formal Clinical Accuracy** | `100% Precision` \| `71.05% mAP@50` | Standard object detection metrics measuring correctness and overlap. | Evaluated using computer vision localization benchmarks, proving 0% false alarms on healthy coats while accurately identifying acute wounds. |
| **Evaluation** | **Inference Latency & FPS** | `3.8 ms` per picture (`263 FPS`) | The time it takes for the model to process one single image. | Operates at 263 frames per second, vastly surpassing our $<15\text{ ms}$ real-time emergency hospital triage requirement! |

---
*Generated for MediPaw Veterinary Skin Diagnostic System — YOLOv8 Hyperparameter Presentation Tables.*
