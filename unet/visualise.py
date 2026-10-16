"""
=============================================================================
MEDIPAW MODULE 4: U-Net — Visualisation Utilities
=============================================================================
Standalone helpers for generating overlay figures and saving diagnostic plots.
Can be called from inference.py or independently for post-processing.
=============================================================================
"""

import os

import cv2
import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")   # headless backend
    import matplotlib.pyplot as plt
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False


def overlay_mask_on_image(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    alpha: float = 0.4,
    color_bgr: tuple = (0, 0, 220),
) -> np.ndarray:
    """
    Blend a binary mask over an image with a translucent colour overlay.

    Parameters
    ----------
    image_bgr : (H, W, 3) uint8 BGR image
    mask      : (H, W)    uint8 binary mask (255 = wound, 0 = background)
    alpha     : overlay transparency (0 = invisible, 1 = opaque)
    color_bgr : BGR colour for the wound region

    Returns
    -------
    (H, W, 3) uint8 blended image
    """
    overlay = image_bgr.copy()
    colour_layer = np.zeros_like(overlay)
    colour_layer[mask > 127] = list(color_bgr)
    cv2.addWeighted(colour_layer, alpha, overlay, 1.0, 0, overlay)
    return overlay


def draw_bboxes(image_bgr: np.ndarray, detections: list[dict]) -> np.ndarray:
    """
    Draw YOLO bounding boxes on an image.

    Parameters
    ----------
    image_bgr  : input image
    detections : list of dicts with keys x1, y1, x2, y2, conf

    Returns
    -------
    Image with boxes drawn (copy of input).
    """
    out = image_bgr.copy()
    for d in detections:
        cv2.rectangle(out, (d["x1"], d["y1"]), (d["x2"], d["y2"]),
                      (0, 220, 0), 2)
        label = f"Wound {d['conf']:.2f}"
        cv2.putText(out, label, (d["x1"], max(d["y1"] - 8, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 0), 2)
    return out


def save_diagnostic_figure(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    overlay: np.ndarray,
    save_path: str,
    title: str = "MediPaw U-Net Wound Segmentation",
):
    """
    Save a three-panel matplotlib figure: original | mask | overlay.

    If matplotlib is not installed, saves only the overlay with cv2.
    """
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    if MPL_AVAILABLE:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(title, fontsize=14)

        axes[0].imshow(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
        axes[0].set_title("Original Image")
        axes[0].axis("off")

        axes[1].imshow(mask, cmap="gray")
        axes[1].set_title("Predicted Mask")
        axes[1].axis("off")

        axes[2].imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
        axes[2].set_title("Mask Overlay")
        axes[2].axis("off")

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  [Visualisation] Saved → {save_path}")
    else:
        # Fallback: save just the overlay
        fallback = save_path.replace(".png", "_overlay.jpg")
        cv2.imwrite(fallback, overlay)
        print(f"  [Visualisation] matplotlib not installed; overlay → {fallback}")
