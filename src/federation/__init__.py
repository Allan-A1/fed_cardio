"""
Federation package — Cross-modal prototype-based federated learning.
=====================================================================
Implements FedProto with projection-head embedding alignment for
heterogeneous modality clients (PCG, ECG, Echo).

Key components:
    ProjectionHead       — Maps native 128-d to shared 64-d alignment space
    FederatedClient      — Wraps a single hospital's model for federated training
    FederatedServer      — Aggregates prototypes from all clients
    prototype_alignment_loss  — L2 pull toward global prototype
    contrastive_prototype_loss — InfoNCE push/pull between class prototypes
"""

from src.federation.projection import ProjectionHead
from src.federation.losses import prototype_alignment_loss, contrastive_prototype_loss
from src.federation.client import FederatedClient
from src.federation.server import FederatedServer

__all__ = [
    "ProjectionHead",
    "FederatedClient",
    "FederatedServer",
    "prototype_alignment_loss",
    "contrastive_prototype_loss",
]
