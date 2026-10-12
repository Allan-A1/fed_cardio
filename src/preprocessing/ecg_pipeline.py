"""
ECG Preprocessing Pipeline — Hospital B (ZZU-pECG)
====================================================
Steps:
  1. Read AttributesDictionary.csv — get filenames, labels, lead count, age
  2. Derive binary label: ICD-10 code present & not 'C21' (normal) → 1, else → 0
     'C21' is the ZZU dataset's code for normal ECG
  3. Filter to pediatric age (<=18 yrs = <=6570 days)
  4. Load each record using wfdb (.dat + .hea)
  5. Resample to 500 Hz (already native), bandpass filter 0.5–40 Hz
  6. Pad/truncate to fixed length (10 sec = 5000 samples)
  7. Normalize per-lead to [-1, 1]
  8. Also track 9-lead vs 12-lead for Week 3 ablation
  9. Save tensors + labels + metadata to outputs/

Usage:
    python -m src.preprocessing.ecg_pipeline
"""

import os
import glob
import numpy as np
import pandas as pd
import wfdb
from scipy.signal import butter, filtfilt
import torch
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR    = "datasets/ZZU-pECG"
ECG_DIR     = os.path.join(DATA_DIR, "Child_ecg")
ATTRS_CSV   = os.path.join(DATA_DIR, "AttributesDictionary.csv")
OUTPUT_DIR  = "outputs/processed/ecg"

SAMPLE_RATE   = 500        # Hz — native rate
FIXED_LEN     = 5000       # samples = 10 seconds at 500 Hz
MAX_AGE_DAYS  = 18 * 365   # 6570 days = 18 years
NORMAL_CODE   = "C21"      # ZZU-pECG code for normal ECG

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def bandpass_filter(signal: np.ndarray, fs: int,
                    lowcut: float = 0.5, highcut: float = 40.0) -> np.ndarray:
    """Apply Butterworth bandpass filter to each lead."""
    nyq = fs / 2.0
    b, a = butter(4, [lowcut / nyq, highcut / nyq], btype="band")
    filtered = np.zeros_like(signal)
    for i in range(signal.shape[1]):
        filtered[:, i] = filtfilt(b, a, signal[:, i])
    return filtered


def pad_or_truncate(signal: np.ndarray, target_len: int) -> np.ndarray:
    """Pad with zeros or truncate to target_len samples."""
    n = signal.shape[0]
    if n >= target_len:
        return signal[:target_len, :]
    pad = np.zeros((target_len - n, signal.shape[1]))
    return np.vstack([signal, pad])


def normalize_leads(signal: np.ndarray) -> np.ndarray:
    """Normalize each lead independently to [-1, 1]."""
    out = np.zeros_like(signal, dtype=np.float32)
    for i in range(signal.shape[1]):
        lead = signal[:, i]
        rng = lead.max() - lead.min()
        if rng > 1e-8:
            out[:, i] = 2.0 * (lead - lead.min()) / rng - 1.0
    return out


def parse_label(icd_code_str: str) -> int:
    """
    Binary label: 0 = normal, 1 = abnormal (any CVD)
    Normal is indicated by AHA_code 'C21' (confirmed from dataset paper).
    """
    if pd.isna(icd_code_str) or str(icd_code_str).strip() == "":
        return -1   # unknown — will be dropped
    return 0 if NORMAL_CODE in str(icd_code_str) else 1


def parse_age_days(age_val) -> int | None:
    """Parse age in days from AttributesDictionary (stored as e.g. '572d')."""
    try:
        s = str(age_val).strip().lower().replace("d", "").replace("'", "")
        return int(float(s))
    except Exception:
        return None


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run():
    print("Loading AttributesDictionary.csv ...")
    df = pd.read_csv(ATTRS_CSV)
    df.columns = [c.strip() for c in df.columns]

    # Derive label from AHA_code (contains C21 for normal)
    df["label"] = df["AHA_code"].apply(parse_label)
    df = df[df["label"] >= 0]   # drop unknowns

    # Pediatric filter
    df["age_days"] = df["Age"].apply(parse_age_days)
    df = df[df["age_days"].notna() & (df["age_days"] <= MAX_AGE_DAYS)]

    print(f"  After filtering — records: {len(df)}")
    print(f"  Label dist — Normal (0): {(df['label']==0).sum()}  |  Abnormal (1): {(df['label']==1).sum()}")
    print(f"  Lead counts — 9-lead: {(df['Lead']==9).sum()}  |  12-lead: {(df['Lead']==12).sum()}")

    all_signals, all_labels, all_meta = [], [], []
    skipped = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing ECG records"):
        filename = str(row["Filename"]).strip()
        rec_path = os.path.join(ECG_DIR, filename)

        try:
            rec = wfdb.rdrecord(rec_path)
        except Exception as e:
            skipped += 1
            continue

        signal = rec.p_signal   # shape: (samples, n_leads)
        if signal is None or signal.ndim != 2:
            skipped += 1
            continue

        # Handle NaN values from missing leads
        signal = np.nan_to_num(signal, nan=0.0)

        # Bandpass filter
        try:
            signal = bandpass_filter(signal, SAMPLE_RATE)
        except Exception:
            pass  # skip filter if signal too short

        # Pad/truncate to fixed length
        signal = pad_or_truncate(signal, FIXED_LEN)

        # Normalize
        signal = normalize_leads(signal)

        # Use first 9 leads for consistent tensor shape (I II III AVR AVL AVF V1 V3 V5)
        signal = signal[:, :9]   # (5000, 9)

        all_signals.append(signal.T)   # store as (9, 5000) — channels first
        all_labels.append(int(row["label"]))
        all_meta.append({
            "filename":  filename,
            "ecg_id":    row.get("ECG_ID", ""),
            "age_days":  int(row["age_days"]),
            "gender":    row.get("Gender", ""),
            "lead_count": int(row.get("Lead", 9)),
            "label":     int(row["label"]),
        })

    print(f"\nSkipped (read errors): {skipped}")
    print(f"Total processed: {len(all_signals)}")
    print(f"Label dist — Normal (0): {all_labels.count(0)}  |  Abnormal (1): {all_labels.count(1)}")

    if len(all_signals) == 0:
        print("No records processed. Check DATA_DIR path.")
        return

    signals_tensor = torch.tensor(np.stack(all_signals), dtype=torch.float32)  # (N, 9, 5000)
    labels_tensor  = torch.tensor(all_labels, dtype=torch.long)

    torch.save(signals_tensor, os.path.join(OUTPUT_DIR, "ecg_signals.pt"))
    torch.save(labels_tensor,  os.path.join(OUTPUT_DIR, "labels.pt"))

    meta_df = pd.DataFrame(all_meta)
    meta_df.to_csv(os.path.join(OUTPUT_DIR, "metadata.csv"), index=False)

    # Also save 9-lead vs 12-lead split indices for Week 3 ablation
    idx_9lead  = meta_df[meta_df["lead_count"] == 9].index.tolist()
    idx_12lead = meta_df[meta_df["lead_count"] == 12].index.tolist()
    torch.save(torch.tensor(idx_9lead),  os.path.join(OUTPUT_DIR, "idx_9lead.pt"))
    torch.save(torch.tensor(idx_12lead), os.path.join(OUTPUT_DIR, "idx_12lead.pt"))

    print(f"\n[DONE] Saved to {OUTPUT_DIR}/")
    print(f"   ecg_signals.pt  shape: {signals_tensor.shape}")
    print(f"   labels.pt       shape: {labels_tensor.shape}")
    print(f"   metadata.csv    rows:  {len(meta_df)}")
    print(f"   idx_9lead.pt    count: {len(idx_9lead)}")
    print(f"   idx_12lead.pt   count: {len(idx_12lead)}")


if __name__ == "__main__":
    run()
