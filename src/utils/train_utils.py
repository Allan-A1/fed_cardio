"""
Shared training utilities — used by all three solo baseline trainers.

Provides:
    - train_one_epoch()
    - evaluate()          → returns loss, accuracy, AUROC, sensitivity, specificity
    - EarlyStopping       → stops training when val_auroc stops improving
    - plot_training_curve()
"""

import os
import time
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt


# ── Epoch helpers ─────────────────────────────────────────────────────────────

def train_one_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    scaler: torch.cuda.amp.GradScaler | None = None,
) -> dict:
    """Run one training epoch. Returns dict with loss and accuracy."""
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    for X, y in loader:
        X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
        optimizer.zero_grad()

        if scaler is not None:
            with torch.autocast(device_type=device.type):
                logits = model(X)
                loss   = criterion(logits, y)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(X)
            loss   = criterion(logits, y)
            loss.backward()
            optimizer.step()

        total_loss += loss.item() * len(y)
        preds = logits.argmax(dim=1)
        correct += (preds == y).sum().item()
        total   += len(y)

    return {
        "loss": total_loss / total,
        "acc":  correct / total,
    }


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> dict:
    """
    Evaluate model on a DataLoader.
    Returns: loss, acc, auroc, sensitivity, specificity.
    """
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_probs, all_labels = [], []

    for X, y in loader:
        X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
        logits = model(X)
        loss   = criterion(logits, y)

        total_loss += loss.item() * len(y)
        probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
        preds = logits.argmax(dim=1)
        correct += (preds == y).sum().item()
        total   += len(y)

        all_probs.extend(probs.tolist())
        all_labels.extend(y.cpu().numpy().tolist())

    all_probs  = np.array(all_probs)
    all_labels = np.array(all_labels)

    # AUROC
    try:
        auroc = roc_auc_score(all_labels, all_probs)
    except ValueError:
        auroc = float("nan")

    # Sensitivity / Specificity at 0.5 threshold
    preds_bin = (all_probs >= 0.5).astype(int)
    if len(np.unique(all_labels)) == 2:
        tn, fp, fn, tp = confusion_matrix(all_labels, preds_bin).ravel()
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
        specificity = tn / (tn + fp) if (tn + fp) > 0 else float("nan")
    else:
        sensitivity = specificity = float("nan")

    return {
        "loss":        total_loss / total,
        "acc":         correct / total,
        "auroc":       auroc,
        "sensitivity": sensitivity,
        "specificity": specificity,
    }


# ── Early stopping ────────────────────────────────────────────────────────────

class EarlyStopping:
    """
    Stop training when validation AUROC hasn't improved for `patience` epochs.
    Saves the best model checkpoint automatically.
    """

    def __init__(self, patience: int = 10, ckpt_path: str = "best_model.pt", min_delta: float = 1e-4):
        self.patience   = patience
        self.ckpt_path  = ckpt_path
        self.min_delta  = min_delta
        self.best_score = -float("inf")
        self.counter    = 0
        self.stopped    = False

    def step(self, score: float, model: nn.Module) -> bool:
        """Returns True if training should stop."""
        if score > self.best_score + self.min_delta:
            self.best_score = score
            self.counter    = 0
            torch.save(model.state_dict(), self.ckpt_path)
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.stopped = True
        return self.stopped


# ── Plotting ──────────────────────────────────────────────────────────────────

def plot_training_curve(
    history: dict,
    title: str,
    save_path: str,
) -> None:
    """
    Save a 2-panel figure: (left) loss curves, (right) AUROC curves.
    history keys: train_loss, val_loss, train_acc, val_auroc
    """
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Loss
    axes[0].plot(epochs, history["train_loss"], label="Train loss", color="#4C72B0")
    axes[0].plot(epochs, history["val_loss"],   label="Val loss",   color="#DD8452")
    axes[0].set_title(f"{title} — Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Cross-entropy loss")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # AUROC
    axes[1].plot(epochs, history["val_auroc"], label="Val AUROC", color="#55A868", linewidth=2)
    axes[1].set_ylim(0.4, 1.02)
    axes[1].set_title(f"{title} — Val AUROC")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("AUROC")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    axes[1].axhline(0.5, color="gray", linestyle="--", alpha=0.4, label="Chance")

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [Plot] Saved -> {save_path}")
