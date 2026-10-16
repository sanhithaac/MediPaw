"""
=============================================================================
MEDIPAW MODULE 4: U-Net — Loss Functions
=============================================================================
Combined BCEWithLogitsLoss + Dice Loss for binary segmentation.

Why combined?
  - BCE handles per-pixel class balance and is numerically stable.
  - Dice directly maximises the overlap metric used in evaluation.
  - Together they give faster convergence on small, imbalanced wound masks.
=============================================================================
"""

import torch
import torch.nn as nn


def dice_loss(logits: torch.Tensor, targets: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    """
    Soft Dice loss for binary segmentation.

    Args
    ----
    logits  : (B, 1, H, W) — raw model outputs (before sigmoid)
    targets : (B, 1, H, W) — ground-truth masks in {0, 1}
    eps     : numerical stability constant

    Returns
    -------
    Scalar loss value.
    """
    probs = torch.sigmoid(logits)
    probs   = probs.view(probs.size(0), -1)
    targets = targets.view(targets.size(0), -1).float()

    intersection = (probs * targets).sum(dim=1)
    union        = probs.sum(dim=1) + targets.sum(dim=1)

    dice = (2.0 * intersection + eps) / (union + eps)
    return 1.0 - dice.mean()


class CombinedLoss(nn.Module):
    """
    BCE + Dice combined loss.

    Args
    ----
    bce_weight  : weight for BCE term  (default 0.5)
    dice_weight : weight for Dice term (default 0.5)
    pos_weight  : optional tensor for class imbalance in BCE
    """

    def __init__(
        self,
        bce_weight:  float = 0.5,
        dice_weight: float = 0.5,
        pos_weight:  torch.Tensor | None = None,
    ):
        super().__init__()
        self.bce_weight  = bce_weight
        self.dice_weight = dice_weight
        self.bce = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce  = self.bce(logits, targets.float())
        dice = dice_loss(logits, targets)
        return self.bce_weight * bce + self.dice_weight * dice
