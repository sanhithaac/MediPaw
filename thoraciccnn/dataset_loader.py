"""
Thoracic Radiograph Dataset Loader for MediPaw.

Handles data loading, medical image preprocessing, patient-level splitting,
and DICOM-UID parsing for canine latero-lateral thoracic X-rays (PMC8111263 / Mendeley ktx4cj55pn/1).
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms


# Standard ImageNet normalization parameters (compatible with pretrained backbones)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]


def parse_patient_id_from_filename(filename: str) -> str:
    """
    Extracts the patient identifier from DICOM SOP Instance UID filenames.
    Format: 1.2.410.200028.100.3.<YYYYMMDD>.<HHMMSSssss>.<PATIENT_ID>.<SERIES>.<INSTANCE>.<EXT>
    """
    basename = os.path.basename(filename)
    parts = basename.split(".")
    if len(parts) >= 11 and parts[0] == "1" and parts[1] == "2":
        return parts[8]  # Patient ID token in Rayence/DICOM UID schema
    # Fallback to stem before any non-alphanumeric or last segment
    stem = Path(basename).stem
    return stem


def get_patient_level_splits(
    data_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
) -> Dict[str, List[str]]:
    """
    Partitions the dataset into train, validation, and test splits grouped strictly by
    patient ID so that no individual canine patient's radiographs leak across splits.

    Returns:
        Dict with keys 'train', 'val', 'test' mapping to lists of absolute image paths.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Ratios must sum to 1.0"

    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
    all_files = [
        os.path.abspath(os.path.join(data_dir, f))
        for f in os.listdir(data_dir)
        if os.path.splitext(f)[1].lower() in valid_extensions and os.path.isfile(os.path.join(data_dir, f))
    ]
    all_files.sort()

    if not all_files:
        raise FileNotFoundError(f"No valid image files found in {data_dir}")

    # Group files by patient ID
    patient_to_files: Dict[str, List[str]] = {}
    for f in all_files:
        pid = parse_patient_id_from_filename(f)
        patient_to_files.setdefault(pid, []).append(f)

    # Sort patient keys for strict reproducibility across platforms
    unique_patients = sorted(list(patient_to_files.keys()))
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_patients)

    n_total = len(unique_patients)
    n_train = int(np.floor(train_ratio * n_total))
    n_val = int(np.floor(val_ratio * n_total))

    train_pids = set(unique_patients[:n_train])
    val_pids   = set(unique_patients[n_train:n_train + n_val])
    test_pids  = set(unique_patients[n_train + n_val:])

    splits: Dict[str, List[str]] = {"train": [], "val": [], "test": []}
    for pid, files in patient_to_files.items():
        if pid in train_pids:
            splits["train"].extend(files)
        elif pid in val_pids:
            splits["val"].extend(files)
        else:
            splits["test"].extend(files)

    for k in splits:
        splits[k].sort()

    return splits


class ThoracicDataset(Dataset):
    """
    PyTorch Dataset for Canine Thoracic Radiographs.
    Supports both supervised modes (when ground truth VHS / pathology labels are supplied)
    and unannotated mode (as provided by PMC8111263 / Mendeley ktx4cj55pn/1).
    """

    def __init__(
        self,
        image_paths: List[str],
        labels: Optional[Dict[str, Any]] = None,
        task: str = "vhs_regression",
        image_size: int = 224,
        is_training: bool = False,
    ):
        self.image_paths = image_paths
        self.labels = labels or {}
        self.task = task
        self.image_size = image_size
        self.is_training = is_training

        if is_training:
            self.transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=7),
                transforms.ColorJitter(brightness=0.1, contrast=0.1),
                transforms.ToTensor(),
                transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
            ])

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        img_path = self.image_paths[idx]
        basename = os.path.basename(img_path)
        pid = parse_patient_id_from_filename(img_path)

        # Robust image loading (handles PNG, JPEG, GIF, RGBA, Grayscale)
        with Image.open(img_path) as raw_img:
            img = raw_img.convert("RGB")
            orig_size = img.size  # (W, H)

        tensor = self.transform(img)

        # Label resolution
        has_label = basename in self.labels
        target_val = self.labels.get(basename, None)

        if target_val is None:
            # When unannotated, return dummy float tensor for regression or -1 for classification
            if self.task == "vhs_regression":
                label_tensor = torch.tensor(float("nan"), dtype=torch.float32)
            else:
                label_tensor = torch.tensor(-1, dtype=torch.long)
        else:
            if self.task == "vhs_regression":
                label_tensor = torch.tensor(float(target_val), dtype=torch.float32)
            else:
                label_tensor = torch.tensor(int(target_val), dtype=torch.long)

        return {
            "image": tensor,
            "label": label_tensor,
            "has_label": has_label,
            "patient_id": pid,
            "filename": basename,
            "image_path": img_path,
            "orig_size": orig_size
        }


def get_dataloaders(
    data_dir: str,
    labels: Optional[Dict[str, Any]] = None,
    batch_size: int = 8,
    image_size: int = 224,
    task: str = "vhs_regression",
    num_workers: int = 0,
    seed: int = 42
) -> Tuple[DataLoader, DataLoader, DataLoader, Dict[str, Any]]:
    """
    Convenience function to generate train, val, and test dataloaders with patient-level splitting.
    """
    splits = get_patient_level_splits(data_dir, seed=seed)

    train_ds = ThoracicDataset(splits["train"], labels=labels, task=task, image_size=image_size, is_training=True)
    val_ds   = ThoracicDataset(splits["val"],   labels=labels, task=task, image_size=image_size, is_training=False)
    test_ds  = ThoracicDataset(splits["test"],  labels=labels, task=task, image_size=image_size, is_training=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,  num_workers=num_workers)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False, num_workers=num_workers)

    metadata = {
        "total_images": len(splits["train"]) + len(splits["val"]) + len(splits["test"]),
        "train_count": len(splits["train"]),
        "val_count": len(splits["val"]),
        "test_count": len(splits["test"]),
        "splits": splits
    }
    return train_loader, val_loader, test_loader, metadata
