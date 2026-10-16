"""
GAN testing script for MediPaw (Thoracic and Eye conditional GANs).
Runs a quick forward pass, computes adversarial loss on a dummy batch,
and saves a few generated sample images for visual inspection.
"""

import os
import torch
import torch.nn as nn
from torchvision.utils import save_image

# Import the GAN classes
import sys
import os
# Ensure the project root is on the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gan.conditional_gan import (
    ThoracicGenerator, ThoracicDiscriminator,
    EyeGenerator, EyeDiscriminator,
    weights_init,
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def test_thoracic_gan(batch_size: int = 4, noise_dim: int = 100):
    # Conditioning: random VHS score in [0, 1]
    vhs = torch.rand(batch_size, 1, device=DEVICE)
    z = torch.randn(batch_size, noise_dim, device=DEVICE)

    G = ThoracicGenerator(noise_dim=noise_dim).to(DEVICE)
    D = ThoracicDiscriminator().to(DEVICE)
    G.apply(weights_init)
    D.apply(weights_init)

    # Generate fake images
    fake_imgs = G(z, vhs)
    # Discriminator output on fake images
    pred_fake = D(fake_imgs, vhs)

    # Simple adversarial loss (BCE with target 0 for fake)
    criterion = nn.BCELoss()
    fake_labels = torch.zeros(batch_size, device=DEVICE)
    loss_g = criterion(pred_fake, fake_labels)
    print(f"[Thoracic GAN] Generator adversarial loss (dummy batch): {loss_g.item():.4f}")

    # Save sample images
    save_path = os.path.join("gan", "samples")
    os.makedirs(save_path, exist_ok=True)
    # Rescale from [-1,1] to [0,1]
    img_grid = (fake_imgs * 0.5) + 0.5
    save_image(img_grid, os.path.join(save_path, "thoracic_sample.png"), nrow=2)
    print(f"Sample thoracic images saved to {save_path}/thoracic_sample.png")

def test_eye_gan(batch_size: int = 4, noise_dim: int = 100, num_classes: int = 5):
    # One‑hot disease label conditioning
    labels = torch.randint(0, num_classes, (batch_size, ), device=DEVICE)
    one_hot = torch.nn.functional.one_hot(labels, num_classes).float()
    z = torch.randn(batch_size, noise_dim, device=DEVICE)

    G = EyeGenerator(num_classes=num_classes, noise_dim=noise_dim).to(DEVICE)
    D = EyeDiscriminator(num_classes=num_classes).to(DEVICE)
    G.apply(weights_init)
    D.apply(weights_init)

    fake_imgs = G(z, one_hot)
    pred_fake = D(fake_imgs, one_hot)
    criterion = nn.BCELoss()
    fake_labels = torch.zeros(batch_size, device=DEVICE)
    loss_g = criterion(pred_fake, fake_labels)
    print(f"[Eye GAN] Generator adversarial loss (dummy batch): {loss_g.item():.4f}")

    save_path = os.path.join("gan", "samples")
    os.makedirs(save_path, exist_ok=True)
    img_grid = (fake_imgs * 0.5) + 0.5
    save_image(img_grid, os.path.join(save_path, "eye_sample.png"), nrow=2)
    print(f"Sample eye images saved to {save_path}/eye_sample.png")

if __name__ == "__main__":
    print("Running dummy GAN tests...")
    test_thoracic_gan()
    test_eye_gan()
    print("Done.")
