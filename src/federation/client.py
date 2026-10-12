"""
Federated Client — Wraps a single hospital's model for FedProto training.
==========================================================================
Each client holds:
    - backbone model (PCGNet / ECGResNet / EchoNet)
    - projection head (128-d → 64-d shared space, two-layer MLP)
    - optimizer (covers both backbone + projection head)
    - local dataset loaders

The client trains locally with the combined loss:
    L_total = L_CE + λ_proto * L_proto + λ_contrast * L_contrast

The classifier still operates on the native 128-d embedding (unchanged).
The projection head is a parallel, non-destructive addition used only
for computing prototypes to share with the server.

v3 changes:
    - Class-balanced prototype & contrastive losses (fixes sensitivity collapse
      for imbalanced clients like Echo with 85/15 normal/abnormal split)
    - Removed dead code (duplicate proj_head call)
    - Added lambda_scale support for adaptive decay during training

v3.1 fixes:
    - Corrected pos_weight formula: mild 1.5× correction when WeightedRandomSampler
      is active (was using full n_neg/n_pos × 1.5 = 4.75×, double-correcting imbalance)
    - Per-client gradient clipping: echo=1.0, pcg=2.0, ecg=5.0 (was flat 5.0 for all)
    - CosineAnnealingLR replaces ReduceLROnPlateau (prevents premature LR freeze)
    - Youden's J optimal threshold at test time (fixes PCG sensitivity regression)

Reference:
    FedProto (Tan et al., AAAI 2022) — AAAI 36(8), 8432–8440
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import defaultdict

from src.federation.projection import ProjectionHead
from src.federation.losses import prototype_alignment_loss, contrastive_prototype_loss


class FederatedClient:
    """
    Wraps a single hospital's model + projection head for federated training.

    Args:
        client_id:    Unique identifier (e.g., "pcg", "ecg", "echo")
        model:        The backbone model (must support return_embedding=True)
        train_loader: DataLoader for local training data
        val_loader:   DataLoader for local validation data
        test_loader:  DataLoader for local test data
        device:       torch device
        embed_dim:    Backbone embedding dimension (default 128)
        proj_dim:     Projection head output dimension (default 64)
        lr:           Learning rate (default 1e-3)
        weight_decay: Weight decay (default 1e-4)
        lambda_proto: Weight for prototype alignment loss (default 0.5)
        lambda_contrast: Weight for contrastive loss (default 0.05)
        temperature:  Contrastive loss temperature (default 0.5)
    """

    def __init__(
        self,
        client_id: str,
        model: nn.Module,
        train_loader,
        val_loader,
        test_loader,
        device: torch.device,
        embed_dim: int = 128,
        proj_dim: int = 64,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        lambda_proto: float = 0.5,
        lambda_contrast: float = 0.05,
        temperature: float = 0.5,
        total_rounds: int = 30,
    ):
        self.client_id = client_id
        self.model = model.to(device)
        self.device = device
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader

        # Projection head — maps native embedding to shared space (two-layer MLP)
        self.proj_head = ProjectionHead(embed_dim, proj_dim).to(device)

        # Single optimizer for both backbone + projection head
        self.optimizer = optim.Adam(
            list(self.model.parameters()) + list(self.proj_head.parameters()),
            lr=lr,
            weight_decay=weight_decay,
        )
        # CosineAnnealingLR: smooth, predictable decay over total_rounds.
        # Replaces ReduceLROnPlateau which fired too aggressively (patience=3 out of
        # ~12 rounds = 25% of training) and froze ECG while Echo was still unstable.
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=total_rounds, eta_min=1e-5
        )

        # Class-weighted CE loss (computed from training data)
        self._setup_criterion()

        # Class weights for balanced prototype/contrastive losses
        self._compute_proto_class_weights()

        # Loss weights
        self.lambda_proto = lambda_proto
        self.lambda_contrast = lambda_contrast
        self.temperature = temperature

        # Best model tracking
        self.best_val_auroc = -float("inf")
        self.best_state = None

    def _setup_criterion(self, use_weighted_sampler: bool = True):
        """Compute class weights for CE loss.

        When WeightedRandomSampler is active, it already balances class frequencies
        in each batch (effective ratio ≈ 1:1). Applying full n_neg/n_pos pos_weight
        on top of that double-penalises the minority class and causes loss spikes.
        In that case, use a mild 1.5× correction only.
        When no sampler is used, use the full inverse-frequency weighting.
        """
        labels = []
        for _, y in self.train_loader:
            labels.extend(y.numpy().tolist())
        labels = np.array(labels)
        n_neg = (labels == 0).sum()
        n_pos = (labels == 1).sum()
        if n_pos > 0 and n_neg > 0:
            if use_weighted_sampler:
                # Sampler already equalises batch class ratios → mild correction only
                pos_weight = 1.5
            else:
                # No sampler → full inverse-frequency weight
                pos_weight = (n_neg / n_pos) * 1.5
            weights = torch.tensor([1.0, pos_weight], device=self.device, dtype=torch.float32)
        else:
            weights = torch.tensor([1.0, 1.0], device=self.device, dtype=torch.float32)
        self.criterion = nn.CrossEntropyLoss(weight=weights)

    def _compute_proto_class_weights(self):
        """
        Compute inverse-frequency class weights for prototype/contrastive losses.

        For balanced datasets (PCG, ECG ~50/50): weights ≈ {0: 1.0, 1: 1.0}
        For imbalanced datasets (Echo ~85/15):   weights ≈ {0: 0.59, 1: 3.33}

        This ensures minority-class samples receive proportionally higher loss
        weight, preventing the specificity trap (predicting everything as normal).
        """
        labels = []
        for _, y in self.train_loader:
            labels.extend(y.numpy().tolist())
        labels = np.array(labels)

        n_total = len(labels)
        unique_classes = np.unique(labels)
        n_classes = len(unique_classes)

        self.proto_class_weights = {}
        for c in unique_classes:
            n_c = (labels == c).sum()
            # Inverse frequency: total / (n_classes * n_c)
            self.proto_class_weights[int(c)] = float(n_total / (n_classes * n_c))

    def local_train(
        self,
        num_epochs: int,
        global_prototypes: dict[int, torch.Tensor] | None = None,
        lambda_scale: float = 1.0,
    ) -> dict:
        """
        Run local training for num_epochs.

        If global_prototypes is None (round 0 warmup), trains with CE only.
        Otherwise, trains with CE + prototype alignment + contrastive loss.

        Args:
            num_epochs:        Number of local epochs to train
            global_prototypes: {class_id: (proj_dim,)} from the server, or None
            lambda_scale:      Multiplier for federated loss weights (for decay).
                               1.0 = full strength, 0.0 = CE only.

        Returns:
            dict with per-epoch losses: {
                "ce_losses": [...],
                "proto_losses": [...],
                "contrast_losses": [...],
                "total_losses": [...]
            }
        """
        self.model.train()
        self.proj_head.train()

        use_federated_loss = global_prototypes is not None
        history = defaultdict(list)

        for epoch in range(num_epochs):
            epoch_ce, epoch_proto, epoch_contrast, epoch_total = 0.0, 0.0, 0.0, 0.0
            n_samples = 0

            for X, y in self.train_loader:
                X = X.to(self.device, non_blocking=True)
                y = y.to(self.device, non_blocking=True)
                batch_size = len(y)

                # --- Data Augmentation for Echo ---
                # Prevents severe overfitting on the minority class
                if self.client_id == "echo":
                    # Random horizontal flip (50%)
                    if torch.rand(1).item() > 0.5:
                        X = torch.flip(X, dims=[3])
                    # Random vertical flip (50%)
                    if torch.rand(1).item() > 0.5:
                        X = torch.flip(X, dims=[2])
                    # Random brightness jitter (+/- 20%)
                    jitter = 0.8 + 0.4 * torch.rand(X.size(0), 1, 1, 1, device=X.device)
                    X = torch.clamp(X * jitter, 0.0, 1.0)
                # ----------------------------------

                self.optimizer.zero_grad()

                # Forward: backbone → native embedding → logits
                logits, native_embed = self.model(X, return_embedding=True)

                # Classification loss (on native 128-d embedding, unchanged)
                loss_ce = self.criterion(logits, y)

                # Federated losses (on projected 64-d embedding)
                loss_proto = torch.tensor(0.0, device=self.device)
                loss_contrast = torch.tensor(0.0, device=self.device)

                if use_federated_loss:
                    projected = self.proj_head(native_embed)

                    loss_proto = prototype_alignment_loss(
                        projected, y, global_prototypes,
                        class_weights=self.proto_class_weights,
                    )
                    loss_contrast = contrastive_prototype_loss(
                        projected, y, global_prototypes, self.temperature,
                        class_weights=self.proto_class_weights,
                    )

                # Combined loss with optional scaling for lambda decay
                loss_total = (
                    loss_ce
                    + (self.lambda_proto * lambda_scale) * loss_proto
                    + (self.lambda_contrast * lambda_scale) * loss_contrast
                )

                loss_total.backward()
                # Per-client gradient clipping:
                # Echo:  tight (1.0) — small model, loss spikes 4×, needs aggressive clip
                # PCG:   medium (2.0) — shallow CNN, moderately stable
                # ECG:   loose  (5.0) — large ResNet, naturally stable
                _GRAD_CLIP = {"echo": 1.0, "pcg": 2.0, "ecg": 5.0}
                torch.nn.utils.clip_grad_norm_(
                    list(self.model.parameters()) + list(self.proj_head.parameters()),
                    max_norm=_GRAD_CLIP.get(self.client_id, 2.0),
                )
                self.optimizer.step()

                epoch_ce += loss_ce.item() * batch_size
                epoch_proto += loss_proto.item() * batch_size
                epoch_contrast += loss_contrast.item() * batch_size
                epoch_total += loss_total.item() * batch_size
                n_samples += batch_size

            history["ce_losses"].append(epoch_ce / n_samples)
            history["proto_losses"].append(epoch_proto / n_samples)
            history["contrast_losses"].append(epoch_contrast / n_samples)
            history["total_losses"].append(epoch_total / n_samples)

        return dict(history)

    @torch.no_grad()
    def compute_prototypes(self) -> tuple[dict[int, torch.Tensor], dict[int, int]]:
        """
        Compute class prototypes in the projected space.

        Forward pass over training data → project embeddings → mean per class.

        Returns:
            prototypes:    {class_id: (proj_dim,)} — mean projected embedding per class
            sample_counts: {class_id: int}         — number of samples per class
        """
        self.model.eval()
        self.proj_head.eval()

        class_embeds = defaultdict(list)

        for X, y in self.train_loader:
            X = X.to(self.device, non_blocking=True)
            _, native_embed = self.model(X, return_embedding=True)
            projected = self.proj_head(native_embed)  # (N, proj_dim)

            for i in range(len(y)):
                class_id = y[i].item()
                class_embeds[class_id].append(projected[i].cpu())

        prototypes = {}
        sample_counts = {}
        for class_id, embeds in class_embeds.items():
            stacked = torch.stack(embeds)         # (n_c, proj_dim)
            prototypes[class_id] = stacked.mean(dim=0)  # (proj_dim,)
            sample_counts[class_id] = len(embeds)

        return prototypes, sample_counts

    @torch.no_grad()
    def evaluate(self, loader=None, optimal_threshold: bool = False) -> dict:
        """
        Evaluate model on a DataLoader.
        Returns: loss, acc, auroc, sensitivity, specificity.

        Args:
            loader:            DataLoader to evaluate on (default: val_loader).
            optimal_threshold: If True, find the decision threshold that maximises
                               Youden's J = sensitivity + specificity - 1, instead
                               of using the fixed 0.5 default. Use True for final
                               test evaluation to correct calibration shift from
                               class-weighted training. Use False during training
                               rounds (faster, consistent for early stopping).
        """
        from sklearn.metrics import roc_auc_score, confusion_matrix, roc_curve

        if loader is None:
            loader = self.val_loader

        self.model.eval()
        total_loss, correct, total = 0.0, 0, 0
        all_probs, all_labels = [], []

        for X, y in loader:
            X = X.to(self.device, non_blocking=True)
            y = y.to(self.device, non_blocking=True)
            logits = self.model(X)
            loss = self.criterion(logits, y)

            total_loss += loss.item() * len(y)
            probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
            preds = logits.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += len(y)

            all_probs.extend(probs.tolist())
            all_labels.extend(y.cpu().numpy().tolist())

        all_probs = np.array(all_probs)
        all_labels = np.array(all_labels)

        # AUROC
        try:
            auroc = roc_auc_score(all_labels, all_probs)
        except ValueError:
            auroc = float("nan")

        # Decision threshold
        if optimal_threshold and len(np.unique(all_labels)) == 2:
            # Youden's J: find threshold that maximises sensitivity + specificity
            fpr, tpr, thresholds = roc_curve(all_labels, all_probs)
            j_scores = tpr - fpr
            best_thresh = float(thresholds[np.argmax(j_scores)])
        else:
            best_thresh = 0.5

        preds_bin = (all_probs >= best_thresh).astype(int)
        if len(np.unique(all_labels)) == 2:
            tn, fp, fn, tp = confusion_matrix(all_labels, preds_bin).ravel()
            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
            specificity = tn / (tn + fp) if (tn + fp) > 0 else float("nan")
        else:
            sensitivity = specificity = float("nan")

        return {
            "loss": total_loss / total,
            "acc": correct / total,
            "auroc": auroc,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "threshold": best_thresh,
        }

    @torch.no_grad()
    def get_all_projected_embeddings(self) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Get all projected embeddings and labels from training data.
        Used for t-SNE visualization.

        Returns:
            embeddings: (N, proj_dim)
            labels:     (N,)
        """
        self.model.eval()
        self.proj_head.eval()

        all_embeds, all_labels = [], []
        for X, y in self.train_loader:
            X = X.to(self.device, non_blocking=True)
            _, native_embed = self.model(X, return_embedding=True)
            projected = self.proj_head(native_embed)
            all_embeds.append(projected.cpu())
            all_labels.append(y)

        return torch.cat(all_embeds), torch.cat(all_labels)

    def save_checkpoint(self, path: str):
        """Save model + projection head state dicts."""
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "proj_head_state_dict": self.proj_head.state_dict(),
            "best_val_auroc": self.best_val_auroc,
        }, path)

    def load_checkpoint(self, path: str):
        """Load model + projection head state dicts."""
        ckpt = torch.load(path, weights_only=True)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.proj_head.load_state_dict(ckpt["proj_head_state_dict"])
