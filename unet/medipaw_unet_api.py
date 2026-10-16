"""
=============================================================================
MEDIPAW MODULE 4: U-Net — Backend Interface
=============================================================================
This module exposes a clean, documented callable for the MediPaw backend.

Backend integration example
----------------------------
  from unet.medipaw_unet_api import segment_wounds

  result = segment_wounds(
      image_path    = "uploads/dog001.jpg",
      yolo_weights  = "yolov8/weights/best.pt",
      unet_weights  = "unet/checkpoints/best_model.pt",
  )
  # result["status"]             — "ok" | "no_detections" | "error"
  # result["detections"]         — list of YOLO bbox dicts
  # result["segmentation_stats"] — per-detection wound pixel coverage
  # result["mask_path"]          — path to PNG mask (full res)
  # result["overlay_path"]       — path to overlay JPEG
  # result["trained_model"]      — True = real checkpoint, False = untrained

Returned dict is JSON-serialisable and backend-framework-agnostic.
=============================================================================
"""

import os
import sys
import traceback

# Allow running this file from any working directory
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)


def segment_wounds(
    image_path:   str,
    yolo_weights: str = "yolov8/weights/best.pt",
    unet_weights: str = "unet/checkpoints/best_model.pt",
    output_dir:   str = "unet/outputs",
    device:       str = "auto",
) -> dict:
    """
    Run the full MediPaw wound segmentation pipeline.

    Parameters
    ----------
    image_path   : Absolute or relative path to the input image.
    yolo_weights : Path to YOLOv8 best.pt weights.
    unet_weights : Path to U-Net best_model.pt checkpoint.
    output_dir   : Directory where output artefacts are saved.
    device       : "auto" | "cuda" | "cpu"

    Returns
    -------
    {
      "status":             "ok" | "no_detections" | "error",
      "image_path":         str,
      "detections":         list[dict],   # each has x1,y1,x2,y2,conf
      "segmentation_stats": list[dict],   # wound_pixels, coverage_pct, ...
      "mask_path":          str | None,
      "overlay_path":       str | None,
      "detection_path":     str | None,
      "trained_model":      bool,
      "error_message":      str | None,
    }
    """
    try:
        from inference import run_pipeline
        raw = run_pipeline(
            image_path=image_path,
            yolo_weights=yolo_weights,
            unet_weights=unet_weights,
            output_dir=output_dir,
            device=device,
        )
        status = "ok" if raw["yolo_detections"] else "no_detections"
        return {
            "status":             status,
            "image_path":         raw["image_path"],
            "detections":         raw["yolo_detections"],
            "segmentation_stats": raw["segmentation_stats"],
            "mask_path":          raw.get("mask_path"),
            "overlay_path":       raw.get("overlay_path"),
            "detection_path":     raw.get("detection_path"),
            "trained_model":      raw["trained_model"],
            "error_message":      None,
        }
    except Exception as exc:
        return {
            "status":             "error",
            "image_path":         image_path,
            "detections":         [],
            "segmentation_stats": [],
            "mask_path":          None,
            "overlay_path":       None,
            "detection_path":     None,
            "trained_model":      False,
            "error_message":      f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        }
