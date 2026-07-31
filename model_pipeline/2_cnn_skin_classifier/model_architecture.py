import torch
import torch.nn as nn
import torchvision.models as models

class MediPawSkinClassifier(nn.Module):
    """
    CNN 1 Architecture for Veterinary Skin Pathology Classification.
    Supports both modern EfficientNet-V2-Small and ResNet-50 backbones for Review 2 comparison.
    """
    def __init__(self, num_classes=6, dropout_rate=0.4, backbone_type="efficientnet_v2_s", freeze_backbone=False):
        super(MediPawSkinClassifier, self).__init__()
        self.backbone_type = backbone_type
        
        if backbone_type == "efficientnet_v2_s":
            print("[Architecture] Initializing EfficientNet-V2-Small backbone (Fused-MBConv spatial micro-texture recognition)...")
            weights = models.EfficientNet_V2_S_Weights.DEFAULT
            self.backbone = models.efficientnet_v2_s(weights=weights)
            
            in_features = self.backbone.classifier[1].in_features
            # Substitute default ImageNet linear head with Review 2 Justified regularized head
            self.backbone.classifier = nn.Sequential(
                nn.Dropout(p=dropout_rate),
                nn.Linear(in_features, 512),
                nn.BatchNorm1d(512, momentum=0.99, eps=1e-5),
                nn.LeakyReLU(negative_slope=0.01, inplace=True),
                nn.Dropout(p=dropout_rate),
                nn.Linear(512, num_classes)
            )
            head_module = self.backbone.classifier

        else: # Fallback to ResNet-50 baseline
            print("[Architecture] Initializing ResNet-50 baseline backbone...")
            weights = models.ResNet50_Weights.DEFAULT
            self.backbone = models.resnet50(weights=weights)
            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Sequential(
                nn.Dropout(p=dropout_rate),
                nn.Linear(in_features, 512),
                nn.BatchNorm1d(512, momentum=0.99, eps=1e-5),
                nn.LeakyReLU(negative_slope=0.01, inplace=True),
                nn.Dropout(p=dropout_rate),
                nn.Linear(512, num_classes)
            )
            head_module = self.backbone.fc

        if freeze_backbone:
            self.freeze_backbone(freeze=True)
            print("[Architecture] Interior feature extractor convolutional weights frozen.")

        # Apply He-Normal (Kaiming) initialization to our new classifier head
        self._initialize_weights(head_module)
        print(f"[Architecture] Custom {num_classes}-Class Veterinary Diagnostic Head active with Kaiming weights & Dropout(p={dropout_rate}).")

    def _initialize_weights(self, head_module):
        """Applies He-Normal (Kaiming) initialization designed specifically for LeakyReLU activations."""
        for m in head_module.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='leaky_relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1.0)
                nn.init.constant_(m.bias, 0.0)

    def freeze_backbone(self, freeze=True):
        """Toggles locking on interior convolutional feature extractors for 2-Stage Transfer Learning Warmup."""
        for name, param in self.backbone.named_parameters():
            if ("classifier" not in name) and ("fc" not in name):
                param.requires_grad = not freeze

    def forward(self, x):
        return self.backbone(x)

if __name__ == "__main__":
    # Rapid architectural verification test
    model_eff = MediPawSkinClassifier(num_classes=6, dropout_rate=0.4, backbone_type="efficientnet_v2_s")
    dummy_input = torch.randn(2, 3, 224, 224)
    out = model_eff(dummy_input)
    print(f"\n[SUCCESS] EfficientNet-V2 Forward Pass Verified! Tensor Shape: {dummy_input.shape} -> Logits: {out.shape}")
