"""
Federation Utilities — Visualization, logging, and convergence analysis.
=========================================================================
Provides comprehensive plotting and analysis for understanding the
federated learning process:

    1. AUROC curves per client over rounds
    2. Loss component breakdown (CE vs proto vs contrastive)
    3. Prototype alignment convergence
    4. t-SNE embedding visualization
    5. Federation summary dashboard
    6. Solo baseline comparison
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Color palette — consistent across all plots
CLIENT_COLORS = {
    "pcg":  "#4C72B0",   # steel blue
    "ecg":  "#DD8452",   # terracotta
    "echo": "#55A868",   # sage green
}
CLIENT_LABELS = {
    "pcg":  "Hospital A (PCG)",
    "ecg":  "Hospital B (ECG)",
    "echo": "Hospital C (Echo)",
}
CLASS_COLORS = {0: "#2ecc71", 1: "#e74c3c"}
CLASS_LABELS = {0: "Normal", 1: "Abnormal"}


def plot_auroc_curves(
    round_metrics: dict[str, list[dict]],
    save_path: str,
    baseline_aurocs: dict[str, float] | None = None,
):
    """
    Plot per-client val AUROC over federation rounds.

    Args:
        round_metrics: {client_id: [{"auroc": ..., "round": ...}, ...]}
        save_path:     Where to save the figure
        baseline_aurocs: {client_id: auroc} — solo baseline for comparison
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for client_id, metrics in round_metrics.items():
        rounds = [m["round"] for m in metrics]
        aurocs = [m["auroc"] for m in metrics]
        color = CLIENT_COLORS.get(client_id, "#999999")
        label = CLIENT_LABELS.get(client_id, client_id)

        ax.plot(rounds, aurocs, marker="o", markersize=4, linewidth=2,
                color=color, label=f"{label} (Fed)")

        # Plot solo baseline as dashed horizontal line
        if baseline_aurocs and client_id in baseline_aurocs:
            ax.axhline(y=baseline_aurocs[client_id], color=color, linestyle="--",
                       alpha=0.5, label=f"{label} (Solo baseline)")

    ax.set_xlabel("Federation Round", fontsize=12)
    ax.set_ylabel("Validation AUROC", fontsize=12)
    ax.set_title("Federated Learning — Per-Client AUROC Over Rounds", fontsize=14, fontweight="bold")
    ax.set_ylim(0.4, 1.02)
    ax.axhline(y=0.5, color="gray", linestyle=":", alpha=0.3, label="Chance")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] AUROC curves -> {save_path}")


def plot_loss_breakdown(
    round_losses: dict[str, list[dict]],
    save_path: str,
):
    """
    Plot loss component breakdown per client over rounds.
    Shows CE, proto, and contrastive loss on separate panels.
    """
    clients = list(round_losses.keys())
    n_clients = len(clients)

    fig, axes = plt.subplots(1, n_clients, figsize=(6 * n_clients, 5), sharey=False)
    if n_clients == 1:
        axes = [axes]

    for idx, client_id in enumerate(clients):
        ax = axes[idx]
        losses = round_losses[client_id]
        rounds = list(range(len(losses)))

        ce = [l.get("ce", 0) for l in losses]
        proto = [l.get("proto", 0) for l in losses]
        contrast = [l.get("contrast", 0) for l in losses]

        ax.plot(rounds, ce, label="CE Loss", color="#3498db", linewidth=2)
        ax.plot(rounds, proto, label="Proto Loss (×λ)", color="#e67e22", linewidth=2)
        ax.plot(rounds, contrast, label="Contrastive (×λ)", color="#9b59b6", linewidth=2)

        color = CLIENT_COLORS.get(client_id, "#999")
        label = CLIENT_LABELS.get(client_id, client_id)
        ax.set_title(f"{label}", fontsize=12, fontweight="bold", color=color)
        ax.set_xlabel("Round")
        ax.set_ylabel("Loss")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    plt.suptitle("Loss Component Breakdown Per Client", fontsize=14, fontweight="bold")
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] Loss breakdown -> {save_path}")


def plot_prototype_convergence(
    server_history: dict,
    save_path: str,
):
    """
    Plot prototype convergence metrics:
    - Left panel:  Prototype shift (how much global protos move per round)
    - Right panel: Inter-client cosine distance (alignment quality)
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: Prototype shift
    shifts = server_history.get("proto_shift", [])
    if shifts:
        rounds = list(range(len(shifts)))
        axes[0].plot(rounds, shifts, color="#e74c3c", linewidth=2, marker="o", markersize=4)
        axes[0].set_xlabel("Round")
        axes[0].set_ylabel("Average Prototype Shift (L2)")
        axes[0].set_title("Prototype Stability", fontsize=12, fontweight="bold")
        axes[0].grid(alpha=0.3)

        # Convergence threshold line
        axes[0].axhline(y=0.01, color="green", linestyle="--", alpha=0.5, label="Convergence threshold")
        axes[0].legend()

    # Panel 2: Inter-client distances
    distances_history = server_history.get("inter_client_distances", [])
    if distances_history:
        # Extract per-pair distances over rounds
        pair_data = {}
        for round_idx, round_dists in enumerate(distances_history):
            for class_key, pairs in round_dists.items():
                for p in pairs:
                    key = f"{class_key} ({p['pair']})"
                    if key not in pair_data:
                        pair_data[key] = {"rounds": [], "dists": []}
                    pair_data[key]["rounds"].append(round_idx)
                    pair_data[key]["dists"].append(p["cosine_distance"])

        colors = plt.cm.Set2(np.linspace(0, 1, len(pair_data)))
        for idx, (key, data) in enumerate(pair_data.items()):
            axes[1].plot(data["rounds"], data["dists"],
                        label=key, linewidth=2, color=colors[idx], marker="s", markersize=3)

        axes[1].set_xlabel("Round")
        axes[1].set_ylabel("Cosine Distance")
        axes[1].set_title("Inter-Client Prototype Alignment", fontsize=12, fontweight="bold")
        axes[1].legend(fontsize=7, loc="upper right")
        axes[1].grid(alpha=0.3)
        axes[1].set_ylim(bottom=0)

    plt.suptitle("Prototype Convergence Analysis", fontsize=14, fontweight="bold")
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] Prototype convergence -> {save_path}")


def plot_tsne_embeddings(
    client_embeddings: dict[str, tuple],
    save_path: str,
    perplexity: int = 30,
):
    """
    t-SNE visualization of projected embeddings from all clients in one plot.
    Shows whether the alignment space is semantically meaningful.

    Args:
        client_embeddings: {client_id: (embeddings_tensor, labels_tensor)}
        save_path: Where to save the figure
    """
    from sklearn.manifold import TSNE

    # Combine all embeddings
    all_embeds = []
    all_labels = []
    all_clients = []
    client_ids = list(client_embeddings.keys())

    for client_id in client_ids:
        embeds, labels = client_embeddings[client_id]
        # Subsample if too many points (for speed)
        n = min(len(embeds), 500)
        indices = np.random.choice(len(embeds), n, replace=False)
        all_embeds.append(embeds[indices].numpy())
        all_labels.append(labels[indices].numpy())
        all_clients.extend([client_id] * n)

    all_embeds = np.concatenate(all_embeds)
    all_labels = np.concatenate(all_labels)
    all_clients = np.array(all_clients)

    # Normalize embeddings to unit sphere so cosine similarity translates to overlapping Euclidean distance
    all_embeds_norm = all_embeds / (np.linalg.norm(all_embeds, axis=1, keepdims=True) + 1e-8)

    # Fit t-SNE
    perplexity = min(perplexity, len(all_embeds_norm) - 1)
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42, max_iter=1000)
    coords = tsne.fit_transform(all_embeds_norm)

    # Plot: color by class, marker by client
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    markers = {"pcg": "o", "ecg": "^", "echo": "s"}

    # Panel 1: Colored by class
    for client_id in client_ids:
        mask_c = all_clients == client_id
        marker = markers.get(client_id, "o")
        for class_id in [0, 1]:
            mask = mask_c & (all_labels == class_id)
            axes[0].scatter(
                coords[mask, 0], coords[mask, 1],
                c=CLASS_COLORS[class_id], marker=marker,
                alpha=0.5, s=20,
                label=f"{CLIENT_LABELS.get(client_id, client_id)} — {CLASS_LABELS[class_id]}",
            )

    axes[0].set_title("Colored by Class", fontsize=12, fontweight="bold")
    axes[0].legend(fontsize=7, loc="best", markerscale=2)
    axes[0].set_xticks([])
    axes[0].set_yticks([])

    # Panel 2: Colored by client (modality)
    for client_id in client_ids:
        mask = all_clients == client_id
        color = CLIENT_COLORS.get(client_id, "#999")
        marker = markers.get(client_id, "o")
        axes[1].scatter(
            coords[mask, 0], coords[mask, 1],
            c=color, marker=marker, alpha=0.5, s=20,
            label=CLIENT_LABELS.get(client_id, client_id),
        )

    axes[1].set_title("Colored by Modality", fontsize=12, fontweight="bold")
    axes[1].legend(fontsize=9, loc="best", markerscale=2)
    axes[1].set_xticks([])
    axes[1].set_yticks([])

    plt.suptitle("t-SNE of Projected Embeddings (Shared Alignment Space)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] t-SNE embeddings -> {save_path}")


def plot_prototype_alignment(
    client_embeddings: dict[str, tuple],
    save_path: str,
    perplexity: int = 30,
):
    """
    Visualization that clearly shows what FedProto aligns: the CLASS PROTOTYPES.

    Panel 1: t-SNE with individual points faded + prototypes as large bold stars
             If alignment worked, same-class stars from different modalities overlap.
    Panel 2: Cosine similarity heatmap between all prototypes
             Perfect alignment = 1.0 for same-class pairs across modalities.
    Panel 3: Bar chart of inter-modality prototype distances (before-context comparison).
    """
    from sklearn.manifold import TSNE
    from scipy.spatial.distance import cosine as cosine_dist

    # ---- Collect embeddings and compute per-client, per-class centroids ----
    all_embeds = []
    all_labels = []
    all_clients = []
    client_ids = list(client_embeddings.keys())
    centroids = {}  # {(client_id, class_id): centroid_vector}

    for client_id in client_ids:
        embeds, labels = client_embeddings[client_id]
        n = min(len(embeds), 500)
        np.random.seed(42)
        indices = np.random.choice(len(embeds), n, replace=False)
        sub_embeds = embeds[indices].numpy()
        sub_labels = labels[indices].numpy()
        all_embeds.append(sub_embeds)
        all_labels.append(sub_labels)
        all_clients.extend([client_id] * n)

        # Compute centroid per class using ALL data (not subsampled)
        full_embeds = embeds.numpy()
        full_labels = labels.numpy()
        for c in [0, 1]:
            mask = full_labels == c
            if mask.sum() > 0:
                centroids[(client_id, c)] = full_embeds[mask].mean(axis=0)

    all_embeds = np.concatenate(all_embeds)
    all_labels = np.concatenate(all_labels)
    all_clients = np.array(all_clients)

    # Normalize everything to unit sphere
    all_embeds_norm = all_embeds / (np.linalg.norm(all_embeds, axis=1, keepdims=True) + 1e-8)
    centroid_keys = list(centroids.keys())
    centroid_vecs = np.array([centroids[k] for k in centroid_keys])
    centroid_norms = centroid_vecs / (np.linalg.norm(centroid_vecs, axis=1, keepdims=True) + 1e-8)

    # ---- t-SNE on combined (individual points + centroids) ----
    combined = np.vstack([all_embeds_norm, centroid_norms])
    n_points = len(all_embeds_norm)
    perplexity = min(perplexity, len(combined) - 1)
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42, max_iter=1000)
    coords = tsne.fit_transform(combined)

    point_coords = coords[:n_points]
    centroid_coords = coords[n_points:]

    # ---- Figure: 3 panels ----
    fig, axes = plt.subplots(1, 3, figsize=(24, 7))
    markers = {"pcg": "o", "ecg": "^", "echo": "s"}

    # === Panel 1: t-SNE with faded points + bold prototype stars ===
    ax = axes[0]
    # Draw faded individual points
    for client_id in client_ids:
        mask_c = all_clients == client_id
        marker = markers.get(client_id, "o")
        for class_id in [0, 1]:
            mask = mask_c & (all_labels == class_id)
            ax.scatter(
                point_coords[mask, 0], point_coords[mask, 1],
                c=CLASS_COLORS[class_id], marker=marker,
                alpha=0.15, s=12, linewidths=0,
            )

    # Draw bold prototype stars
    for idx, key in enumerate(centroid_keys):
        client_id, class_id = key
        cx, cy = centroid_coords[idx]
        color = CLIENT_COLORS.get(client_id, "#999")
        edge_color = CLASS_COLORS[class_id]
        label = f"{CLIENT_LABELS.get(client_id, client_id)} - {CLASS_LABELS[class_id]}"
        ax.scatter(
            cx, cy, s=400, marker="*", c=color,
            edgecolors=edge_color, linewidths=2.5, zorder=10,
            label=label,
        )

    # Draw lines connecting same-class prototypes across modalities
    for class_id in [0, 1]:
        class_centroid_indices = [
            i for i, k in enumerate(centroid_keys) if k[1] == class_id
        ]
        if len(class_centroid_indices) >= 2:
            for i in range(len(class_centroid_indices)):
                for j in range(i + 1, len(class_centroid_indices)):
                    ci = class_centroid_indices[i]
                    cj = class_centroid_indices[j]
                    ax.plot(
                        [centroid_coords[ci, 0], centroid_coords[cj, 0]],
                        [centroid_coords[ci, 1], centroid_coords[cj, 1]],
                        color=CLASS_COLORS[class_id], linewidth=1.5,
                        linestyle="--", alpha=0.7, zorder=9,
                    )

    ax.set_title("Prototype Alignment (stars = class centroids)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=6.5, loc="best", markerscale=1.2, ncol=2)
    ax.set_xticks([])
    ax.set_yticks([])

    # === Panel 2: Cosine similarity heatmap ===
    ax2 = axes[1]
    n_centroids = len(centroid_keys)
    sim_matrix = np.zeros((n_centroids, n_centroids))
    for i in range(n_centroids):
        for j in range(n_centroids):
            sim_matrix[i, j] = 1.0 - cosine_dist(centroid_vecs[i], centroid_vecs[j])

    tick_labels = [
        f"{CLIENT_LABELS.get(k[0], k[0]).split('(')[1].rstrip(')')}-{CLASS_LABELS[k[1]]}"
        for k in centroid_keys
    ]
    im = ax2.imshow(sim_matrix, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax2.set_xticks(range(n_centroids))
    ax2.set_yticks(range(n_centroids))
    ax2.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=9)
    ax2.set_yticklabels(tick_labels, fontsize=9)

    # Annotate cells with values
    for i in range(n_centroids):
        for j in range(n_centroids):
            val = sim_matrix[i, j]
            text_color = "white" if abs(val) > 0.7 else "black"
            ax2.text(j, i, f"{val:.3f}", ha="center", va="center",
                     fontsize=9, fontweight="bold", color=text_color)

    plt.colorbar(im, ax=ax2, shrink=0.8)
    ax2.set_title("Cosine Similarity Between Prototypes", fontsize=12, fontweight="bold")

    # === Panel 3: Bar chart — inter-modality distances ===
    ax3 = axes[2]
    bar_data = []
    bar_labels = []
    bar_colors = []

    for class_id in [0, 1]:
        class_keys = [(c, class_id) for c in client_ids if (c, class_id) in centroids]
        for i in range(len(class_keys)):
            for j in range(i + 1, len(class_keys)):
                k1, k2 = class_keys[i], class_keys[j]
                dist = cosine_dist(centroids[k1], centroids[k2])
                c1_short = CLIENT_LABELS.get(k1[0], k1[0]).split("(")[1].rstrip(")")
                c2_short = CLIENT_LABELS.get(k2[0], k2[0]).split("(")[1].rstrip(")")
                bar_labels.append(f"{c1_short}-{c2_short}\n{CLASS_LABELS[class_id]}")
                bar_data.append(dist)
                bar_colors.append(CLASS_COLORS[class_id])

    bars = ax3.bar(range(len(bar_data)), bar_data, color=bar_colors, edgecolor="white", linewidth=0.5)
    ax3.set_xticks(range(len(bar_data)))
    ax3.set_xticklabels(bar_labels, fontsize=8)
    ax3.set_ylabel("Cosine Distance (lower = better aligned)", fontsize=10)
    ax3.set_title("Cross-Modality Prototype Distance", fontsize=12, fontweight="bold")
    ax3.set_ylim(0, max(bar_data) * 1.5 if bar_data else 1)
    ax3.grid(axis="y", alpha=0.3)

    # Annotate bars with exact values
    for bar, val in zip(bars, bar_data):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                 f"{val:.4f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.suptitle(
        "FedProto Alignment Analysis -- What the Models Actually Learned to Share",
        fontsize=15, fontweight="bold",
    )
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] Prototype alignment -> {save_path}")

def plot_sensitivity_specificity(
    round_metrics: dict[str, list[dict]],
    save_path: str,
):
    """
    Plot sensitivity and specificity per client over rounds.
    Important for medical screening — high sensitivity is critical.
    """
    clients = list(round_metrics.keys())
    n_clients = len(clients)

    fig, axes = plt.subplots(1, n_clients, figsize=(6 * n_clients, 5), sharey=True)
    if n_clients == 1:
        axes = [axes]

    for idx, client_id in enumerate(clients):
        ax = axes[idx]
        metrics = round_metrics[client_id]
        rounds = [m["round"] for m in metrics]
        sens = [m["sensitivity"] for m in metrics]
        spec = [m["specificity"] for m in metrics]

        ax.plot(rounds, sens, label="Sensitivity", color="#e74c3c", linewidth=2, marker="o", markersize=3)
        ax.plot(rounds, spec, label="Specificity", color="#3498db", linewidth=2, marker="s", markersize=3)

        color = CLIENT_COLORS.get(client_id, "#999")
        label = CLIENT_LABELS.get(client_id, client_id)
        ax.set_title(f"{label}", fontsize=12, fontweight="bold", color=color)
        ax.set_xlabel("Round")
        ax.set_ylabel("Rate")
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.grid(alpha=0.3)
        ax.axhline(y=0.5, color="gray", linestyle=":", alpha=0.3)

    plt.suptitle("Sensitivity & Specificity Over Rounds", fontsize=14, fontweight="bold")
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] Sensitivity/Specificity -> {save_path}")


def plot_federation_dashboard(
    round_metrics: dict[str, list[dict]],
    server_history: dict,
    round_losses: dict[str, list[dict]],
    save_path: str,
    baseline_aurocs: dict[str, float] | None = None,
):
    """
    All-in-one federation dashboard — 4-panel summary figure.
    """
    fig = plt.figure(figsize=(20, 14))
    gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.3)

    # Panel 1: AUROC curves
    ax1 = fig.add_subplot(gs[0, 0])
    for client_id, metrics in round_metrics.items():
        rounds = [m["round"] for m in metrics]
        aurocs = [m["auroc"] for m in metrics]
        color = CLIENT_COLORS.get(client_id, "#999")
        label = CLIENT_LABELS.get(client_id, client_id)
        ax1.plot(rounds, aurocs, marker="o", markersize=3, linewidth=2,
                color=color, label=f"{label}")
        if baseline_aurocs and client_id in baseline_aurocs:
            ax1.axhline(y=baseline_aurocs[client_id], color=color, linestyle="--", alpha=0.4)
    ax1.set_title("AUROC Over Rounds", fontweight="bold")
    ax1.set_xlabel("Round")
    ax1.set_ylabel("Val AUROC")
    ax1.set_ylim(0.4, 1.02)
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)

    # Panel 2: Prototype shift
    ax2 = fig.add_subplot(gs[0, 1])
    shifts = server_history.get("proto_shift", [])
    if shifts:
        ax2.plot(range(len(shifts)), shifts, color="#e74c3c", linewidth=2, marker="o", markersize=3)
        ax2.axhline(y=0.01, color="green", linestyle="--", alpha=0.5)
    ax2.set_title("Prototype Stability", fontweight="bold")
    ax2.set_xlabel("Round")
    ax2.set_ylabel("Avg Prototype Shift")
    ax2.grid(alpha=0.3)

    # Panel 3: Loss breakdown (first client)
    ax3 = fig.add_subplot(gs[1, 0])
    for client_id, losses in round_losses.items():
        rounds = list(range(len(losses)))
        total = [l.get("ce", 0) + l.get("proto", 0) + l.get("contrast", 0) for l in losses]
        color = CLIENT_COLORS.get(client_id, "#999")
        ax3.plot(rounds, total, label=CLIENT_LABELS.get(client_id, client_id),
                color=color, linewidth=2)
    ax3.set_title("Total Loss Per Client", fontweight="bold")
    ax3.set_xlabel("Round")
    ax3.set_ylabel("Loss")
    ax3.legend(fontsize=8)
    ax3.grid(alpha=0.3)

    # Panel 4: Class separation
    ax4 = fig.add_subplot(gs[1, 1])
    norms_history = server_history.get("global_proto_norms", [])
    if norms_history:
        # Plot class separation over rounds
        distances_history = server_history.get("inter_client_distances", [])
        if distances_history:
            # Average inter-client distance per round
            avg_dists = []
            for rd in distances_history:
                all_d = []
                for pairs in rd.values():
                    for p in pairs:
                        all_d.append(p["cosine_distance"])
                avg_dists.append(np.mean(all_d) if all_d else 0)
            ax4.plot(range(len(avg_dists)), avg_dists, color="#9b59b6", linewidth=2, marker="s", markersize=3)
    ax4.set_title("Avg Inter-Client Cosine Distance", fontweight="bold")
    ax4.set_xlabel("Round")
    ax4.set_ylabel("Cosine Distance (↓ = better aligned)")
    ax4.grid(alpha=0.3)

    plt.suptitle("FedProto — Federation Dashboard", fontsize=16, fontweight="bold", y=1.02)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] Dashboard -> {save_path}")


def save_federation_results(results: dict, path: str):
    """JSON-safe serialization (handles numpy types)."""
    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return str(obj)
        return obj

    def _deep_convert(obj):
        if isinstance(obj, dict):
            return {str(k): _deep_convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_deep_convert(v) for v in obj]
        return _convert(obj)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(_deep_convert(results), f, indent=2)
    print(f"  [Save] Results -> {path}")


def load_baseline_aurocs(results_dir: str = "outputs/results") -> dict[str, float]:
    """
    Load solo baseline AUROC scores if they exist.
    Returns {client_id: auroc} for comparison plots.
    """
    baselines = {}
    mapping = {
        "pcg": "pcg_baseline.json",
        "ecg": "ecg_baseline.json",
        "echo": "echo_baseline.json",
    }
    for client_id, filename in mapping.items():
        path = os.path.join(results_dir, filename)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            if "test_auroc" in data:
                baselines[client_id] = data["test_auroc"]
    return baselines
