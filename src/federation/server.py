"""
Federated Server — Central aggregator for cross-modal prototype sharing.
=========================================================================
The server:
    1. Receives per-class prototypes from all clients (tiny vectors, ~512 bytes each)
    2. Computes weighted-average global prototypes
    3. Broadcasts global prototypes back to all clients
    4. Tracks convergence metrics (prototype distances, alignment quality)

No model parameters are ever transmitted — only class-mean projected
embeddings. This preserves privacy and makes the protocol architecture-agnostic.

Aggregation weighting strategies:
    - 'count':  weight = sample_count  (original — favours large datasets)
    - 'sqrt':   weight = √sample_count (balanced — reduces domination)
    - 'equal':  weight = 1.0           (uniform — all clients equal)

Reference:
    FedProto (Tan et al., AAAI 2022) — AAAI 36(8), 8432–8440
"""

import torch
import torch.nn.functional as F
from collections import defaultdict


class FederatedServer:
    """
    Central server that aggregates prototypes from heterogeneous clients.

    The server never sees raw data or model parameters.
    It only handles tiny prototype vectors (2 × proj_dim floats per client).

    Args:
        num_classes: Number of output classes (default 2).
        proj_dim:    Dimension of shared projection space (default 64).
        weighting:   Aggregation weighting strategy: 'count', 'sqrt', or 'equal'.
                     'sqrt' reduces domination by large-dataset clients (recommended
                     when client dataset sizes vary significantly).
    """

    def __init__(self, num_classes: int = 2, proj_dim: int = 64, weighting: str = "sqrt"):
        self.num_classes = num_classes
        self.proj_dim = proj_dim
        self.weighting = weighting

        # Current global prototypes
        self.global_prototypes: dict[int, torch.Tensor] = {}

        # History for convergence tracking
        self.history = {
            "global_proto_norms": [],       # per-round norm of each class proto
            "inter_client_distances": [],   # per-round pairwise proto distances
            "proto_shift": [],              # how much global protos moved this round
        }

    def _get_weight(self, count: int) -> float:
        """Map raw sample count to aggregation weight based on strategy."""
        if self.weighting == "sqrt":
            return count ** 0.5
        elif self.weighting == "equal":
            return 1.0
        else:  # 'count'
            return float(count)

    def aggregate_prototypes(
        self,
        client_prototypes: dict[str, dict[int, torch.Tensor]],
        client_counts: dict[str, dict[int, int]],
    ) -> dict[int, torch.Tensor]:
        """
        Weighted average of client prototypes → global prototypes.

        With 'sqrt' weighting:
            G_c = Σ_i (√n_i_c * p_i_c) / Σ_i (√n_i_c)

        This reduces the domination of large-dataset clients (e.g., ECG with 14K
        samples) over small-dataset clients (e.g., Echo with 3K samples).

        Args:
            client_prototypes: {client_id: {class_id: (proj_dim,)}}
            client_counts:     {client_id: {class_id: int}}

        Returns:
            global_prototypes: {class_id: (proj_dim,)} — weighted average
        """
        old_protos = {k: v.clone() for k, v in self.global_prototypes.items()}

        new_global = {}
        for class_id in range(self.num_classes):
            weighted_sum = torch.zeros(self.proj_dim)
            total_weight = 0.0

            for client_id, protos in client_prototypes.items():
                if class_id in protos:
                    count = client_counts[client_id].get(class_id, 0)
                    if count > 0:
                        w = self._get_weight(count)
                        weighted_sum += w * protos[class_id]
                        total_weight += w

            if total_weight > 0:
                new_global[class_id] = weighted_sum / total_weight
            else:
                # Fallback: keep previous or initialize to zero
                new_global[class_id] = self.global_prototypes.get(
                    class_id, torch.zeros(self.proj_dim)
                )

        # Track how much prototypes shifted
        if old_protos:
            shifts = []
            for c in new_global:
                if c in old_protos:
                    shift = (new_global[c] - old_protos[c]).norm().item()
                    shifts.append(shift)
            self.history["proto_shift"].append(
                sum(shifts) / len(shifts) if shifts else 0.0
            )
        else:
            self.history["proto_shift"].append(float("inf"))

        # Track global prototype norms
        norms = {c: new_global[c].norm().item() for c in new_global}
        self.history["global_proto_norms"].append(norms)

        # Track inter-client distances (how aligned are the clients?)
        self._compute_inter_client_distances(client_prototypes)

        self.global_prototypes = new_global
        return new_global

    def _compute_inter_client_distances(
        self,
        client_prototypes: dict[str, dict[int, torch.Tensor]],
    ):
        """
        Compute pairwise cosine distances between clients' same-class prototypes.
        This measures alignment quality — smaller = better alignment.
        """
        client_ids = list(client_prototypes.keys())
        if len(client_ids) < 2:
            self.history["inter_client_distances"].append({})
            return

        distances = {}
        for class_id in range(self.num_classes):
            class_dists = []
            for i in range(len(client_ids)):
                for j in range(i + 1, len(client_ids)):
                    c_i, c_j = client_ids[i], client_ids[j]
                    if class_id in client_prototypes[c_i] and class_id in client_prototypes[c_j]:
                        p_i = client_prototypes[c_i][class_id]
                        p_j = client_prototypes[c_j][class_id]
                        cos_dist = 1.0 - F.cosine_similarity(
                            p_i.unsqueeze(0), p_j.unsqueeze(0)
                        ).item()
                        class_dists.append({
                            "pair": f"{c_i}-{c_j}",
                            "cosine_distance": cos_dist,
                        })
            distances[f"class_{class_id}"] = class_dists

        self.history["inter_client_distances"].append(distances)

    def get_class_separation(self) -> float:
        """
        Compute cosine distance between global prototypes of different classes.
        Larger = better separation. If it collapses toward 0, both classes
        are mapping to the same point (prototype collapse).
        """
        if len(self.global_prototypes) < 2:
            return 0.0

        p0 = self.global_prototypes[0]
        p1 = self.global_prototypes[1]
        return 1.0 - F.cosine_similarity(p0.unsqueeze(0), p1.unsqueeze(0)).item()

    def check_convergence(self, window: int = 5, threshold: float = 0.01) -> bool:
        """
        Check if prototypes have converged (stopped shifting meaningfully).

        Args:
            window:    Number of recent rounds to check
            threshold: Maximum average shift to consider converged

        Returns:
            True if the average prototype shift over the last `window` rounds
            is below `threshold`.
        """
        shifts = self.history["proto_shift"]
        if len(shifts) < window:
            return False
        recent = shifts[-window:]
        avg_shift = sum(recent) / len(recent)
        return avg_shift < threshold

    def get_alignment_summary(self, round_num: int) -> str:
        """Format a human-readable alignment quality summary."""
        sep = self.get_class_separation()
        shift = self.history["proto_shift"][-1] if self.history["proto_shift"] else float("inf")

        lines = [
            f"  |- Class separation (cosine dist): {sep:.4f}",
            f"  |- Proto shift from last round:    {shift:.6f}",
            f"  |- Aggregation weighting:          {self.weighting}",
        ]

        # Inter-client alignment
        if self.history["inter_client_distances"]:
            latest = self.history["inter_client_distances"][-1]
            for class_key, pairs in latest.items():
                for p in pairs:
                    lines.append(
                        f"  |- {class_key} {p['pair']} alignment: "
                        f"cos_dist={p['cosine_distance']:.4f}"
                    )

        converged = self.check_convergence()
        lines.append(f"  |- Converged: {'YES' if converged else 'not yet'}")

        return "\n".join(lines)
