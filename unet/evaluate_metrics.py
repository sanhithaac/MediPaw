"""
=============================================================================
MEDIPAW MODULE 4: U-Net — Evaluation Metrics
=============================================================================
Computes Dice, IoU, Precision, and Recall from predicted and target masks.
Works on CPU tensors; no GPU context required.
=============================================================================
"""

import torch


def compute_metrics(
    preds: torch.Tensor,
    targets: torch.Tensor,
    threshold: float = 0.5,
    eps: float = 1e-6,
) -> dict[str, float]:
    """
    Compute segmentation metrics for a batch of predictions.

    Parameters
    ----------
    preds   : (B, 1, H, W) — SIGMOID probabilities OR binary {0,1}
    targets : (B, 1, H, W) — binary ground truth {0, 1}
    threshold : binarisation threshold (ignored if preds already binary)
    eps     : smoothing constant

    Returns
    -------
    dict with keys: dice, iou, precision, recall
    """
    preds   = (preds >= threshold).float().view(-1)
    targets = targets.float().view(-1)

    tp = (preds * targets).sum().item()
    fp = (preds * (1 - targets)).sum().item()
    fn = ((1 - preds) * targets).sum().item()

    precision = tp / (tp + fp + eps)
    recall    = tp / (tp + fn + eps)
    dice      = 2 * tp / (2 * tp + fp + fn + eps)
    iou       = tp / (tp + fp + fn + eps)

    return {
        "dice":      float(dice),
        "iou":       float(iou),
        "precision": float(precision),
        "recall":    float(recall),
    }


def evaluate_on_loader(
    model: "torch.nn.Module",
    loader: "torch.utils.data.DataLoader",
    device: "torch.device",
    threshold: float = 0.5,
) -> dict[str, float]:
    """
    Run full-dataset evaluation using compute_metrics.

    Returns averaged metrics dict.
    """
    model.eval()
    all_preds, all_targets = [], []

    with torch.no_grad():
        for images, masks in loader:
            images = images.to(device)
            logits = model(images)
            probs  = torch.sigmoid(logits).cpu()
            all_preds.append((probs >= threshold).float())
            all_targets.append(masks.float())

    return compute_metrics(
        torch.cat(all_preds, 0),
        torch.cat(all_targets, 0),
        threshold=threshold,
    )


if __name__ == "__main__":
    # Quick sanity test
    preds   = torch.tensor([[[[1, 0], [1, 1]]]], dtype=torch.float32)
    targets = torch.tensor([[[[1, 0], [0, 1]]]], dtype=torch.float32)
    m = compute_metrics(preds, targets)
    print("Test metrics:", {k: round(v, 4) for k, v in m.items()})
