# MediPaw — Multi-Modal Vision Transformer (ViT) Fusion Layer

## Purpose

Fuses intermediate feature embeddings (576-dim) extracted by individual MediPaw CNN models
into a unified cross-modal representation for clinical urgency estimation.

## Architecture

```
[Eye CNN]         576-dim embedding ─┐
[Thoracic CNN]    576-dim embedding ─┼─ Linear Projection → d_model=256 ─┐
[Future CNNs...]  576-dim embedding ─┘                                    │
                                                                           ▼
                                              CLS Token + Positional Encoding
                                                         │
                                            3-Layer Pre-Norm Transformer Encoder
                                                         │
                                                   CLS Token Output (256-dim)
                                                    ┌────┴────┐
                                             Urgency Head   Triage Head
                                           (sigmoid scalar)  (4-class logits)
```

## Scientific Status

| Component | Status |
|-----------|--------|
| Architecture | ✅ Implemented |
| Feature extraction (Eye CNN) | ✅ Returns 576-dim embedding |
| Feature extraction (Thoracic CNN) | ✅ Returns 576-dim embedding (on init checkpoint only) |
| Supervised training | ❌ Requires multi-modal clinical cohort with verified triage labels |
| Operational triage output | ❌ Rule-based fallback used until training is complete |

**All fusion outputs are transparently disclosed as `architecture_prototype` until the model
is trained on a validated multi-modal clinical dataset.**

## Module Files

| File | Description |
|------|-------------|
| `model.py` | `MultiModalViT` Transformer architecture |
| `inference.py` | `run_fusion()` — collects embeddings, runs ViT, returns standardized result dict |
| `multimodal_api.py` | `fuse_model_results()` — public API callable from backend adapters |
| `checkpoints/` | Trained checkpoint saved here as `best_vit_model.pth` after training |

## Backend Integration

The ViT runs automatically at the end of every `/api/intake` request:

```python
# backend/adapters.py
from multimodal_vit.multimodal_api import fuse_model_results
vit_result = fuse_model_results(model_results)
```

A standalone fusion endpoint is also available:
```
POST /api/predict/fusion
Form fields: file (image), modality ("ocular" | "thoracic")
```

## Training (Future Work)

To train the ViT fusion head:
1. Collect intake packets where ≥2 CNN models returned validated embeddings
2. Record ground-truth triage priority labels (Low / Medium / High / Critical)
3. Construct multi-modal dataset with stacked 576-dim embeddings as input
4. Fine-tune on cross-entropy (triage head) + MSE (urgency head)
5. Save weights to `checkpoints/best_vit_model.pth`
