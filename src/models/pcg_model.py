"""
PCG Model — Hospital A (CirCor DigiScope)
==========================================
Input:  mel-spectrogram tensor (N, 64, T) — 64 mel bins, variable T
        During training T = fixed (from 5-sec segments at 4kHz):
            T = (SEGMENT_SEC * SR) / HOP_LENGTH + 1 = (5*4000)/128 + 1 = 157
Architecture:
    2D CNN treating the mel-spectrogram as a 2D image (n_mels × time).
    Shallow by design — keeps inference cheap and penultimate embedding
    accessible for cross-modal prototype computation (Week 4).

    conv → bn → relu → pool  ×3 layers
    adaptive avg-pool → flatten → fc(128) → fc(2)

Penultimate layer (fc(128)) = the embedding used for prototype vectors.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class PCGBlock(nn.Module):
    """Conv2d → BN → ReLU → MaxPool block."""

    def __init__(self, in_ch: int, out_ch: int, pool: tuple[int, int] = (2, 2)):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False)
        self.bn   = nn.BatchNorm2d(out_ch)
        self.pool = nn.MaxPool2d(pool)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.pool(F.relu(self.bn(self.conv(x))))


class PCGNet(nn.Module):
    """
    Mel-spectrogram CNN for pediatric PCG binary screening.

    Args:
        embed_dim: size of the penultimate embedding (default 128).
        num_classes: 2 for binary screening.
        dropout: dropout probability before classification head.
    """

    def __init__(self, embed_dim: int = 128, num_classes: int = 2, dropout: float = 0.3):
        super().__init__()

        # Input: (N, 1, 64, T) — add channel dim in forward()
        self.block1 = PCGBlock(1,  32,  pool=(2, 2))   # → (N, 32, 32, T//2)
        self.block2 = PCGBlock(32, 64,  pool=(2, 2))   # → (N, 64, 16, T//4)
        self.block3 = PCGBlock(64, 128, pool=(2, 2))   # → (N, 128, 8, T//8)

        self.gap     = nn.AdaptiveAvgPool2d((4, 4))     # → (N, 128, 4, 4)
        self.dropout = nn.Dropout(dropout)

        self.embed_dim = embed_dim
        self.fc_embed  = nn.Linear(128 * 4 * 4, embed_dim)
        self.fc_out    = nn.Linear(embed_dim, num_classes)

    def forward(self, x: torch.Tensor, return_embedding: bool = False):
        """
        Args:
            x: (N, 64, T) or (N, 1, 64, T)
            return_embedding: if True, also return the 128-d embedding
        Returns:
            logits: (N, num_classes)
            embedding (optional): (N, embed_dim)
        """
        if x.dim() == 3:
            x = x.unsqueeze(1)          # (N, 1, 64, T)

        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.gap(x)
        x = x.flatten(1)               # (N, 128*4*4)
        x = self.dropout(x)
        emb = F.relu(self.fc_embed(x)) # (N, embed_dim)
        logits = self.fc_out(emb)      # (N, 2)

        if return_embedding:
            return logits, emb
        return logits


def get_pcg_model(embed_dim: int = 128, dropout: float = 0.3) -> PCGNet:
    """Factory function — returns an untrained PCGNet."""
    return PCGNet(embed_dim=embed_dim, dropout=dropout)


if __name__ == "__main__":
    # Quick shape check
    model = get_pcg_model()
    dummy = torch.randn(4, 64, 157)        # batch=4, 64 mels, 157 time steps
    logits, emb = model(dummy, return_embedding=True)
    print(f"Input:     {dummy.shape}")
    print(f"Logits:    {logits.shape}")    # (4, 2)
    print(f"Embedding: {emb.shape}")       # (4, 128)
    total = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {total:,}")
