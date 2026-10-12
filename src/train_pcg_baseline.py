"""
Solo Baseline Trainer — Hospital A (PCG / CirCor DigiScope)
============================================================
Trains PCGNet on mel-spectrogram data.
Saves: best checkpoint, training curve figure, final metrics JSON.

Usage (from project root):
    python -m src.train_pcg_baseline
    python -m src.train_pcg_baseline --epochs 50 --lr 1e-3 --batch_size 64
"""

import os
import json
import argparse
import time
import torch
import torch.nn as nn
import torch.optim as optim

from src.datasets import PCGDataset, make_loaders
from src.models.pcg_model import get_pcg_model
from src.utils.train_utils import train_one_epoch, evaluate, EarlyStopping, plot_training_curve

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULTS = dict(
    data_dir    = "outputs/processed/pcg",
    ckpt_dir    = "outputs/checkpoints",
    fig_dir     = "outputs/figures",
    results_dir = "outputs/results",
    epochs      = 60,
    lr          = 1e-3,
    batch_size  = 64,
    weight_decay= 1e-4,
    patience    = 12,
    dropout     = 0.3,
    embed_dim   = 128,
    num_workers = 0,
    seed        = 42,
)


def parse_args():
    p = argparse.ArgumentParser(description="Train PCG solo baseline (Hospital A)")
    for k, v in DEFAULTS.items():
        p.add_argument(f"--{k}", type=type(v), default=v)
    return p.parse_args()


def main():
    cfg = parse_args()
    torch.manual_seed(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"  Hospital A — PCG Solo Baseline")
    print(f"  Device: {device}")
    print(f"{'='*60}")

    # ── Data ────────────────────────────────────────────────────────────────
    print("\n[1/4] Loading PCG dataset ...")
    ds = PCGDataset(cfg.data_dir)
    print(f"  Total segments: {len(ds)}")
    train_loader, val_loader, test_loader = make_loaders(
        ds, batch_size=cfg.batch_size, num_workers=cfg.num_workers, seed=cfg.seed
    )
    print(f"  Train: {len(train_loader.dataset)}  |  Val: {len(val_loader.dataset)}  |  Test: {len(test_loader.dataset)}")

    # ── Model ────────────────────────────────────────────────────────────────
    print("\n[2/4] Building model ...")
    model = get_pcg_model(embed_dim=cfg.embed_dim, dropout=cfg.dropout).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  PCGNet  |  Parameters: {n_params:,}")

    # Class-weighted loss to handle imbalance (additional safeguard alongside sampler)
    labels_all = [ds[i][1].item() for i in range(len(ds))]
    n_neg = labels_all.count(0)
    n_pos = labels_all.count(1)
    pos_weight = torch.tensor([n_neg / n_pos], device=device)
    # CrossEntropyLoss with class weighting
    weights = torch.tensor([1.0, float(pos_weight.item())], device=device)
    criterion = nn.CrossEntropyLoss(weight=weights)

    optimizer = optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=5)

    os.makedirs(cfg.ckpt_dir, exist_ok=True)
    ckpt_path = os.path.join(cfg.ckpt_dir, "pcg_best.pt")
    early_stop = EarlyStopping(patience=cfg.patience, ckpt_path=ckpt_path)

    # AMP scaler (only active if CUDA available)
    scaler = torch.cuda.amp.GradScaler() if device.type == "cuda" else None

    # ── Training loop ────────────────────────────────────────────────────────
    print(f"\n[3/4] Training for up to {cfg.epochs} epochs ...")
    history = {"train_loss": [], "val_loss": [], "val_auroc": []}
    t0 = time.time()

    for epoch in range(1, cfg.epochs + 1):
        tr = train_one_epoch(model, train_loader, optimizer, criterion, device, scaler)
        va = evaluate(model, val_loader, criterion, device)

        history["train_loss"].append(tr["loss"])
        history["val_loss"].append(va["loss"])
        history["val_auroc"].append(va["auroc"])

        scheduler.step(va["auroc"])

        # Log every 5 epochs
        if epoch % 5 == 0 or epoch == 1:
            elapsed = time.time() - t0
            print(
                f"  Epoch {epoch:03d}/{cfg.epochs} | "
                f"Train loss: {tr['loss']:.4f} acc: {tr['acc']:.3f} | "
                f"Val loss: {va['loss']:.4f} AUROC: {va['auroc']:.4f} "
                f"Sens: {va['sensitivity']:.3f} Spec: {va['specificity']:.3f} "
                f"| {elapsed:.0f}s"
            )

        if early_stop.step(va["auroc"], model):
            print(f"  Early stopping at epoch {epoch} (best val AUROC: {early_stop.best_score:.4f})")
            break

    # ── Final evaluation ─────────────────────────────────────────────────────
    print("\n[4/4] Evaluating on test set ...")
    model.load_state_dict(torch.load(ckpt_path, weights_only=True))
    test_metrics = evaluate(model, test_loader, criterion, device)

    print(f"\n  == Hospital A -- PCG Baseline Test Results ==")
    print(f"  |  AUROC:       {test_metrics['auroc']:.4f}")
    print(f"  |  Sensitivity: {test_metrics['sensitivity']:.4f}")
    print(f"  |  Specificity: {test_metrics['specificity']:.4f}")
    print(f"  |  Accuracy:    {test_metrics['acc']:.4f}")
    print(f"  {'='*46}")

    # Save metrics
    os.makedirs(cfg.results_dir, exist_ok=True)
    out = {
        "hospital": "A",
        "modality": "PCG",
        "dataset": "CirCor_DigiScope",
        "model": "PCGNet",
        "n_train": len(train_loader.dataset),
        "n_val":   len(val_loader.dataset),
        "n_test":  len(test_loader.dataset),
        **{f"test_{k}": v for k, v in test_metrics.items()},
        "best_val_auroc": early_stop.best_score,
        "epochs_trained": len(history["train_loss"]),
    }
    results_path = os.path.join(cfg.results_dir, "pcg_baseline.json")
    with open(results_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Results saved -> {results_path}")

    # Save training curve
    os.makedirs(cfg.fig_dir, exist_ok=True)
    plot_training_curve(
        history,
        title="Hospital A — PCG Baseline",
        save_path=os.path.join(cfg.fig_dir, "pcg_baseline_curve.png"),
    )

    print("\n[DONE] PCG baseline training complete.")
    return out


if __name__ == "__main__":
    main()
