"""
=============================================================================
MEDIPAW MODULE 4: U-Net Wound Segmentation — Model Architecture
=============================================================================
Classic encoder-decoder U-Net with skip connections.

Input  : (B, 3, H, W)  — RGB image crop from YOLOv8 bounding box
Output : (B, 1, H, W)  — single-channel logit mask (apply sigmoid for prob)

Designed to be lightweight (default 32 base filters) so it trains on
limited data and runs on a CPU or entry-level GPU.
=============================================================================
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class DoubleConv(nn.Module):
    """Two consecutive Conv → BN → ReLU blocks, the core U-Net unit."""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class Down(nn.Module):
    """MaxPool → DoubleConv (encoder step)."""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.pool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_ch, out_ch),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool_conv(x)


class Up(nn.Module):
    """Bilinear upsample + skip-connection concat → DoubleConv (decoder step)."""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
        self.conv = DoubleConv(in_ch, out_ch)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        # Pad if spatial dims differ due to odd input sizes
        if x.shape != skip.shape:
            x = F.pad(
                x,
                [0, skip.shape[-1] - x.shape[-1], 0, skip.shape[-2] - x.shape[-2]],
            )
        x = torch.cat([skip, x], dim=1)
        return self.conv(x)


# ---------------------------------------------------------------------------
# U-Net
# ---------------------------------------------------------------------------

class UNet(nn.Module):
    """
    U-Net for binary wound segmentation.

    Args
    ----
    in_channels  : 3 for RGB
    base_filters : 32 (default) — doubling at each encoder level
    """

    def __init__(self, in_channels: int = 3, base_filters: int = 32, out_channels: int = 1, num_classes: int = None):
        super().__init__()
        f = base_filters  # shorthand
        out_ch = num_classes if num_classes is not None else out_channels

        # Encoder
        self.enc1 = DoubleConv(in_channels, f)      # 256 → 256
        self.enc2 = Down(f, f * 2)                  # 256 → 128
        self.enc3 = Down(f * 2, f * 4)              # 128 → 64
        self.enc4 = Down(f * 4, f * 8)              # 64  → 32

        # Bottleneck
        self.bottleneck = Down(f * 8, f * 16)       # 32  → 16

        # Decoder (in_ch = bottleneck_ch + skip_ch)
        self.dec4 = Up(f * 16 + f * 8, f * 8)      # 16  → 32
        self.dec3 = Up(f * 8  + f * 4, f * 4)      # 32  → 64
        self.dec2 = Up(f * 4  + f * 2, f * 2)      # 64  → 128
        self.dec1 = Up(f * 2  + f,     f)           # 128 → 256

        # Head: 1×1 conv producing output logits
        self.head = nn.Conv2d(f, out_ch, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder
        s1 = self.enc1(x)
        s2 = self.enc2(s1)
        s3 = self.enc3(s2)
        s4 = self.enc4(s3)

        # Bottleneck
        b = self.bottleneck(s4)

        # Decoder
        d4 = self.dec4(b,  s4)
        d3 = self.dec3(d4, s3)
        d2 = self.dec2(d3, s2)
        d1 = self.dec1(d2, s1)

        return self.head(d1)


# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    model = UNet(in_channels=3, base_filters=32)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"U-Net trainable parameters: {total_params:,}")

    dummy = torch.zeros(2, 3, 256, 256)
    out   = model(dummy)
    print(f"Input  shape : {dummy.shape}")
    print(f"Output shape : {out.shape}")   # should be (2, 1, 256, 256)
    assert out.shape == (2, 1, 256, 256), "Shape mismatch!"
    print("Architecture OK.")
