"""
PCG Preprocessing Pipeline — Hospital A (CirCor DigiScope)
============================================================
Steps:
  1. Parse subject metadata (.txt files) — filter to pediatric (age ≤ 18 yrs)
  2. Load .wav recordings
  3. Resample to 4000 Hz (dataset native rate)
  4. Segment into fixed-length windows (5 sec)
  5. Compute mel-spectrogram
  6. Derive binary label: normal=0, abnormal=1 (unknown → dropped)
  7. Save processed tensors + labels to outputs/

Usage:
    python -m src.preprocessing.pcg_pipeline
"""

import os
import glob
import numpy as np
import pandas as pd
import librosa
import soundfile as sf
import torch
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR    = "datasets/CirCor_DigiScope/the-circor-digiscope-phonocardiogram-dataset-1.0.3"
OUTPUT_DIR  = "outputs/processed/pcg"
SAMPLE_RATE = 4000        # Hz — native CirCor rate
SEGMENT_SEC = 5           # seconds per window
N_FFT       = 512
HOP_LENGTH  = 128
N_MELS      = 64
MAX_AGE_YRS = 18 * 12     # 216 months — pediatric cutoff

# Age group string → approximate months (used for filtering when numeric age unavailable)
AGE_GROUP_MAP = {
    "Neonate":     1,
    "Infant":      6,
    "Child":       84,    # ~7 yrs, clearly pediatric
    "Adolescent":  168,   # ~14 yrs
    "Young Adult": 264,   # ~22 yrs → above cutoff, filtered out
}

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_subject_file(txt_path: str) -> dict | None:
    """
    Parse a CirCor subject .txt file.
    Returns dict with keys: subject_id, murmur, age_months
    Returns None if the subject should be excluded.
    """
    info = {}
    with open(txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#Age:"):
                info["age_group"] = line.split(":", 1)[1].strip()
            elif line.startswith("#Murmur:"):
                info["murmur"] = line.split(":", 1)[1].strip()

    # Filter: only known murmur labels
    murmur = info.get("murmur", "Unknown")
    if murmur == "Unknown":
        return None

    # Filter: pediatric only
    age_group = info.get("age_group", "")
    age_months = AGE_GROUP_MAP.get(age_group, 999)
    if age_months > MAX_AGE_YRS:
        return None

    subject_id = os.path.splitext(os.path.basename(txt_path))[0]
    label = 0 if murmur == "Absent" else 1   # binary: normal=0, abnormal=1

    return {"subject_id": subject_id, "label": label, "age_group": age_group}


def load_and_resample(wav_path: str, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Load a .wav file and resample to target_sr."""
    audio, sr = librosa.load(wav_path, sr=target_sr, mono=True)
    return audio


def segment_audio(audio: np.ndarray, sr: int, seg_sec: int) -> list[np.ndarray]:
    """Split audio into non-overlapping fixed-length segments. Drop last partial."""
    seg_len = sr * seg_sec
    segments = []
    for start in range(0, len(audio) - seg_len + 1, seg_len):
        segments.append(audio[start : start + seg_len])
    return segments


def compute_melspectrogram(segment: np.ndarray, sr: int) -> np.ndarray:
    """Compute log-mel spectrogram. Returns (n_mels, time) array."""
    mel = librosa.feature.melspectrogram(
        y=segment, sr=sr,
        n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=N_MELS
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    # Normalize to [0, 1]
    log_mel = (log_mel - log_mel.min()) / (log_mel.max() - log_mel.min() + 1e-8)
    return log_mel.astype(np.float32)


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run():
    txt_files = glob.glob(os.path.join(DATA_DIR, "training_data", "*.txt"))
    if not txt_files:
        # Try root of dataset
        txt_files = glob.glob(os.path.join(DATA_DIR, "*.txt"))

    print(f"Found {len(txt_files)} subject files.")

    all_specs, all_labels, all_meta = [], [], []
    skipped_unknown, skipped_adult = 0, 0

    for txt_path in tqdm(txt_files, desc="Processing subjects"):
        meta = parse_subject_file(txt_path)
        if meta is None:
            skipped_unknown += 1
            continue

        subject_id = meta["subject_id"]
        label      = meta["label"]

        # Find all .wav files for this subject
        subject_dir = os.path.dirname(txt_path)
        wav_files = glob.glob(os.path.join(subject_dir, f"{subject_id}_*.wav"))

        for wav_path in wav_files:
            try:
                audio    = load_and_resample(wav_path)
                segments = segment_audio(audio, SAMPLE_RATE, SEGMENT_SEC)

                for seg in segments:
                    spec = compute_melspectrogram(seg, SAMPLE_RATE)
                    all_specs.append(spec)
                    all_labels.append(label)
                    all_meta.append({
                        "subject_id": subject_id,
                        "wav_file":   os.path.basename(wav_path),
                        "age_group":  meta["age_group"],
                        "label":      label,
                    })
            except Exception as e:
                print(f"  [WARN] Failed {wav_path}: {e}")
                continue

    print(f"\nSkipped (unknown label): {skipped_unknown}")
    print(f"Total segments: {len(all_specs)}")
    print(f"Label distribution — Normal (0): {all_labels.count(0)}  |  Abnormal (1): {all_labels.count(1)}")

    if len(all_specs) == 0:
        print("No segments processed. Check DATA_DIR path.")
        return

    # Save as tensors
    specs_tensor  = torch.tensor(np.stack(all_specs), dtype=torch.float32)  # (N, n_mels, time)
    labels_tensor = torch.tensor(all_labels, dtype=torch.long)

    torch.save(specs_tensor,  os.path.join(OUTPUT_DIR, "spectrograms.pt"))
    torch.save(labels_tensor, os.path.join(OUTPUT_DIR, "labels.pt"))

    meta_df = pd.DataFrame(all_meta)
    meta_df.to_csv(os.path.join(OUTPUT_DIR, "metadata.csv"), index=False)

    print(f"\n[DONE] Saved to {OUTPUT_DIR}/")
    print(f"   spectrograms.pt  shape: {specs_tensor.shape}")
    print(f"   labels.pt        shape: {labels_tensor.shape}")
    print(f"   metadata.csv     rows:  {len(meta_df)}")


if __name__ == "__main__":
    run()
