# MediPaw: Multi-Modal Veterinary Triage Pipeline

## Abstract

### 1. Problem Statement
Veterinary clinics face high patient volumes, delaying the assessment of critical signs (e.g., shock, severe trauma). There is an urgent need for an automated, multi-modal system capable of instantly analyzing physical symptoms to correctly prioritize life-threatening cases.

### 2. Novelty
* **Multi-Modal Fusion:** Combines targeted physical symptom extraction (skin, eyes, gums) with geometric wound analysis (damage percentage).
* **Tiered Triage Logic:** Uses a Vision Transformer (ViT) to dynamically override base classifications (e.g., instantly escalating cases with pale gums and >10% wound area to "Critical").
* **Specialized Ensembles:** Deploys distinct CNNs and specialized models (YOLOv8, U-Net) for specific anatomical targets, mimicking a vet's holistic primary assessment.

### 3. Comparison with Existing Products
* **Current Solutions:** Mostly single-model, general symptom checkers that lack severity context or systemic health correlation.
* **MediPaw's Difference:** Acts as an intelligent triage agent. It integrates structural disease detection (CNNs) with precise trauma geometry (U-Net/YOLO) and systemic perfusion indicators (gum color), offering context-aware queue placement rather than simple classification.

### 4. Architecture
* **Image 1 (Skin/Body):** 
  * **CNN 1:** Classifies structural skin conditions (Mange, Ringworm, etc.).
  * **YOLOv8:** Localizes parasites (ticks) and acute traumas.
  * **U-Net:** Segments bounding boxes to calculate exact wound surface area.
* **Image 2 (Eye Close-Up):**
  * **CNN 2:** Classifies ocular traumas (Cataracts, Ulcers, etc.).
* **Image 3 (Gum Close-Up):**
  * **CNN 3:** Classifies mucous membrane color for systemic vascular perfusion (Pale/Shock vs. Healthy).
* **Fusion Layer (ViT):**
  * **Multi-Modal Vision Transformer:** Synthesizes outputs from all models to determine Final Triage Queue Placement (Critical | High | Medium | Low).
    <img width="991" height="678" alt="image" src="https://github.com/user-attachments/assets/6e9c4e59-aaed-4852-ba5f-b26ff56325e6" />


## Tech Stack

### Frontend & UI
* **React** — user interface and component-based application structure.
* **React Router** — client-side navigation.
* **Tailwind CSS** — responsive styling and UI design.
* **Framer Motion** — interface animations.
* **Three.js / React Three Fiber** — interactive 3D visuals.

### Backend
* **Node.js** — API and server-side runtime.
* **Express.js** — REST API framework for connecting the UI and AI services.
* **Axios** — HTTP communication between the frontend and backend.

### AI / ML Models
* **Python** — model training, inference, and image-processing workflow.
* **PyTorch** — deep-learning framework used to build and run the CNN, U-Net, and ViT models.
* **Ultralytics YOLOv8** — PyTorch-based object-detection framework for ticks, parasites, and trauma.
* **OpenCV / Pillow** — image loading, preprocessing, and result annotation.
* **CNNs** — classify skin diseases, eye conditions, and gum colour.
* **U-Net** — segments wounds and estimates wound area.
* **Vision Transformer (ViT)** — fuses multimodal outputs and predicts final triage priority.

### 5. Dataset Links
* **Skin Disease (CNN 1):** [Dogs Skin Diseases (Youssefmohmmed)](https://www.kaggle.com/datasets/youssefmohmmed/dogs-skin-diseases-image-dataset) | [Dogs Skin Disease (Yashmotiani)](https://www.kaggle.com/datasets/yashmotiani/dogs-skin-disease-dataset) | [Animal Skin Disease Series (Roboflow)](https://universe.roboflow.com/shoaib-axxkh/animal-skin-disease-vb2io-fd8zr-whsem)
* **Ocular Pathology (CNN 2):** [Dog Eyes Version 4 (Roboflow)](https://universe.roboflow.com/dog-eyes/dog-eyes_ver.4) | [Dog Eye Problems Detection (Roboflow)](https://universe.roboflow.com/jonathan-chandra/dog-eye-problems-detection)
* **Mucous Membrane Color (CNN 3):** [Dog Dental Dataset (Roboflow)](https://universe.roboflow.com/moriahai/dog-dental) (Cropped for gum tissue)
* **Parasite & Trauma (YOLOv8 / U-Net):** [Tick Detection (Roboflow)](https://universe.roboflow.com/search?q=tick+detection) | [Animal Wound (Roboflow)](https://universe.roboflow.com/search?q=animal+wound)
* **Triage Priority Head (ViT):** Clinical mapping data mined from [IEEE DataPort](https://ieee-dataport.org/), [Mendeley Data](https://data.mendeley.com/), and [Zenodo](https://zenodo.org/).

---
