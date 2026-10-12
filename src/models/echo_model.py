"""
Echo Model — Hospital C (EchoNet-Pediatric)
============================================
Input:  echo frame tensor (N, 2, 112, 112)
        Channel 0 = End-Diastolic (ED) frame (grayscale, normalized [0,1])
        Channel 1 = End-Systolic  (ES) frame (grayscale, normalized [0,1])

Architecture (v2 — lightweight):
    4-block CNN replacing the original ResNet-18 backbone.
    Each block: Conv2d(k=3) → BN → ReLU → MaxPool(2,2)
    Channel widths: 2 → 32 → 64 → 128 → 256
    After blocks: global average pool → fc(256 → embed_dim=128) → fc(128 → 2)

    The original ResNet-18 had 11.2M parameters for just 3,258 samples
    (params/sample = 3,450:1). This lightweight version has ~422K params
    (params/sample ≈ 129:1), matching the ratio of the ECG model.

Penultimate layer (fc(128)) = the embedding used for prototype vectors.

Change rationale:
    ResNet-18 was massively over-parameterized for the small EchoNet-Pediatric
    dataset. Training from scratch (no pretraining due to 2-channel input) with
    11.2M params on 3,258 samples led to poor generalization and made the model
    vulnerable to gradient interference from FedProto's auxiliary losses.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class EchoBlock(nn.Module):
    """Conv2d → BN → ReLU → MaxPool block."""

    def __init__(self, in_ch: int, out_ch: int, pool: tuple[int, int] = (2, 2)):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False)
        self.bn   = nn.BatchNorm2d(out_ch)
        self.pool = nn.MaxPool2d(pool)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool(F.relu(self.bn(self.conv(x))))


class EchoNet(nn.Module):
    """
    Lightweight 4-block CNN for 2-channel (ED+ES frame pair) pediatric echo.

    Replaces the original ResNet-18 backbone for better fit to the small
    EchoNet-Pediatric dataset (~3,258 samples).

    Args:
        embed_dim:   size of penultimate embedding (default 128).
        num_classes: 2 for binary screening.
        dropout:     dropout probability before classification head.
    """

    def __init__(
        self,
        embed_dim: int = 128,
        num_classes: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()

        # Input: (N, 2, 112, 112)
        self.block1 = EchoBlock(2,   32,  pool=(2, 2))   # → (N, 32, 56, 56)
        self.block2 = EchoBlock(32,  64,  pool=(2, 2))   # → (N, 64, 28, 28)
        self.block3 = EchoBlock(64,  128, pool=(2, 2))   # → (N, 128, 14, 14)
        self.block4 = EchoBlock(128, 256, pool=(2, 2))   # → (N, 256, 7, 7)

        self.gap     = nn.AdaptiveAvgPool2d(1)            # → (N, 256, 1, 1)
        self.dropout = nn.Dropout(dropout)

        self.embed_dim = embed_dim
        self.fc_embed  = nn.Linear(256, embed_dim)
        self.fc_out    = nn.Linear(embed_dim, num_classes)

    def forward(self, x: torch.Tensor, return_embedding: bool = False):
        """
        Args:
            x: (N, 2, 112, 112)
            return_embedding: if True, also return the embed_dim-d embedding
        Returns:
            logits: (N, num_classes)
            embedding (optional): (N, embed_dim)
        """
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.gap(x)
        x = x.flatten(1)               # (N, 256)
        x = self.dropout(x)
        emb = F.relu(self.fc_embed(x))  # (N, embed_dim)
        logits = self.fc_out(emb)       # (N, 2)

        if return_embedding:
            return logits, emb
        return logits


def get_echo_model(embed_dim: int = 128, dropout: float = 0.3) -> EchoNet:
    """Factory function — returns an untrained EchoNet."""
    return EchoNet(embed_dim=embed_dim, dropout=dropout)


if __name__ == "__main__":
    model = get_echo_model()
    dummy = torch.randn(4, 2, 112, 112)    # batch=4, 2 frames, 112×112
    logits, emb = model(dummy, return_embedding=True)
    print(f"Input:     {dummy.shape}")
    print(f"Logits:    {logits.shape}")    # (4, 2)
    print(f"Embedding: {emb.shape}")       # (4, 128)
    total = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {total:,}")
