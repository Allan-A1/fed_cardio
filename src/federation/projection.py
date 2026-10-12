"""
Projection Head — Maps native embeddings to shared alignment space.
====================================================================
Each federated client gets its own ProjectionHead that learns to translate
its model's native 128-d embedding into a shared 64-d coordinate system.

This is the key innovation that makes cross-modal prototype averaging
meaningful. Without it, averaging PCG, ECG, and Echo embeddings is like
averaging Chinese and English sentences character-by-character.

Architecture (v3 — two-layer MLP):
    Linear(embed_dim → hidden_dim) → BN → ReLU → Linear(hidden_dim → proj_dim)
    → L2-normalise

    The hidden layer with BatchNorm preserves discriminative information
    before the final normalisation step. A single-layer head (v2) suffers from
    ReLU dead neurons (~50% zero activations), leaving only ~32 of 64 dims
    active per sample and causing slow prototype class separation.
    The two-layer design (following SimCLR v2 / MoCo v2) consistently produces
    better-separated class prototypes and more stable contrastive loss.

Reference:
    SimCLR v2 (Chen et al., 2020) — two-layer projection head
    MFCPL (Le et al., 2024) — arXiv:2401.13898
    FedTGP (Zhang et al., AAAI 2024) — AAAI 38(15), 16768–16776
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ProjectionHead(nn.Module):
    """
    Two-layer MLP projection from native embedding space to shared alignment space.

    Architecture: Linear(embed_dim → hidden_dim) → BN → ReLU
                  → Linear(hidden_dim → proj_dim) → L2-normalise

    The hidden layer with BatchNorm preserves discriminative information that
    a single-layer head destroys via ReLU dead neurons. BN also stabilises
    gradients across heterogeneous modalities (PCG/ECG/Echo have very different
    activation scale distributions).

    Placing L2-normalisation at the output (not after BN) matches the cosine-
    similarity geometry of the contrastive prototype loss.

    Args:
        embed_dim:  Dimension of the backbone's native embedding (default 128).
        proj_dim:   Dimension of the shared alignment space (default 64).
        hidden_dim: Width of the intermediate layer (default 128).
    """

    def __init__(self, embed_dim: int = 128, proj_dim: int = 64,
                 hidden_dim: int = 128):
        super().__init__()
        self.embed_dim = embed_dim
        self.proj_dim = proj_dim
        self.net = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim, bias=False),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, proj_dim, bias=False),
        )

    def forward(self, embedding: torch.Tensor) -> torch.Tensor:
        """
        Args:
            embedding: (N, embed_dim) — native backbone embedding
        Returns:
            projected:  (N, proj_dim)  — L2-normalised, on unit hypersphere
        """
        x = self.net(embedding)              # (N, proj_dim)
        return F.normalize(x, dim=1)         # unit-norm → hypersphere


if __name__ == "__main__":
    # Quick shape, parameter & normalisation check
    head = ProjectionHead(embed_dim=128, proj_dim=64, hidden_dim=128)
    dummy = torch.randn(8, 128)
    out = head(dummy)
    print(f"Input:      {dummy.shape}")        # (8, 128)
    print(f"Projected:  {out.shape}")          # (8, 64)
    norms = out.norm(dim=1)
    print(f"L2 norms:   min={norms.min():.4f}  max={norms.max():.4f}  (should be ~1.0)")
    n_params = sum(p.numel() for p in head.parameters())
    print(f"Parameters: {n_params:,}")         # 24,832 (128*128 + 128*64)
