"""
FedProto Pipeline Orchestrator — End-to-end cross-modal federated learning.
=============================================================================
Runs the complete federated prototype learning pipeline across heterogeneous
modality clients (PCG, ECG, Echo).

Pipeline:
    Round 0:  Local warmup (CE only, no prototypes)
    Rounds 1–N: Full federated training (CE + Proto + Contrastive)
    Each round: local training → compute prototypes → server aggregates →
                broadcast → evaluate → check convergence

Features:
    - Early stopping on average val AUROC across clients
    - Convergence detection (prototype distance plateau)
    - Comprehensive visualization (AUROC, loss, t-SNE, convergence, dashboard)
    - Smoke test mode for quick validation
    - Selective client inclusion (--clients pcg,echo)

v3 changes:
    - Per-client lambda configuration (lower contrastive weight for Echo)
    - Adaptive lambda decay over rounds (prevents contrastive loss domination)
    - sqrt-weighted server aggregation (fairer for small-data clients)
    - Class-balanced prototype/contrastive losses
    - Lightweight Echo model (~422K params instead of 11.2M)

Usage:
    python -m src.run_federation
    python -m src.run_federation --rounds 30 --local_epochs 5
    python -m src.run_federation --smoke_test
    python -m src.run_federation --clients pcg,echo --rounds 10

References:
    FedProto (Tan et al., AAAI 2022), MFCPL (Le et al., 2024),
    FedCMD (2025), FedTGP (Zhang et al., AAAI 2024)
"""

import os
import sys
import json
import time
import argparse
import logging
from collections import defaultdict

import torch
import numpy as np

from src.datasets import PCGDataset, ECGDataset, EchoDataset, make_loaders
from src.models.pcg_model import get_pcg_model
from src.models.ecg_model import get_ecg_model
from src.models.echo_model import get_echo_model

from src.federation.client import FederatedClient
from src.federation.server import FederatedServer
from src.federation.federation_utils import (
    plot_auroc_curves,
    plot_loss_breakdown,
    plot_prototype_convergence,
    plot_tsne_embeddings,
    plot_sensitivity_specificity,
    plot_federation_dashboard,
    save_federation_results,
    load_baseline_aurocs,
)


# ── Defaults ──────────────────────────────────────────────────────────────────

# Per-client lambda overrides: lower contrastive weight for data-scarce clients
# Echo (3K samples, 85/15 imbalance) gets much lower contrastive weight
# PCG (11K samples, balanced) gets slightly lower contrastive weight
CLIENT_LAMBDA_OVERRIDES = {
    "echo": {"lambda_proto": 0.3, "lambda_contrast": 0.05},
    "pcg":  {"lambda_proto": 0.5, "lambda_contrast": 0.1},
    "ecg":  {},  # uses defaults
}


DEFAULTS = dict(
    # Federation
    rounds          = 30,
    local_epochs    = 5,
    warmup_epochs   = 5,
    proj_dim        = 64,
    lambda_proto    = 0.5,
    lambda_contrast = 0.15,
    temperature     = 0.5,
    lambda_decay    = 0.03,   # linear decay per round: scale = max(0.3, 1 - decay*round)
    server_weighting= "sqrt", # 'count', 'sqrt', or 'equal'

    # Training
    lr              = 1e-3,
    weight_decay    = 1e-4,
    batch_size      = 32,
    embed_dim       = 128,
    dropout         = 0.3,
    num_workers     = 0,

    # Early stopping
    patience        = 8,
    min_delta       = 1e-4,

    # Paths
    output_dir      = "outputs/federation_v3",
    pcg_data_dir    = "outputs/processed/pcg",
    ecg_data_dir    = "outputs/processed/ecg",
    echo_data_dir   = "outputs/processed/echo",
    baseline_dir    = "outputs/results",

    # Misc
    seed            = 42,
    clients         = "pcg,ecg,echo",
    smoke_test      = False,
)


def parse_args():
    p = argparse.ArgumentParser(
        description="FedProto — Cross-modal federated prototype learning"
    )
    for k, v in DEFAULTS.items():
        if isinstance(v, bool):
            p.add_argument(f"--{k}", action="store_true", default=v)
        else:
            p.add_argument(f"--{k}", type=type(v), default=v)
    return p.parse_args()


def setup_logging(output_dir: str) -> logging.Logger:
    """Set up file + console logging."""
    log_dir = os.path.join(output_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("federation")
    logger.setLevel(logging.INFO)

    # File handler (UTF-8 for Unicode support)
    fh = logging.FileHandler(os.path.join(log_dir, "federation_log.txt"), mode="w", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S"))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def create_client(
    client_id: str,
    cfg,
    device: torch.device,
    logger: logging.Logger,
) -> FederatedClient:
    """Factory function to create a federated client by modality."""
    smoke = cfg.smoke_test

    if client_id == "pcg":
        ds = PCGDataset(cfg.pcg_data_dir)
        model = get_pcg_model(embed_dim=cfg.embed_dim, dropout=cfg.dropout)
        logger.info(f"  PCG: {len(ds)} samples")
    elif client_id == "ecg":
        ds = ECGDataset(cfg.ecg_data_dir)
        model = get_ecg_model(in_channels=9, embed_dim=cfg.embed_dim, dropout=cfg.dropout)
        logger.info(f"  ECG: {len(ds)} samples")
    elif client_id == "echo":
        ds = EchoDataset(cfg.echo_data_dir)
        model = get_echo_model(embed_dim=cfg.embed_dim, dropout=0.5) # Increased dropout
        logger.info(f"  Echo: {len(ds)} samples")
    else:
        raise ValueError(f"Unknown client: {client_id}")

    # In smoke test mode, use a tiny subset
    if smoke:
        from torch.utils.data import Subset
        n = min(100, len(ds))
        ds = Subset(ds, list(range(n)))
        logger.info(f"  [SMOKE TEST] Subset to {n} samples")

    batch_size = cfg.batch_size
    train_loader, val_loader, test_loader = make_loaders(
        ds, batch_size=batch_size, num_workers=cfg.num_workers, seed=cfg.seed
    )

    n_params = sum(p.numel() for p in model.parameters())
    logger.info(f"  Model params: {n_params:,}")

    # Apply per-client lambda overrides
    overrides = CLIENT_LAMBDA_OVERRIDES.get(client_id, {})
    lp = overrides.get("lambda_proto", cfg.lambda_proto)
    lc = overrides.get("lambda_contrast", cfg.lambda_contrast)
    if overrides:
        logger.info(f"  λ_proto={lp:.3f}  λ_contrast={lc:.3f}  (per-client override)")
    else:
        logger.info(f"  λ_proto={lp:.3f}  λ_contrast={lc:.3f}  (default)")

    client = FederatedClient(
        client_id=client_id,
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        device=device,
        embed_dim=cfg.embed_dim,
        proj_dim=cfg.proj_dim,
        lr=cfg.lr,
        weight_decay=cfg.weight_decay,
        lambda_proto=lp,
        lambda_contrast=lc,
        temperature=cfg.temperature,
        total_rounds=cfg.rounds,
    )
    return client


# ── Early Stopping for Federation ────────────────────────────────────────────

class FederationEarlyStopping:
    """
    Improved early stopper for federation.

    Uses a rolling median of the last `smooth_window` rounds per client before
    averaging. This prevents a single unstable client (e.g., Echo's ±0.03 AUROC
    swings) from triggering premature stopping when PCG and ECG are still
    improving.

    Stopping criterion: smoothed average AUROC has not improved by `min_delta`
    for `patience` consecutive rounds.
    """

    def __init__(self, patience: int = 12, min_delta: float = 5e-4,
                 smooth_window: int = 3):
        self.patience = patience
        self.min_delta = min_delta
        self.smooth_window = smooth_window
        self.best_score = -float("inf")
        self.counter = 0
        self.best_round = 0
        self._client_history: dict[str, list[float]] = {}

    def step(self, per_client_auroc: dict[str, float], round_num: int) -> bool:
        """
        Args:
            per_client_auroc: {client_id: val_auroc_this_round}
            round_num:        current federation round number
        Returns True if training should stop.
        """
        # Accumulate per-client history
        for cid, auroc in per_client_auroc.items():
            self._client_history.setdefault(cid, []).append(auroc)

        # Rolling median per client (dampens Echo's oscillation)
        smoothed_values = []
        for cid, hist in self._client_history.items():
            window = hist[-self.smooth_window:]
            smoothed_values.append(float(np.median(window)))

        avg_smoothed = sum(smoothed_values) / len(smoothed_values)

        if avg_smoothed > self.best_score + self.min_delta:
            self.best_score = avg_smoothed
            self.counter = 0
            self.best_round = round_num
            return False
        else:
            self.counter += 1
            return self.counter >= self.patience


# ── Main Pipeline ────────────────────────────────────────────────────────────

def main():
    cfg = parse_args()

    # Override for smoke test
    if cfg.smoke_test:
        cfg.rounds = 3
        cfg.local_epochs = 1
        cfg.warmup_epochs = 1
        cfg.patience = 100  # don't early stop in smoke test

    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Setup
    os.makedirs(cfg.output_dir, exist_ok=True)
    logger = setup_logging(cfg.output_dir)

    logger.info("=" * 70)
    logger.info("  FedProto — Cross-Modal Federated Prototype Learning")
    logger.info("=" * 70)
    logger.info(f"  Device:          {device}")
    if device.type == "cuda":
        logger.info(f"  GPU:             {torch.cuda.get_device_name(0)}")
        logger.info(f"  VRAM:            {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    logger.info(f"  Rounds:          {cfg.rounds}")
    logger.info(f"  Local epochs:    {cfg.local_epochs}")
    logger.info(f"  Warmup epochs:   {cfg.warmup_epochs}")
    logger.info(f"  Projection dim:  {cfg.proj_dim}")
    logger.info(f"  lambda_proto:    {cfg.lambda_proto}")
    logger.info(f"  lambda_contrast: {cfg.lambda_contrast}")
    logger.info(f"  Temperature:     {cfg.temperature}")
    logger.info(f"  Clients:         {cfg.clients}")
    logger.info(f"  Lambda decay:    {cfg.lambda_decay} per round")
    logger.info(f"  Server weight:   {cfg.server_weighting}")
    if cfg.smoke_test:
        logger.info("  [!] SMOKE TEST MODE -- tiny data, few rounds")
    logger.info("")

    # -- 1. Initialize Clients -------------------------------------------------
    client_ids = [c.strip() for c in cfg.clients.split(",")]
    logger.info(f"[1/{5 + cfg.rounds}] Initializing {len(client_ids)} clients ...")

    clients = {}
    for cid in client_ids:
        logger.info(f"\n  Creating client: {cid.upper()}")
        clients[cid] = create_client(cid, cfg, device, logger)

    # -- 2. Initialize Server --------------------------------------------------
    server = FederatedServer(num_classes=2, proj_dim=cfg.proj_dim, weighting=cfg.server_weighting)

    # Load baseline AUROCs for comparison (if available)
    baseline_aurocs = load_baseline_aurocs(cfg.baseline_dir)
    if baseline_aurocs:
        logger.info(f"\n  Solo baselines found: {baseline_aurocs}")

    # -- 3. Tracking -----------------------------------------------------------
    round_metrics = {cid: [] for cid in client_ids}       # per-client eval per round
    round_losses = {cid: [] for cid in client_ids}        # per-client loss per round
    early_stop = FederationEarlyStopping(
        patience=cfg.patience, min_delta=cfg.min_delta, smooth_window=3
    )

    ckpt_dir = os.path.join(cfg.output_dir, "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)

    t0 = time.time()

    # -- 4. Round 0: Warmup (CE only) -----------------------------------------
    logger.info(f"\n{'-'*70}")
    logger.info(f"  ROUND 0 -- Local Warmup ({cfg.warmup_epochs} epochs, CE only)")
    logger.info(f"{'-'*70}")

    for cid, client in clients.items():
        logger.info(f"\n  [{cid.upper()}] Training {cfg.warmup_epochs} warmup epochs ...")
        loss_info = client.local_train(
            num_epochs=cfg.warmup_epochs,
            global_prototypes=None,  # CE only — no federated loss yet
        )

        # Evaluate
        val_metrics = client.evaluate(client.val_loader)
        logger.info(
            f"  [{cid.upper()}] Warmup done | "
            f"Val AUROC: {val_metrics['auroc']:.4f}  "
            f"Sens: {val_metrics['sensitivity']:.3f}  "
            f"Spec: {val_metrics['specificity']:.3f}"
        )

        round_metrics[cid].append({"round": 0, **val_metrics})
        round_losses[cid].append({
            "ce": loss_info["ce_losses"][-1],
            "proto": 0.0,
            "contrast": 0.0,
        })

    # Compute initial prototypes
    logger.info("\n  Computing initial prototypes ...")
    all_protos = {}
    all_counts = {}
    for cid, client in clients.items():
        protos, counts = client.compute_prototypes()
        all_protos[cid] = protos
        all_counts[cid] = counts
        logger.info(f"  [{cid.upper()}] Prototypes: " +
                    ", ".join(f"class {c}: {n} samples" for c, n in counts.items()))

    # Server aggregation
    global_prototypes = server.aggregate_prototypes(all_protos, all_counts)
    logger.info(f"\n  Global prototypes initialized.")
    logger.info(server.get_alignment_summary(0))

    # -- 5. Federated Rounds 1-N -----------------------------------------------
    for round_num in range(1, cfg.rounds + 1):
        elapsed = time.time() - t0
        logger.info(f"\n{'-'*70}")
        logger.info(f"  ROUND {round_num}/{cfg.rounds}  ({elapsed:.0f}s elapsed)")
        logger.info(f"{'-'*70}")

        # ── Lambda decay schedule: gradually reduce federated loss influence ──
        lambda_scale = max(0.3, 1.0 - cfg.lambda_decay * round_num)
        if round_num == 1 or round_num % 5 == 0:
            logger.info(f"  λ_scale = {lambda_scale:.3f}")

        # ── Local training with federated loss ──
        for cid, client in clients.items():
            loss_info = client.local_train(
                num_epochs=cfg.local_epochs,
                global_prototypes=global_prototypes,
                lambda_scale=lambda_scale,
            )

            # Record last-epoch losses
            round_losses[cid].append({
                "ce": loss_info["ce_losses"][-1],
                "proto": loss_info["proto_losses"][-1],
                "contrast": loss_info["contrast_losses"][-1],
            })

        # ── Compute prototypes ──
        all_protos = {}
        all_counts = {}
        for cid, client in clients.items():
            protos, counts = client.compute_prototypes()
            all_protos[cid] = protos
            all_counts[cid] = counts

        # ── Server aggregation ──
        global_prototypes = server.aggregate_prototypes(all_protos, all_counts)

        # ── Evaluate all clients ──
        avg_auroc = 0.0
        per_client_auroc = {}
        for cid, client in clients.items():
            val_metrics = client.evaluate(client.val_loader)
            round_metrics[cid].append({"round": round_num, **val_metrics})
            avg_auroc += val_metrics["auroc"]
            per_client_auroc[cid] = val_metrics["auroc"]

            logger.info(
                f"  [{cid.upper()}] "
                f"AUROC: {val_metrics['auroc']:.4f}  "
                f"Sens: {val_metrics['sensitivity']:.3f}  "
                f"Spec: {val_metrics['specificity']:.3f}  "
                f"Loss CE: {round_losses[cid][-1]['ce']:.4f}  "
                f"Proto: {round_losses[cid][-1]['proto']:.4f}  "
                f"Contr: {round_losses[cid][-1]['contrast']:.4f}"
            )

            # Balanced accuracy = (sensitivity + specificity) / 2
            bal_acc = (
                val_metrics["sensitivity"] + val_metrics["specificity"]
            ) / 2 if not (np.isnan(val_metrics["sensitivity"]) or np.isnan(val_metrics["specificity"])) else -1.0

            # Checkpoint A: Best AUROC (for ranking and comparison)
            if val_metrics["auroc"] > client.best_val_auroc:
                client.best_val_auroc = val_metrics["auroc"]
                client.best_state = {
                    "model": {k: v.cpu().clone() for k, v in client.model.state_dict().items()},
                    "proj_head": {k: v.cpu().clone() for k, v in client.proj_head.state_dict().items()},
                }
                ckpt_path = os.path.join(ckpt_dir, f"{cid}_federated_best.pt")
                client.save_checkpoint(ckpt_path)

            # Checkpoint B: Best balanced accuracy (sensitivity-aware)
            if bal_acc > getattr(client, "best_bal_acc", -1.0):
                client.best_bal_acc = bal_acc
                ckpt_path_bal = os.path.join(ckpt_dir, f"{cid}_federated_balanced.pt")
                client.save_checkpoint(ckpt_path_bal)

        avg_auroc /= len(clients)

        # Alignment summary
        logger.info(f"\n  Alignment Quality:")
        logger.info(server.get_alignment_summary(round_num))
        logger.info(f"  Average Val AUROC (raw): {avg_auroc:.4f}")

        # ── Convergence check ──
        if server.check_convergence(window=5, threshold=0.01):
            logger.info(f"\n  [OK] Prototypes converged! (shift < 0.01 for 5 rounds)")

        # ── Early stopping (smoothed per-client AUROC) ──
        if early_stop.step(per_client_auroc, round_num):
            logger.info(
                f"\n  [STOP] Early stopping at round {round_num} "
                f"(best smoothed avg AUROC: {early_stop.best_score:.4f} at round {early_stop.best_round})"
            )
            break

        # ── LR scheduler step (cosine — no metric argument needed) ──
        for cid, client in clients.items():
            client.scheduler.step()

    # ── 6. Final Test Evaluation ─────────────────────────────────────────────
    total_time = time.time() - t0
    logger.info(f"\n{'='*70}")
    logger.info(f"  FINAL TEST EVALUATION")
    logger.info(f"{'='*70}")

    test_results = {}
    for cid, client in clients.items():
        # Load best checkpoint (AUROC-based)
        ckpt_path = os.path.join(ckpt_dir, f"{cid}_federated_best.pt")
        if os.path.exists(ckpt_path):
            client.load_checkpoint(ckpt_path)

        # Use optimal Youden's J threshold at test time to correct
        # calibration shift from class-weighted training
        test_metrics = client.evaluate(client.test_loader, optimal_threshold=True)
        test_results[cid] = test_metrics

        logger.info(f"\n  == {cid.upper()} -- Federated Test Results ==")
        logger.info(f"  |  AUROC:       {test_metrics['auroc']:.4f}")
        logger.info(f"  |  Sensitivity: {test_metrics['sensitivity']:.4f}")
        logger.info(f"  |  Specificity: {test_metrics['specificity']:.4f}")
        logger.info(f"  |  Accuracy:    {test_metrics['acc']:.4f}")
        if cid in baseline_aurocs:
            diff = test_metrics["auroc"] - baseline_aurocs[cid]
            symbol = "[+]" if diff > 0 else "[-]"
            logger.info(f"  |  vs Solo:     {symbol} {abs(diff):.4f}")
        logger.info(f"  {'='*44}")

    # ── 7. Comparison Table ──────────────────────────────────────────────────
    if baseline_aurocs:
        logger.info(f"\n  {'-'*60}")
        logger.info(f"  {'Client':<10} {'Solo AUROC':<14} {'Fed AUROC':<14} {'Delta':<10} {'Verdict'}")
        logger.info(f"  {'-'*60}")
        for cid in client_ids:
            if cid in baseline_aurocs and cid in test_results:
                solo = baseline_aurocs[cid]
                fed = test_results[cid]["auroc"]
                diff = fed - solo
                verdict = "[+] IMPROVED" if diff > 0.005 else ("[=] SAME" if abs(diff) <= 0.005 else "[-] REGRESSED")
                logger.info(f"  {cid.upper():<10} {solo:<14.4f} {fed:<14.4f} {diff:+.4f}    {verdict}")
        logger.info(f"  {'-'*60}")

    # ── 8. Generate Visualizations ────────────────────────────────────────────
    logger.info(f"\n[Generating visualizations ...]")
    fig_dir = os.path.join(cfg.output_dir, "figures")

    # AUROC curves
    plot_auroc_curves(
        round_metrics, os.path.join(fig_dir, "federation_auroc_curves.png"),
        baseline_aurocs=baseline_aurocs,
    )

    # Loss breakdown
    plot_loss_breakdown(
        round_losses, os.path.join(fig_dir, "federation_loss_breakdown.png"),
    )

    # Prototype convergence
    plot_prototype_convergence(
        server.history, os.path.join(fig_dir, "prototype_convergence.png"),
    )

    # Sensitivity / Specificity
    plot_sensitivity_specificity(
        round_metrics, os.path.join(fig_dir, "federation_sens_spec.png"),
    )

    # t-SNE of final projected embeddings
    logger.info("  Computing t-SNE embeddings ...")
    client_embeddings = {}
    for cid, client in clients.items():
        embeds, labels = client.get_all_projected_embeddings()
        client_embeddings[cid] = (embeds, labels)
    plot_tsne_embeddings(
        client_embeddings, os.path.join(fig_dir, "embedding_tsne.png"),
    )

    # Dashboard
    plot_federation_dashboard(
        round_metrics, server.history, round_losses,
        os.path.join(fig_dir, "federation_dashboard.png"),
        baseline_aurocs=baseline_aurocs,
    )

    # ── 9. Save Results ──────────────────────────────────────────────────────
    results = {
        "config": {k: v for k, v in vars(cfg).items()},
        "total_time_seconds": total_time,
        "total_rounds": round_num if 'round_num' in dir() else 0,
        "best_avg_auroc": early_stop.best_score,
        "best_round": early_stop.best_round,
        "test_results": test_results,
        "baseline_aurocs": baseline_aurocs,
        "per_round_metrics": round_metrics,
        "per_round_losses": round_losses,
        "server_history": {
            "proto_shift": server.history["proto_shift"],
            "global_proto_norms": server.history["global_proto_norms"],
        },
        "convergence_detected": server.check_convergence(),
    }
    save_federation_results(
        results, os.path.join(cfg.output_dir, "results", "federation_results.json")
    )

    # ── Done ──────────────────────────────────────────────────────────────────
    logger.info(f"\n{'='*70}")
    logger.info(f"  [DONE] FEDERATION COMPLETE")
    logger.info(f"  Total time:        {total_time:.0f}s ({total_time/60:.1f} min)")
    logger.info(f"  Best avg AUROC:    {early_stop.best_score:.4f} (round {early_stop.best_round})")
    logger.info(f"  Converged:         {'Yes' if server.check_convergence() else 'No'}")
    logger.info(f"  Output dir:        {cfg.output_dir}")
    logger.info(f"{'='*70}")

    return results


if __name__ == "__main__":
    main()
