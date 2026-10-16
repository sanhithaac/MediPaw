"""
=============================================================================
MEDIPAW MODULE 4: U-Net — Dataset Loader
=============================================================================

ANNOTATION REALITY CHECK (important)
--------------------------------------
The MediPaw yolo_canine_wounds dataset contains ONLY YOLO bounding-box
annotations (5 tokens: class cx cy w h).  There are NO pixel-level
segmentation masks in the current dataset.

This loader supports TWO modes:

  MODE A  — mask_dir supplied (preferred)
  ----------------------------------------
  For use when proper binary PNG masks exist on disk.
  Each mask image is a grayscale PNG where:
    255 = wound pixel
    0   = background pixel
  Masks and images must share the same filename stem.

  MODE B  — mask_dir = None (fallback / demonstration)
  -------------------------------------------------------
  When no mask annotations exist, we generate a SYNTHETIC GAUSSIAN MASK
  from the YOLO bounding-box annotation.  This is ONLY for demonstrating
  the pipeline architecture.  Models trained on synthetic masks will NOT
  produce valid segmentation metrics and MUST NOT be reported as real results.
  The loader logs a clear warning in this mode.

Augmentation
  We use albumentations so that geometric transforms are applied
  identically to both the image and the mask (synchronised).

Usage
  dataset = WoundSegmentationDataset(
      images_dir = "skincnn/yolo_canine_wounds/train/images",
      labels_dir = "skincnn/yolo_canine_wounds/train/labels",   # YOLO txts
      mask_dir   = None,   # or "unet/masks/train" if masks exist
      img_size   = 256,
  )
=============================================================================
"""

import os
import warnings
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gaussian_mask_from_yolo(label_path: str, img_h: int, img_w: int) -> np.ndarray:
    """
    Build a SYNTHETIC binary mask from a YOLO label file.

    Each bounding box is converted to a filled rectangle.  This is used
    only when real segmentation masks are unavailable.  A warning is always
    emitted when this function is called.
    """
    mask = np.zeros((img_h, img_w), dtype=np.uint8)
    if not label_path or not os.path.exists(label_path):
        return mask

    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            _, cx, cy, bw, bh = map(float, parts[:5])
            x1 = int((cx - bw / 2) * img_w)
            y1 = int((cy - bh / 2) * img_h)
            x2 = int((cx + bw / 2) * img_w)
            y2 = int((cy + bh / 2) * img_h)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(img_w - 1, x2), min(img_h - 1, y2)
            mask[y1:y2, x1:x2] = 255

    return mask


def _build_transform(img_size: int, augment: bool) -> "A.Compose | None":
    """Return an albumentations transform pipeline or None if not installed."""
    if not ALBUMENTATIONS_AVAILABLE:
        return None

    base = [
        A.Resize(img_size, img_size),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ]

    if augment:
        aug = [
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.1,
                               rotate_limit=15, p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.2,
                                       contrast_limit=0.2, p=0.4),
            A.GaussNoise(p=0.2),
        ]
        transforms = aug + base
    else:
        transforms = base

    return A.Compose(transforms)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class WoundSegmentationDataset(Dataset):
    """
    PyTorch Dataset for U-Net wound segmentation.

    Parameters
    ----------
    images_dir : path to directory containing .jpg / .png images
    labels_dir : path to YOLO label .txt files (used for synthetic masks)
    mask_dir   : path to PNG binary mask files; if None, synthetic masks
                 are generated from YOLO bboxes (fallback mode)
    img_size   : square resize target (default 256)
    augment    : whether to apply data augmentation (True for train)
    """

    SYNTHETIC_WARNED = False  # class-level flag to avoid repeating warning

    def __init__(
        self,
        images_dir: str,
        labels_dir: str | None = None,
        mask_dir:   str | None = None,
        img_size:   int = 256,
        augment:    bool = False,
    ):
        self.images_dir = Path(images_dir)
        self.labels_dir = Path(labels_dir) if labels_dir else None
        self.mask_dir   = Path(mask_dir)   if mask_dir   else None
        self.img_size   = img_size
        self.augment    = augment
        self.use_synthetic = (self.mask_dir is None)

        if self.use_synthetic and not WoundSegmentationDataset.SYNTHETIC_WARNED:
            warnings.warn(
                "\n"
                "============================================================\n"
                "[MediPaw U-Net] SYNTHETIC MASK MODE ACTIVE\n"
                "No real segmentation masks found (mask_dir=None).\n"
                "Masks are being generated from YOLO bounding boxes.\n"
                "This is a PIPELINE DEMONSTRATION ONLY.\n"
                "Models trained this way CANNOT produce valid metrics.\n"
                "Provide real PNG masks in mask_dir to enable real training.\n"
                "============================================================",
                UserWarning,
                stacklevel=2,
            )
            WoundSegmentationDataset.SYNTHETIC_WARNED = True

        # Collect image paths
        exts = {".jpg", ".jpeg", ".png", ".bmp"}
        self.image_paths = sorted(
            p for p in self.images_dir.iterdir() if p.suffix.lower() in exts
        )

        if not self.image_paths:
            raise RuntimeError(f"No images found in {images_dir}")

        self.transform = _build_transform(img_size, augment)

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        img_path = self.image_paths[idx]

        # Load image
        img = cv2.imread(str(img_path))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {img_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]

        # Load or generate mask
        if self.use_synthetic:
            lbl_path = None
            if self.labels_dir is not None:
                lbl_path = self.labels_dir / (img_path.stem + ".txt")
                lbl_path = str(lbl_path) if lbl_path.exists() else None
            mask = _gaussian_mask_from_yolo(lbl_path, h, w)
        else:
            mask_path = self.mask_dir / (img_path.stem + ".png")
            if not mask_path.exists():
                mask_path = self.mask_dir / (img_path.stem + ".jpg")
            if mask_path.exists():
                mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
                if mask is None:
                    raise FileNotFoundError(f"Cannot read mask: {mask_path}")
            else:
                # Graceful fallback to empty mask
                warnings.warn(f"Mask not found for {img_path.name}; using zeros.")
                mask = np.zeros((h, w), dtype=np.uint8)

        # Binarise mask → 0/1
        mask = (mask > 127).astype(np.uint8)

        # Apply transforms
        if self.transform is not None:
            transformed = self.transform(image=img, mask=mask)
            image_tensor = transformed["image"]           # float32 (3, H, W)
            mask_tensor  = transformed["mask"].unsqueeze(0).float()  # (1, H, W)
        else:
            # Manual fallback (no albumentations)
            img  = cv2.resize(img,  (self.img_size, self.img_size))
            mask = cv2.resize(mask, (self.img_size, self.img_size),
                              interpolation=cv2.INTER_NEAREST)
            mean = np.array([0.485, 0.456, 0.406])
            std  = np.array([0.229, 0.224, 0.225])
            img  = (img / 255.0 - mean) / std
            image_tensor = torch.from_numpy(img.transpose(2, 0, 1)).float()
            mask_tensor  = torch.from_numpy(mask[None]).float()

        return image_tensor, mask_tensor


# ---------------------------------------------------------------------------
# Quick sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ds = WoundSegmentationDataset(
        images_dir=r"skincnn/yolo_canine_wounds/train/images",
        labels_dir=r"skincnn/yolo_canine_wounds/train/labels",
        mask_dir=None,       # synthetic mode
        img_size=256,
        augment=False,
    )
    print(f"Dataset length: {len(ds)}")
    img, msk = ds[0]
    print(f"Image tensor : {img.shape} dtype={img.dtype}")
    print(f"Mask  tensor : {msk.shape} dtype={msk.dtype}")
    print(f"Mask  unique : {msk.unique()}")
