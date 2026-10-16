"""
=============================================================================
MediPaw U-Net — YOLOv8 wrapper for the yolov8/ module
=============================================================================
Thin wrapper around Uha's predict_new_image.py that returns a structured dict
so the backend can call it without importing the script directly.

Usage
-----
  from yolov8.yolo_interface import detect_wounds

  detections = detect_wounds("path/to/image.jpg")
  # [{"x1": 120, "y1": 80, "x2": 350, "y2": 290, "conf": 0.87}, ...]
=============================================================================
"""

import os
import sys
from pathlib import Path

_YOLO_DIR = os.path.dirname(os.path.abspath(__file__))
if _YOLO_DIR not in sys.path:
    sys.path.insert(0, _YOLO_DIR)

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


DEFAULT_WEIGHTS = os.path.join(_YOLO_DIR, "weights", "best.pt")
CONF_THRESHOLD  = 0.25


def detect_wounds(
    image_path: str,
    weights: str = DEFAULT_WEIGHTS,
    conf: float = CONF_THRESHOLD,
    save_viz: bool = False,
) -> list[dict]:
    """
    Run YOLOv8 wound detection on a single image.

    Parameters
    ----------
    image_path : path to input image
    weights    : path to YOLOv8 best.pt (defaults to yolov8/weights/best.pt)
    conf       : confidence threshold
    save_viz   : if True, saves an annotated image to disk (ultralytics default dir)

    Returns
    -------
    List of detection dicts:
      [{"x1": int, "y1": int, "x2": int, "y2": int, "conf": float}, ...]
    """
    if not YOLO_AVAILABLE:
        raise ImportError(
            "ultralytics is not installed. Run: pip install ultralytics"
        )

    if not os.path.exists(weights):
        raise FileNotFoundError(
            f"YOLO weights not found at: {weights}\n"
            "Ensure yolov8/weights/best.pt is present."
        )

    model   = YOLO(weights)
    results = model.predict(
        source=str(image_path),
        conf=conf,
        save=save_viz,
        verbose=False,
    )

    detections = []
    for box in results[0].boxes:
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        detections.append({
            "x1":  x1,
            "y1":  y1,
            "x2":  x2,
            "y2":  y2,
            "conf": round(float(box.conf[0].item()), 4),
        })

    return detections


if __name__ == "__main__":
    import sys
    img = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    dets = detect_wounds(img)
    print(f"Detected {len(dets)} wound(s):")
    for d in dets:
        print(f"  {d}")
