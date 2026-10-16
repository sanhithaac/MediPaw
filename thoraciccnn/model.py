"""
Thoracic CNN Model Architecture for MediPaw.

Designed for canine thoracic radiograph analysis:
1. Feature Extractor Head: Outputs a 576-dim intermediate embedding tailored for
   downstream MediPaw Multi-Modal ViT fusion.
2. VHS Regression Head: Predicts Vertebral Heart Score (VHS) when supervised ground-truth is available.
3. Disease Classification Head: Extensible for multi-class pathology classification.
"""

from typing import Tuple, Optional, Union
import torch
import torch.nn as nn
import torchvision.models as models


class ThoracicCNN(nn.Module):
    """
    Lightweight, medical-grade CNN for Canine Thoracic Radiographs.
    """

    def __init__(
        self,
        backbone_name: str = "mobilenet_v3_small",
        pretrained: bool = True,
        dropout_rate: float = 0.25,
        num_classes: Optional[int] = None
    ):
        super(ThoracicCNN, self).__init__()
        self.backbone_name = backbone_name
        self.num_classes = num_classes

        if backbone_name == "mobilenet_v3_small":
            weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
            base = models.mobilenet_v3_small(weights=weights)
            self.features = base.features
            self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
            self.feature_dim = 576

        elif backbone_name == "resnet18":
            weights = models.ResNet18_Weights.DEFAULT if pretrained else None
            base = models.resnet18(weights=weights)
            self.features = nn.Sequential(
                base.conv1, base.bn1, base.relu, base.maxpool,
                base.layer1, base.layer2, base.layer3, base.layer4
            )
            self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
            self.feature_dim = 512

        else:
            raise ValueError(f"Unsupported backbone: {backbone_name}. Choose 'mobilenet_v3_small' or 'resnet18'.")

        # Feature projection & normalization for ViT cross-modal fusion
        self.feature_norm = nn.LayerNorm(self.feature_dim)

        # 1. Vertebral Heart Score (VHS) Regression Head
        self.regression_head = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(self.feature_dim, 128),
            nn.GELU(),
            nn.Dropout(p=dropout_rate / 2.0),
            nn.Linear(128, 1)
        )

        # 2. Extensible Pathology Classification Head
        if num_classes is not None and num_classes > 0:
            self.classifier_head = nn.Sequential(
                nn.Dropout(p=dropout_rate),
                nn.Linear(self.feature_dim, num_classes)
            )
        else:
            self.classifier_head = None

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extracts pooled and normalized feature embeddings (B, feature_dim)
        designed specifically for MediPaw Multi-Modal ViT fusion.
        """
        feat = self.features(x)
        feat = self.avgpool(feat)
        feat = torch.flatten(feat, 1)
        feat = self.feature_norm(feat)
        return feat

    def forward_with_features(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns both the prediction output and the intermediate feature vector.
        """
        features = self.extract_features(x)
        prediction = self.regression_head(features).squeeze(-1)
        return prediction, features

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Standard forward pass predicting VHS scalar (or logits if classification head active).
        """
        features = self.extract_features(x)
        if self.classifier_head is not None:
            return self.classifier_head(features)
        return self.regression_head(features).squeeze(-1)


def build_thoracic_model(
    backbone_name: str = "mobilenet_v3_small",
    pretrained: bool = True,
    dropout_rate: float = 0.25,
    num_classes: Optional[int] = None,
    device: Optional[Union[str, torch.device]] = None
) -> ThoracicCNN:
    """Factory function for building and placing ThoracicCNN on target device."""
    model = ThoracicCNN(
        backbone_name=backbone_name,
        pretrained=pretrained,
        dropout_rate=dropout_rate,
        num_classes=num_classes
    )
    if device is not None:
        model.to(device)
    return model
