"""
Federated Prototype Losses
===========================
Two loss functions that train projection heads to create a shared
embedding space across heterogeneous modality clients.

Loss 1 — Prototype Alignment (L_proto):
    Pulls each sample's projected embedding toward the global prototype
    of its own class. Cosine distance on the unit hypersphere.
    Now supports per-class weighting to handle imbalanced datasets.

Loss 2 — Contrastive Prototype (L_contrast):
    InfoNCE-style: pulls toward same-class global prototype,
    pushes away from other-class global prototype.
    Now supports per-sample weighting for class-imbalanced clients.

Combined:
    L_total = L_CE + λ_proto * L_proto + λ_contrast * L_contrast

References:
    MFCPL (Le et al., 2024) — arXiv:2401.13898
    FedTGP (Zhang et al., AAAI 2024) — AAAI 38(15), 16768–16776
"""

import torch
import torch.nn.functional as F


def prototype_alignment_loss(
    projected_embeddings: torch.Tensor,
    labels: torch.Tensor,
    global_prototypes: dict[int, torch.Tensor],
    class_weights: dict[int, float] | None = None,
) -> torch.Tensor:
    """
    L_proto = weighted mean of (1 − cosine_similarity(proj(embed_i), G_{y_i}))

    Uses cosine distance instead of squared L2 because projected embeddings are
    now L2-normalised (unit vectors on the hypersphere). Cosine distance is the
    natural metric in this geometry and is consistent with the contrastive loss.

    Supports per-class weighting so that minority classes (e.g., abnormal in
    Echo's 85/15 split) contribute proportionally more to the loss.

    Args:
        projected_embeddings: (N, proj_dim) — L2-normalised output of ProjectionHead
        labels:               (N,)         — class labels (0 or 1)
        global_prototypes:    {class_id: (proj_dim,)} — global prototype per class
        class_weights:        {class_id: float} — weight per class (default: uniform)

    Returns:
        Scalar loss (weighted mean cosine distance to same-class prototype).
    """
    loss = torch.tensor(0.0, device=projected_embeddings.device)
    total_weight = 0.0

    for class_id, proto in global_prototypes.items():
        mask = labels == class_id
        if mask.sum() == 0:
            continue
        class_embeds = projected_embeddings[mask]   # (n_c, proj_dim)
        proto = proto.to(projected_embeddings.device)

        # Normalise prototype (server averages may not be unit-norm)
        proto_norm = F.normalize(proto.unsqueeze(0), dim=1)          # (1, proj_dim)
        # Cosine similarity → cosine distance = 1 − sim
        cos_sim = F.cosine_similarity(class_embeds, proto_norm.expand_as(class_embeds), dim=1)  # (n_c,)
        distances = 1.0 - cos_sim                                     # (n_c,) in [0, 2]

        w = class_weights[class_id] if class_weights is not None else 1.0
        loss = loss + w * distances.sum()
        total_weight += w * mask.sum().item()

    if total_weight > 0:
        loss = loss / total_weight
    return loss


def contrastive_prototype_loss(
    projected_embeddings: torch.Tensor,
    labels: torch.Tensor,
    global_prototypes: dict[int, torch.Tensor],
    temperature: float = 0.5,
    class_weights: dict[int, float] | None = None,
) -> torch.Tensor:
    """
    L_contrast = −log( exp(sim(z, G_pos) / τ) / Σ_c exp(sim(z, G_c) / τ) )

    InfoNCE-style contrastive loss using global prototypes as anchors.
    Pulls embeddings toward their own-class prototype, pushes away from others.

    Supports per-sample weighting derived from class weights so that minority
    class samples receive proportionally higher loss weight.

    Args:
        projected_embeddings: (N, proj_dim)
        labels:               (N,)
        global_prototypes:    {class_id: (proj_dim,)}
        temperature:          τ — controls sharpness (default 0.5)
        class_weights:        {class_id: float} — weight per class (default: uniform)

    Returns:
        Scalar contrastive loss.
    """
    if len(global_prototypes) < 2:
        return torch.tensor(0.0, device=projected_embeddings.device)

    # Stack prototypes into a matrix: (num_classes, proj_dim)
    class_ids = sorted(global_prototypes.keys())
    proto_matrix = torch.stack(
        [global_prototypes[c].to(projected_embeddings.device) for c in class_ids]
    )  # (C, proj_dim)

    # Normalize both embeddings and prototypes for cosine similarity
    z_norm = F.normalize(projected_embeddings, dim=1)       # (N, proj_dim)
    p_norm = F.normalize(proto_matrix, dim=1)                # (C, proj_dim)

    # Cosine similarity: (N, C)
    sim = torch.mm(z_norm, p_norm.T) / temperature

    # Build target: which prototype index is the positive for each sample
    # Map label values to indices in class_ids
    label_to_idx = {c: i for i, c in enumerate(class_ids)}
    targets = torch.tensor(
        [label_to_idx[y.item()] for y in labels],
        device=projected_embeddings.device,
        dtype=torch.long,
    )

    if class_weights is not None:
        # Per-sample weighted cross-entropy for class-imbalanced clients
        sample_weights = torch.tensor(
            [class_weights.get(y.item(), 1.0) for y in labels],
            device=projected_embeddings.device,
            dtype=torch.float32,
        )
        log_probs = F.log_softmax(sim, dim=1)
        nll = -log_probs[range(len(targets)), targets]
        loss = (sample_weights * nll).sum() / sample_weights.sum()
    else:
        # Standard unweighted cross-entropy
        loss = F.cross_entropy(sim, targets)

    return loss


if __name__ == "__main__":
    # Quick sanity check
    torch.manual_seed(42)
    N, D = 16, 64
    embeds = torch.randn(N, D)
    labels = torch.randint(0, 2, (N,))
    protos = {
        0: torch.randn(D),
        1: torch.randn(D),
    }

    # Without class weights
    l_proto = prototype_alignment_loss(embeds, labels, protos)
    l_contr = contrastive_prototype_loss(embeds, labels, protos, temperature=0.5)
    print(f"Prototype alignment loss (unweighted): {l_proto.item():.4f}")
    print(f"Contrastive proto loss (unweighted):   {l_contr.item():.4f}")

    # With class weights (simulating imbalanced Echo: 85/15 split)
    cw = {0: 0.588, 1: 3.333}  # inverse-frequency weights
    l_proto_w = prototype_alignment_loss(embeds, labels, protos, class_weights=cw)
    l_contr_w = contrastive_prototype_loss(embeds, labels, protos, temperature=0.5, class_weights=cw)
    print(f"Prototype alignment loss (weighted):   {l_proto_w.item():.4f}")
    print(f"Contrastive proto loss (weighted):     {l_contr_w.item():.4f}")
    print("✓ All losses computed successfully.")
