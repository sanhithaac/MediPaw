"""
Multi-Modal Vision Transformer (ViT) Fusion Model for MediPaw.

Architecture:
    - Accepts a variable list of 576-dimensional feature embeddings (one per active model)
    - Treats each embedding as a "token" in a small Transformer encoder
    - A CLS token aggregates cross-modal information
    - Regression head - scalar clinical urgency score [0, 1]
    - Classification head - multi-class triage category (Low / Medium / High / Critical)

Design constraints (scientific rigor):
    - No arbitrary confidence summation across unrelated classifiers
    - The fusion model itself must be trained on multi-modal clinical cohorts to produce
      autonomous triage scores. Until that training occurs, outputs are marked as
      architecture_prototype and the rule-based fallback in server.py is used instead.
    - Feature embeddings from trained models (Eye CNN, Thoracic CNN) ARE extracted and
      returned for archival and future fine-tuning.
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Union

import torch
import torch.nn as nn


class LearnablePositionalEncoding(nn.Module):
    """Learned positional embeddings for up to max_tokens modality tokens + 1 CLS."""

    def __init__(self, d_model: int, max_tokens: int = 8):
        super().__init__()
        self.pe = nn.Embedding(max_tokens + 1, d_model)

    def forward(self, seq_len: int) -> torch.Tensor:
        idx = torch.arange(seq_len, device=self.pe.weight.device)
        return self.pe(idx)


class MultiModalViT(nn.Module):
    """
    Cross-modal Transformer encoder that fuses feature embeddings from
    multiple MediPaw CNN models into a single clinical urgency representation.
    """

    TRIAGE_CLASSES = ["Low", "Medium", "High", "Critical"]

    def __init__(
        self,
        feature_dim: int = 576,
        d_model: int = 256,
        num_heads: int = 4,
        num_encoder_layers: int = 3,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        max_modalities: int = 6,
        num_triage_classes: int = 4,
    ):
        super().__init__()
        self.feature_dim = feature_dim
        self.d_model = d_model
        self.num_triage_classes = num_triage_classes

        self.input_projection = nn.Sequential(
            nn.Linear(feature_dim, d_model),
            nn.LayerNorm(d_model),
        )

        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        self.pos_enc = LearnablePositionalEncoding(d_model, max_tokens=max_modalities)

        enc_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(
            enc_layer,
            num_layers=num_encoder_layers,
            enable_nested_tensor=False,  # norm_first=True requires this to be False
        )

        self.urgency_head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, 64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

        self.triage_head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, 64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_triage_classes),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(
        self,
        embeddings: torch.Tensor,
        padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        B, N, _ = embeddings.shape

        x = self.input_projection(embeddings)
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, x], dim=1)
        pos = self.pos_enc(N + 1).unsqueeze(0)
        x = x + pos

        x = self.encoder(x, src_key_padding_mask=padding_mask)

        cls_out = x[:, 0, :]
        urgency_score = self.urgency_head(cls_out).squeeze(-1)
        triage_logits = self.triage_head(cls_out)

        return urgency_score, triage_logits, cls_out

    @classmethod
    def urgency_to_triage_label(cls, urgency: float) -> str:
        if urgency >= 0.80:
            return "Critical"
        elif urgency >= 0.55:
            return "High"
        elif urgency >= 0.30:
            return "Medium"
        else:
            return "Low"


def build_multimodal_vit(
    feature_dim: int = 576,
    d_model: int = 256,
    num_heads: int = 4,
    num_encoder_layers: int = 3,
    device: Optional[Union[str, torch.device]] = None,
) -> MultiModalViT:
    model = MultiModalViT(
        feature_dim=feature_dim,
        d_model=d_model,
        num_heads=num_heads,
        num_encoder_layers=num_encoder_layers,
    )
    if device is not None:
        if isinstance(device, str):
            device = torch.device(device)
        model.to(device)
    return model
