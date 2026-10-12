"""
Solo Baseline Trainer — Hospital C (Echo / EchoNet-Pediatric)
==============================================================
Trains EchoNet (ResNet-18, 2-channel) on ED+ES frame pairs.
Saves: best checkpoint, training curve figure, final metrics JSON.

Usage (from project root):
    python -m src.train_echo_baseline
    python -m src.train_echo_baseline --epochs 50 --lr 1e-3
"""

import os
import json
import argparse
import time
import torch
import torch.nn as nn
import torch.optim as optim

from src.datasets import EchoDataset, make_loaders
from src.models.echo_model import get_echo_model
from src.utils.train_utils import train_one_epoch, evaluate, EarlyStopping, plot_training_curve

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULTS = dict(
    data_dir    = "outputs/processed/echo",
    ckpt_dir    = "outputs/checkpoints",
    fig_dir     = "outputs/figures",
    results_dir = "outputs/results",
    epochs      = 60,
    lr          = 1e-3,
    batch_size  = 32,
    weight_decay= 1e-4,
    patience    = 12,
    dropout     = 0.3,
    embed_dim   = 128,
    num_workers = 0,
    seed        = 42,
)


def parse_args():
    p = argparse.ArgumentParser(description="Train Echo solo baseline (Hospital C)")
    for k, v in DEFAULTS.items():
        p.add_argument(f"--{k}", type=type(v), default=v)
    return p.parse_args()


def main():
    cfg = parse_args()
    torch.manual_seed(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"  Hospital C — Echo Solo Baseline")
    print(f"  Device: {device}")
    print(f"{'='*60}")

    # ── Data ────────────────────────────────────────────────────────────────
    print("\n[1/4] Loading Echo dataset ...")
    ds = EchoDataset(cfg.data_dir)
    print(f"  Total pairs: {len(ds)}")
    train_loader, val_loader, test_loader = make_loaders(
        ds, batch_size=cfg.batch_size, num_workers=cfg.num_workers, seed=cfg.seed
    )
    print(f"  Train: {len(train_loader.dataset)}  |  Val: {len(val_loader.dataset)}  |  Test: {len(test_loader.dataset)}")

    # ── Model ────────────────────────────────────────────────────────────────
    print("\n[2/4] Building model ...")
    model = get_echo_model(embed_dim=cfg.embed_dim, dropout=cfg.dropout).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  EchoNet (ResNet-18 backbone)  |  Parameters: {n_params:,}")

    # Class-weighted loss (EchoNet-Pediatric: ~85% normal / 15% reduced EF)
    labels_all = [ds[i][1].item() for i in range(len(ds))]
    n_neg = labels_all.count(0)
    n_pos = labels_all.count(1)
    pos_weight = n_neg / n_pos
    weights    = torch.tensor([1.0, pos_weight], device=device)
    criterion  = nn.CrossEntropyLoss(weight=weights)

    optimizer = optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=5)

    os.makedirs(cfg.ckpt_dir, exist_ok=True)
    ckpt_path  = os.path.join(cfg.ckpt_dir, "echo_best.pt")
    early_stop = EarlyStopping(patience=cfg.patience, ckpt_path=ckpt_path)

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

    print(f"\n  == Hospital C -- Echo Baseline Test Results ==")
    print(f"  |  AUROC:       {test_metrics['auroc']:.4f}")
    print(f"  |  Sensitivity: {test_metrics['sensitivity']:.4f}")
    print(f"  |  Specificity: {test_metrics['specificity']:.4f}")
    print(f"  |  Accuracy:    {test_metrics['acc']:.4f}")
    print(f"  {'='*46}")

    # Save metrics
    os.makedirs(cfg.results_dir, exist_ok=True)
    out = {
        "hospital": "C",
        "modality": "Echo",
        "dataset": "EchoNet-Pediatric",
        "model": "EchoNet (ResNet-18)",
        "n_train": len(train_loader.dataset),
        "n_val":   len(val_loader.dataset),
        "n_test":  len(test_loader.dataset),
        **{f"test_{k}": v for k, v in test_metrics.items()},
        "best_val_auroc": early_stop.best_score,
        "epochs_trained": len(history["train_loss"]),
    }
    results_path = os.path.join(cfg.results_dir, "echo_baseline.json")
    with open(results_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Results saved -> {results_path}")

    os.makedirs(cfg.fig_dir, exist_ok=True)
    plot_training_curve(
        history,
        title="Hospital C -- Echo Baseline",
        save_path=os.path.join(cfg.fig_dir, "echo_baseline_curve.png"),
    )

    print("\n[DONE] Echo baseline training complete.")
    return out


if __name__ == "__main__":
    main()
