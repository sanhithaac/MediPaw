import os
import sys
import torch

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from thoraciccnn.dataset_loader import get_dataloaders
from thoraciccnn.model import build_thoracic_model
from thoraciccnn.train import train_thoracic_model
from thoraciccnn.thoraciccnn_api import predict_thoracic

print("=== 1. Testing Dataset Loader & Patient Splitting ===")
data_dir = os.path.join(_THIS_DIR, "data")
train_l, val_l, test_l, meta = get_dataloaders(data_dir, batch_size=4)
print(f"Total: {meta['total_images']}, Train: {meta['train_count']}, Val: {meta['val_count']}, Test: {meta['test_count']}")
sample_batch = next(iter(train_l))
print(f"Batch image tensor shape: {sample_batch['image'].shape}")
print(f"Sample patient IDs in batch: {sample_batch['patient_id'][:4]}")

print("\n=== 2. Testing Model Forward Pass & Feature Extraction ===")
m = build_thoracic_model(backbone_name="mobilenet_v3_small", pretrained=False)
dummy = torch.randn(2, 3, 224, 224)
pred, feat = m.forward_with_features(dummy)
print(f"Model forward pass: pred={pred.shape}, features={feat.shape}")
assert feat.shape == (2, 576), f"Expected feature shape (2, 576), got {feat.shape}"

print("\n=== 3. Testing Guarded Training Pipeline ===")
train_thoracic_model(data_dir, annotation_path=None, output_dir=os.path.join(_THIS_DIR, "checkpoints"))

print("\n=== 4. Testing Inference API Callable ===")
sample_files = [f for f in os.listdir(data_dir) if f.endswith(".png")]
sample_path = os.path.join(data_dir, sample_files[0])
res = predict_thoracic(sample_path, return_features=True)
print(f"Status: {res['status']}")
print(f"Model Name: {res['model_name']}")
print(f"Task: {res['task']}")
first_warn = res['warnings'][0] if res.get('warnings') else "None"
print(f"Warnings ({len(res.get('warnings', []))}): {first_warn}")
print(f"Diagnostics: {res['diagnostics']}")

print("\n[SUCCESS] All Thoracic CNN module tests passed successfully!")
