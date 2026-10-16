"""
=============================================================================
MEDIPAW MODULE 4: U-Net + YOLOv8 — Unified Inference Script
=============================================================================

PIPELINE
--------
  1. Load input image.
  2. YOLOv8 detects wound bounding boxes (reuses Uha's best.pt).
  3. Each detected ROI is cropped, resized to 256×256, and fed to U-Net.
  4. U-Net produces a sigmoid mask for the cropped region.
  5. The per-crop mask is resized back and stitched into a full-image canvas.
  6. Outputs are visualised and saved.

This script exposes a `run_pipeline()` function callable by the backend.

Usage (PowerShell)
------------------
  cd MediPaw_Code
  python unet/inference.py --image path/to/dog_image.jpg \
                           --yolo_weights yolov8/weights/best.pt \
                           --unet_weights unet/checkpoints/best_model.pt

Output files (saved to unet/outputs/)
  - <stem>_detection.jpg   — image with YOLOv8 bounding boxes
  - <stem>_mask.png        — full-resolution binary mask
  - <stem>_overlay.jpg     — image with translucent mask overlay
  - <stem>_result.json     — structured JSON result for backend

IMPORTANT
---------
If no U-Net checkpoint exists (unet/checkpoints/best_model.pt is missing),
the script falls back to an untrained random-weight model and clearly
annotates that in the output JSON. Train first for real results.
=============================================================================
"""

import argparse
import json
import os
from pathlib import Path

import cv2
import numpy as np
import torch

try:
    from ultralytics import YOLO as _YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARNING] ultralytics not installed. YOLO stage will be skipped.")

from model_architecture import UNet


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IMG_SIZE    = 256
YOLO_CONF   = 0.25    # confidence threshold for YOLOv8 detections
MASK_THRESH = 0.50    # sigmoid probability threshold for mask binarisation

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


# ---------------------------------------------------------------------------
# Preprocessing helpers
# ---------------------------------------------------------------------------

def _preprocess_crop(crop_bgr: np.ndarray) -> torch.Tensor:
    """Convert a BGR numpy crop to a normalised (1, 3, H, W) float tensor."""
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    crop_rgb = cv2.resize(crop_rgb, (IMG_SIZE, IMG_SIZE))
    crop_f   = crop_rgb.astype(np.float32) / 255.0
    crop_n   = (crop_f - IMAGENET_MEAN) / IMAGENET_STD
    tensor   = torch.from_numpy(crop_n.transpose(2, 0, 1)).unsqueeze(0)
    return tensor


def _mask_to_np(logits: torch.Tensor, target_h: int, target_w: int) -> np.ndarray:
    """Convert model output logit to a resized uint8 binary mask."""
    prob = torch.sigmoid(logits[0, 0]).numpy()
    binary_mask = (prob >= MASK_THRESH).astype(np.uint8) * 255
    return cv2.resize(binary_mask, (target_w, target_h),
                      interpolation=cv2.INTER_NEAREST)


# ---------------------------------------------------------------------------
# Main pipeline function
# ---------------------------------------------------------------------------

def run_pipeline(
    image_path: str,
    yolo_weights: str = "yolov8/weights/best.pt",
    unet_weights: str = "unet/checkpoints/best_model.pt",
    output_dir: str   = "unet/outputs",
    device: str       = "auto",
) -> dict:
    """
    Run YOLOv8 → U-Net pipeline on a single image.

    Parameters
    ----------
    image_path   : path to input image (any species, any wound type)
    yolo_weights : path to YOLOv8 best.pt checkpoint
    unet_weights : path to U-Net best_model.pt checkpoint (or None)
    output_dir   : directory where result files are saved
    device       : "auto" | "cuda" | "cpu"

    Returns
    -------
    dict with keys:
      image_path, yolo_detections, unet_available, trained_model,
      mask_path, overlay_path, segmentation_stats
    """
    os.makedirs(output_dir, exist_ok=True)
    stem = Path(image_path).stem

    # Resolve device
    if device == "auto":
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        dev = torch.device(device)

    print("=" * 72)
    print(f"  [MediPaw] YOLOv8 → U-Net inference  |  device={dev}")
    print(f"  Image : {image_path}")
    print("=" * 72)

    # ── Load image ──────────────────────────────────────────────────────
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise FileNotFoundError(f"Cannot open image: {image_path}")
    h_orig, w_orig = img_bgr.shape[:2]

    # ── STAGE 1: YOLOv8 detection ────────────────────────────────────────
    detections = []
    if YOLO_AVAILABLE and os.path.exists(yolo_weights):
        print(f"\n[Stage 1] YOLOv8 detection with weights: {yolo_weights}")
        yolo = _YOLO(yolo_weights)
        results = yolo.predict(
            source=str(image_path), conf=YOLO_CONF, save=False, verbose=False
        )
        boxes = results[0].boxes
        for box in boxes:
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            conf = float(box.conf[0].item())
            detections.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "conf": round(conf, 4)})

        # Draw boxes
        det_img = img_bgr.copy()
        for d in detections:
            cv2.rectangle(det_img, (d["x1"], d["y1"]), (d["x2"], d["y2"]),
                          (0, 255, 0), 2)
            cv2.putText(det_img, f"Wound {d['conf']:.2f}",
                        (d["x1"], max(d["y1"] - 8, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        det_path = os.path.join(output_dir, f"{stem}_detection.jpg")
        cv2.imwrite(det_path, det_img)
        print(f"  [YOLO] {len(detections)} wound(s) detected → {det_path}")
    else:
        print("[Stage 1] YOLO skipped — fallback: whole image as one detection")
        detections = [{"x1": 0, "y1": 0, "x2": w_orig, "y2": h_orig, "conf": 1.0}]
        det_path   = None

    # ── STAGE 2: U-Net segmentation ──────────────────────────────────────
    print("\n[Stage 2] U-Net segmentation")

    model = UNet(in_channels=3, base_filters=32).to(dev)
    trained_model = False

    if os.path.exists(unet_weights):
        ckpt = torch.load(unet_weights, map_location=dev)
        model.load_state_dict(ckpt["state_dict"])
        print(f"  [U-Net] Loaded checkpoint (epoch {ckpt.get('epoch','?')}, "
              f"val_dice={ckpt.get('val_dice', 'N/A')})")
        trained_model = True
    else:
        print(f"  [U-Net] WARNING: No checkpoint at {unet_weights}.")
        print("          Using UNTRAINED model — mask is random noise (architecture demo).")

    model.eval()

    # Full-image mask canvas
    full_mask = np.zeros((h_orig, w_orig), dtype=np.uint8)

    seg_stats = []
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
        # Clamp to image bounds
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, w_orig), min(y2, h_orig)
        if x2 <= x1 or y2 <= y1:
            continue

        crop = img_bgr[y1:y2, x1:x2]
        tensor = _preprocess_crop(crop).to(dev)

        with torch.no_grad():
            logits = model(tensor)

        crop_mask = _mask_to_np(logits.cpu(), y2 - y1, x2 - x1)
        full_mask[y1:y2, x1:x2] = np.maximum(full_mask[y1:y2, x1:x2], crop_mask)

        wound_px  = int((crop_mask > 127).sum())
        total_px  = int((y2 - y1) * (x2 - x1))
        coverage  = round(wound_px / total_px * 100, 2) if total_px > 0 else 0.0
        seg_stats.append({
            "detection_idx": i,
            "bbox":          det,
            "wound_pixels":  wound_px,
            "total_pixels":  total_px,
            "coverage_pct":  coverage,
        })
        print(f"  Wound #{i+1}: coverage={coverage:.1f}% ({wound_px}/{total_px} px)")

    # Save full mask
    mask_path    = os.path.join(output_dir, f"{stem}_mask.png")
    overlay_path = os.path.join(output_dir, f"{stem}_overlay.jpg")
    cv2.imwrite(mask_path, full_mask)

    # Colour overlay (translucent red)
    overlay = img_bgr.copy()
    red_layer = np.zeros_like(overlay)
    red_layer[full_mask > 127] = [0, 0, 220]
    cv2.addWeighted(red_layer, 0.4, overlay, 1.0, 0, overlay)
    cv2.imwrite(overlay_path, overlay)

    print(f"\n  [Output] mask    → {mask_path}")
    print(f"  [Output] overlay → {overlay_path}")

    # ── Result JSON ──────────────────────────────────────────────────────
    result = {
        "image_path":       str(image_path),
        "yolo_detections":  detections,
        "unet_available":   os.path.exists(unet_weights),
        "trained_model":    trained_model,
        "mask_path":        mask_path,
        "overlay_path":     overlay_path,
        "detection_path":   det_path,
        "segmentation_stats": seg_stats,
    }

    json_path = os.path.join(output_dir, f"{stem}_result.json")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  [Output] JSON    → {json_path}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="MediPaw: YOLOv8 → U-Net wound segmentation pipeline"
    )
    p.add_argument("--image",        required=True, help="Input image path")
    p.add_argument("--yolo_weights", default="yolov8/weights/best.pt")
    p.add_argument("--unet_weights", default="unet/checkpoints/best_model.pt")
    p.add_argument("--output_dir",   default="unet/outputs")
    p.add_argument("--device",       default="auto")
    args = p.parse_args()

    result = run_pipeline(
        image_path=args.image,
        yolo_weights=args.yolo_weights,
        unet_weights=args.unet_weights,
        output_dir=args.output_dir,
        device=args.device,
    )
    print("\n[Pipeline complete]")
