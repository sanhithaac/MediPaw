"""
conditional_gan.py
-----------------
Simple conditional GAN implementation (cGAN) for MediPaw.
Two generators are provided:
* `ThoracicGenerator` – generates a 224×224 RGB radiograph conditioned on a scalar VHS score.
* `EyeGenerator` – generates a 224×224 RGB eye image conditioned on a one‑hot disease label.
Both share a common `BaseGenerator` backbone (transpose convolutions) and accept a noise vector `z` (dim 100) plus a conditioning vector.
Two discriminators (`ThoracicDiscriminator`, `EyeDiscriminator`) evaluate realism and the conditioning consistency.
The implementation is deliberately lightweight so it can be trained on CPU/GPU within the project constraints.
"""

import torch
# pyrefly: ignore [missing-import]
import torch.nn as nn

class BaseGenerator(nn.Module):
    """Common generator backbone used for both modalities.
    Input: concatenated noise (`z`) and conditioning vector (`c`).
    Output: 3×224×224 image (RGB).
    """
    def __init__(self, noise_dim: int, cond_dim: int, feature_maps: int = 64):
        super().__init__()
        self.input_dim = noise_dim + cond_dim
        self.net = nn.Sequential(
            # Input is (input_dim) × 1 × 1 -> 7×7
            nn.ConvTranspose2d(self.input_dim, feature_maps * 8, 7, 1, 0, bias=False),
            nn.BatchNorm2d(feature_maps * 8),
            nn.ReLU(True),
            # 7×7 -> 14×14
            nn.ConvTranspose2d(feature_maps * 8, feature_maps * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps * 4),
            nn.ReLU(True),
            # 14×14 -> 28×28
            nn.ConvTranspose2d(feature_maps * 4, feature_maps * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps * 2),
            nn.ReLU(True),
            # 28×28 -> 56×56
            nn.ConvTranspose2d(feature_maps * 2, feature_maps, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps),
            nn.ReLU(True),
            # 56×56 -> 112×112
            nn.ConvTranspose2d(feature_maps, feature_maps // 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps // 2),
            nn.ReLU(True),
            # 112×112 -> 224×224
            nn.ConvTranspose2d(feature_maps // 2, 3, 4, 2, 1, bias=False),
            nn.Tanh()  # Output in [-1, 1]
        )

    def forward(self, z: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        # z: (B, noise_dim), c: (B, cond_dim)
        x = torch.cat([z, c], dim=1)
        x = x.view(x.size(0), self.input_dim, 1, 1)
        return self.net(x)

class ThoracicGenerator(BaseGenerator):
    """Generator for thoracic radiographs.
    Conditioning is a single scalar VHS score (float) normalised to [0, 1].
    """
    def __init__(self, noise_dim: int = 100):
        super().__init__(noise_dim=noise_dim, cond_dim=1)

    def forward(self, z: torch.Tensor, vhs: torch.Tensor) -> torch.Tensor:
        # vhs shape: (B, 1)
        return super().forward(z, vhs)

class EyeGenerator(BaseGenerator):
    """Generator for eye images.
    Conditioning is a one‑hot vector of length `num_classes`.
    """
    def __init__(self, num_classes: int, noise_dim: int = 100):
        super().__init__(noise_dim=noise_dim, cond_dim=num_classes)
        self.num_classes = num_classes

    def forward(self, z: torch.Tensor, label_onehot: torch.Tensor) -> torch.Tensor:
        return super().forward(z, label_onehot)

class BaseDiscriminator(nn.Module):
    """Common discriminator backbone.
    Takes a 3×224×224 image and the conditioning vector, and outputs a probability.
    """
    def __init__(self, cond_dim: int, feature_maps: int = 64):
        super().__init__()
        self.cond_dim = cond_dim
        self.features = nn.Sequential(
            # 224x224 -> 112x112
            nn.Conv2d(3, feature_maps, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            # 112x112 -> 56x56
            nn.Conv2d(feature_maps, feature_maps * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps * 2),
            nn.LeakyReLU(0.2, inplace=True),
            # 56x56 -> 28x28
            nn.Conv2d(feature_maps * 2, feature_maps * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps * 4),
            nn.LeakyReLU(0.2, inplace=True),
            # 28x28 -> 14x14
            nn.Conv2d(feature_maps * 4, feature_maps * 8, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps * 8),
            nn.LeakyReLU(0.2, inplace=True),
            # 14x14 -> 7x7
            nn.Conv2d(feature_maps * 8, feature_maps * 8, 4, 2, 1, bias=False),
            nn.BatchNorm2d(feature_maps * 8),
            nn.LeakyReLU(0.2, inplace=True),
        )
        # Linear projection to embed conditioning to a 7x7 spatial feature map
        self.cond_proj = nn.Linear(self.cond_dim, 7 * 7)
        # Final classifier combines (feature_maps * 8 + 1) channels at 7x7 -> 1x1
        self.classifier = nn.Sequential(
            nn.Conv2d(feature_maps * 8 + 1, 1, 7, 1, 0, bias=False),
            nn.Sigmoid()
        )

    def forward(self, img: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        # img: (B,3,224,224), c: (B,cond_dim)
        feat = self.features(img)  # shape (B, feature_maps*8, 7, 7)
        cond_map = self.cond_proj(c).view(c.size(0), 1, 7, 7)
        combined = torch.cat([feat, cond_map], dim=1)  # (B, feature_maps*8 + 1, 7, 7)
        out = self.classifier(combined)
        return out.view(-1)

class ThoracicDiscriminator(BaseDiscriminator):
    def __init__(self):
        # Conditioning is a scalar VHS score → dim 1
        super().__init__(cond_dim=1)

class EyeDiscriminator(BaseDiscriminator):
    def __init__(self, num_classes: int):
        super().__init__(cond_dim=num_classes)
        self.num_classes = num_classes

# Helper utilities ----------------------------------------------------------

def weights_init(m: nn.Module):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)

if __name__ == "__main__":
    # Simple sanity‑check: instantiate and print model summaries
    G_t = ThoracicGenerator()
    D_t = ThoracicDiscriminator()
    G_e = EyeGenerator(num_classes=5)
    D_e = EyeDiscriminator(num_classes=5)
    print("Thoracic Generator:", G_t)
    print("Thoracic Discriminator:", D_t)
    print("Eye Generator:", G_e)
    print("Eye Discriminator:", D_e)

