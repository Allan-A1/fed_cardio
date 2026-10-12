"""
Dataset loaders for all three hospital modalities.
Each loader returns a torch Dataset over pre-processed .pt tensor files.
All three datasets expose a consistent interface:
    __len__, __getitem__ → (tensor, label)
"""

import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import numpy as np
import pandas as pd


# ── Hospital A — PCG ─────────────────────────────────────────────────────────

class PCGDataset(Dataset):
    """
    Mel-spectrogram dataset for Hospital A (CirCor DigiScope).

    Loads:
        spectrograms.pt — (N, n_mels, T)  float32
        labels.pt       — (N,)            long
    """

    def __init__(self, data_dir: str = "outputs/processed/pcg"):
        self.X = torch.load(f"{data_dir}/spectrograms.pt", weights_only=True)  # (N, 64, T)
        self.y = torch.load(f"{data_dir}/labels.pt",       weights_only=True)  # (N,)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


# ── Hospital B — ECG ──────────────────────────────────────────────────────────

class ECGDataset(Dataset):
    """
    ECG signal dataset for Hospital B (ZZU-pECG).

    Loads:
        ecg_signals.pt — (N, 9, 5000)  float32
        labels.pt      — (N,)          long
    Optional index filter for lead-count ablations (Week 3).
    """

    def __init__(
        self,
        data_dir: str = "outputs/processed/ecg",
        index_filter: torch.Tensor | None = None,
    ):
        X_full = torch.load(f"{data_dir}/ecg_signals.pt", weights_only=True)  # (N, 9, 5000)
        y_full = torch.load(f"{data_dir}/labels.pt",      weights_only=True)  # (N,)

        if index_filter is not None:
            self.X = X_full[index_filter]
            self.y = y_full[index_filter]
        else:
            self.X = X_full
            self.y = y_full

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


# ── Hospital C — Echo ─────────────────────────────────────────────────────────

class EchoDataset(Dataset):
    """
    Echo ED/ES frame dataset for Hospital C (EchoNet-Pediatric).

    Loads:
        ed_es_frames.pt — (N, 2, H, W)  float32
        labels.pt       — (N,)          long
    """

    def __init__(self, data_dir: str = "outputs/processed/echo"):
        self.X = torch.load(f"{data_dir}/ed_es_frames.pt", weights_only=True)  # (N, 2, 112, 112)
        self.y = torch.load(f"{data_dir}/labels.pt",       weights_only=True)  # (N,)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


# ── Train / Val / Test split ───────────────────────────────────────────────────

def split_dataset(
    dataset: Dataset,
    train_frac: float = 0.70,
    val_frac:   float = 0.15,
    seed: int = 42,
) -> tuple[Dataset, Dataset, Dataset]:
    """
    Random stratified split of a dataset into train / val / test subsets.
    Returns three Subset objects.
    """
    from torch.utils.data import Subset

    n = len(dataset)
    rng = np.random.default_rng(seed)

    # Gather labels
    labels = np.array([dataset[i][1].item() for i in range(n)])

    # Stratified split: partition each class separately then merge
    idx_0 = np.where(labels == 0)[0]
    idx_1 = np.where(labels == 1)[0]

    def _split_class(idx: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        rng.shuffle(idx)
        n_tr = int(len(idx) * train_frac)
        n_va = int(len(idx) * val_frac)
        return idx[:n_tr], idx[n_tr:n_tr + n_va], idx[n_tr + n_va:]

    tr0, va0, te0 = _split_class(idx_0)
    tr1, va1, te1 = _split_class(idx_1)

    train_idx = np.concatenate([tr0, tr1])
    val_idx   = np.concatenate([va0, va1])
    test_idx  = np.concatenate([te0, te1])

    return Subset(dataset, train_idx), Subset(dataset, val_idx), Subset(dataset, test_idx)


def make_weighted_sampler(dataset: Dataset) -> WeightedRandomSampler:
    """
    Build a WeightedRandomSampler to handle class imbalance.
    Draws samples so each batch has approximately equal class representation.
    """
    labels = np.array([dataset[i][1].item() for i in range(len(dataset))])
    class_counts = np.bincount(labels)
    class_weights = 1.0 / class_counts
    sample_weights = class_weights[labels]
    sampler = WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.float),
        num_samples=len(labels),
        replacement=True,
    )
    return sampler


def make_loaders(
    dataset: Dataset,
    batch_size: int = 32,
    num_workers: int = 0,
    pin_memory: bool = True,
    seed: int = 42,
    use_weighted_sampler: bool = True,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """
    Convenience wrapper: split dataset → build DataLoaders.
    Returns (train_loader, val_loader, test_loader).

    Args:
        use_weighted_sampler: If True (default), applies WeightedRandomSampler to
            the training loader so each batch has approximately balanced classes.
            Set to False when the CE loss already applies its own class weights
            (e.g., with pos_weight) to avoid double-counting the imbalance.
            For Echo (76/24 split), the sampler is used and pos_weight is set to
            a mild 1.5 correction (not full n_neg/n_pos ratio).
    """
    train_ds, val_ds, test_ds = split_dataset(dataset, seed=seed)

    if use_weighted_sampler:
        sampler = make_weighted_sampler(train_ds)
        train_loader = DataLoader(
            train_ds, batch_size=batch_size, sampler=sampler,
            num_workers=num_workers, pin_memory=pin_memory,
        )
    else:
        train_loader = DataLoader(
            train_ds, batch_size=batch_size, shuffle=True,
            num_workers=num_workers, pin_memory=pin_memory,
        )

    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=pin_memory,
    )
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=pin_memory,
    )
    return train_loader, val_loader, test_loader
