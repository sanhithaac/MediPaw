"""
Eye CNN Model Architecture for MediPaw Ocular Abnormality Classification.

Designed for independent ocular disease classification and downstream Multi-Modal
Vision Transformer (ViT) feature fusion:
- Supports MobileNetV3-Small (default, lightweight for CPU / edge deployment)
  and EfficientNet-B0 transfer learning backbones
- Pretrained ImageNet weights with customizable dropout and classification head
- Exposes intermediate pooled feature embeddings (e.g. 576-dim for MobileNetV3-Small)
  for downstream multi-modal cross-attention fusion in MediPaw triage
- Provides forward_features(), forward(), and predict_proba() APIs
"""

import torch
import torch.nn as nn
import torchvision.models as models
from typing import Tuple, Dict, Any, Optional


class EyeCNN(nn.Module):
    """
    Eye CNN classifier for 4-class canine ocular abnormality detection:
    - conjunctivitis
    - entropion
    - eyelid_lump
    - healthy
    """

    def __init__(
        self,
        num_classes: int = 4,
        backbone_name: str = "mobilenet_v3_small",
        pretrained: bool = True,
        dropout_rate: float = 0.2,
        freeze_backbone_layers: int = 0
    ):
        super(EyeCNN, self).__init__()
        self.num_classes = num_classes
        self.backbone_name = backbone_name.lower()
        self.dropout_rate = dropout_rate

        if self.backbone_name == "mobilenet_v3_small":
            weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
            backbone = models.mobilenet_v3_small(weights=weights)
            # MobileNetV3 features -> avgpool -> 576-dim vector
            self.features = backbone.features
            self.avgpool = backbone.avgpool
            self.feature_dim = 576

            # Custom classification head
            self.classifier = nn.Sequential(
                nn.Linear(self.feature_dim, 256),
                nn.Hardswish(),
                nn.Dropout(p=self.dropout_rate),
                nn.Linear(256, self.num_classes)
            )

        elif self.backbone_name == "efficientnet_b0":
            weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            backbone = models.efficientnet_b0(weights=weights)
            self.features = backbone.features
            self.avgpool = backbone.avgpool
            self.feature_dim = 1280

            self.classifier = nn.Sequential(
                nn.Dropout(p=self.dropout_rate),
                nn.Linear(self.feature_dim, 256),
                nn.SiLU(),
                nn.Dropout(p=self.dropout_rate),
                nn.Linear(256, self.num_classes)
            )
        else:
            raise ValueError(f"Unsupported backbone: {backbone_name}. Choose 'mobilenet_v3_small' or 'efficientnet_b0'.")

        # Optional layer freezing for fine-tuning
        if freeze_backbone_layers > 0:
            for idx, child in enumerate(self.features.children()):
                if idx < freeze_backbone_layers:
                    for param in child.parameters():
                        param.requires_grad = False

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extracts the 1D global pooled feature embedding vector.
        This embedding is consumed downstream by the MediPaw Multi-Modal ViT.

        Args:
            x: Input tensor of shape (B, 3, H, W)
        Returns:
            embedding: Feature tensor of shape (B, feature_dim)
                       (576 for mobilenet_v3_small, 1280 for efficientnet_b0)
        """
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Standard forward pass returning unnormalized class logits.

        Args:
            x: Input tensor of shape (B, 3, 224, 224)
        Returns:
            logits: Tensor of shape (B, num_classes)
        """
        features = self.forward_features(x)
        logits = self.classifier(features)
        return logits

    def forward_with_features(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns both logits and intermediate feature embeddings in a single pass.
        Facilitates joint inference for downstream multi-modal transformer fusion.

        Returns:
            (logits, features):
                logits shape: (B, num_classes)
                features shape: (B, feature_dim)
        """
        features = self.forward_features(x)
        logits = self.classifier(features)
        return logits, features

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """
        Returns normalized class probabilities via Softmax.
        """
        logits = self.forward(x)
        return torch.softmax(logits, dim=1)


def build_eye_model(
    num_classes: int = 4,
    backbone_name: str = "mobilenet_v3_small",
    pretrained: bool = True,
    dropout_rate: float = 0.2,
    device: Optional[torch.device] = None
) -> EyeCNN:
    """
    Factory function to instantiate and initialize the EyeCNN model.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = EyeCNN(
        num_classes=num_classes,
        backbone_name=backbone_name,
        pretrained=pretrained,
        dropout_rate=dropout_rate
    )
    model.to(device)
    return model


if __name__ == "__main__":
    # Smoke test model initialization and feature dimensions
    print("Testing EyeCNN model instantiation and feature extractor...")
    sample_input = torch.randn(2, 3, 224, 224)

    # Test MobileNetV3-Small
    model_mb = build_eye_model(num_classes=4, backbone_name="mobilenet_v3_small", pretrained=False)
    logits_mb, feats_mb = model_mb.forward_with_features(sample_input)
    print(f"MobileNetV3-Small: logits shape = {logits_mb.shape}, feature embedding shape = {feats_mb.shape} (Dim: {model_mb.feature_dim})")
    assert logits_mb.shape == (2, 4)
    assert feats_mb.shape == (2, 576)

    # Test EfficientNet-B0
    model_ef = build_eye_model(num_classes=4, backbone_name="efficientnet_b0", pretrained=False)
    logits_ef, feats_ef = model_ef.forward_with_features(sample_input)
    print(f"EfficientNet-B0: logits shape = {logits_ef.shape}, feature embedding shape = {feats_ef.shape} (Dim: {model_ef.feature_dim})")
    assert logits_ef.shape == (2, 4)
    assert feats_ef.shape == (2, 1280)

    print("Model smoke test passed successfully!")
