"""
ECG Model — Hospital B (ZZU-pECG)
====================================
Input:  ECG tensor (N, 9, 5000) — 9 leads, 5000 samples (10 sec @ 500 Hz)

Architecture:
    Compact 1D ResNet with 5 residual blocks.
    Each block: Conv1d(k=7) → BN → ReLU → Conv1d(k=7) → BN + skip connection
    Increasing channel width: 32 → 64 → 128 → 256 → 256
    After blocks: global average pool → fc(128) → fc(2)

The 9-channel input handles both 9-lead and 12-lead records uniformly
(12-lead records padded to 9 leads were already handled in ecg_pipeline.py
by taking the first 9 leads).

Penultimate layer (fc(128)) = the embedding used for prototype vectors (Week 4).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ResBlock1D(nn.Module):
    """1D Residual block with optional down-sampling via stride."""

    def __init__(self, in_ch: int, out_ch: int, stride: int = 1, kernel_size: int = 7):
        super().__init__()
        pad = kernel_size // 2
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size, stride=stride, padding=pad, bias=False)
        self.bn1   = nn.BatchNorm1d(out_ch)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size, stride=1, padding=pad, bias=False)
        self.bn2   = nn.BatchNorm1d(out_ch)

        self.skip = nn.Sequential()
        if stride != 1 or in_ch != out_ch:
            self.skip = nn.Sequential(
                nn.Conv1d(in_ch, out_ch, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm1d(out_ch),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = out + self.skip(x)
        return F.relu(out)


class ECGResNet(nn.Module):
    """
    Compact 1D ResNet for pediatric ECG binary screening.

    Args:
        in_channels: number of ECG leads (default 9).
        embed_dim:   size of penultimate embedding (default 128).
        num_classes: 2 for binary screening.
        dropout:     dropout probability before classification head.
    """

    def __init__(
        self,
        in_channels: int = 9,
        embed_dim: int = 128,
        num_classes: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()

        # Stem: bring to 32 channels, downsample 4× early
        self.stem = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=15, stride=4, padding=7, bias=False),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=3, stride=2, padding=1),   # → L//8 ≈ 625
        )

        # Residual blocks — stride=2 at start of each block halves sequence length
        self.layer1 = ResBlock1D(32,  64,  stride=2)   # → ~312
        self.layer2 = ResBlock1D(64,  128, stride=2)   # → ~156
        self.layer3 = ResBlock1D(128, 256, stride=2)   # → ~78
        self.layer4 = ResBlock1D(256, 256, stride=2)   # → ~39

        self.gap     = nn.AdaptiveAvgPool1d(1)          # → (N, 256, 1)
        self.dropout = nn.Dropout(dropout)

        self.embed_dim = embed_dim
        self.fc_embed  = nn.Linear(256, embed_dim)
        self.fc_out    = nn.Linear(embed_dim, num_classes)

    def forward(self, x: torch.Tensor, return_embedding: bool = False):
        """
        Args:
            x: (N, 9, 5000)
            return_embedding: if True, also return the embed_dim-d embedding
        Returns:
            logits: (N, num_classes)
            embedding (optional): (N, embed_dim)
        """
        x = self.stem(x)      # (N, 32, ~625)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.gap(x).squeeze(-1)   # (N, 256)
        x = self.dropout(x)
        emb = F.relu(self.fc_embed(x))  # (N, embed_dim)
        logits = self.fc_out(emb)       # (N, 2)

        if return_embedding:
            return logits, emb
        return logits


def get_ecg_model(in_channels: int = 9, embed_dim: int = 128, dropout: float = 0.3) -> ECGResNet:
    """Factory function — returns an untrained ECGResNet."""
    return ECGResNet(in_channels=in_channels, embed_dim=embed_dim, dropout=dropout)


if __name__ == "__main__":
    model = get_ecg_model()
    dummy = torch.randn(4, 9, 5000)        # batch=4, 9 leads, 5000 samples
    logits, emb = model(dummy, return_embedding=True)
    print(f"Input:     {dummy.shape}")
    print(f"Logits:    {logits.shape}")    # (4, 2)
    print(f"Embedding: {emb.shape}")       # (4, 128)
    total = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {total:,}")
