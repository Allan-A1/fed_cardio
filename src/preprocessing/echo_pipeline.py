"""
Echo Preprocessing Pipeline — Hospital C (EchoNet-Pediatric)
=============================================================
Steps:
  1. Read FileList.csv — get video filenames + EF values
  2. Derive binary label: EF < 55% → 1 (reduced function), else → 0 (normal)
     (55% is the standard ASE pediatric LV dysfunction cutoff)
  3. Load each .avi video via OpenCV
  4. Extract End-Diastolic (ED) and End-Systolic (ES) frames
     using VolumeTracings.csv frame indices
  5. Resize frames to 112×112, normalize to [0, 1]
  6. Stack ED+ES as 2-channel input (2, H, W)
  7. Save processed tensors + labels to outputs/

Usage:
    python -m src.preprocessing.echo_pipeline
"""

import os
import glob
import numpy as np
import pandas as pd
import cv2
import torch
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR     = "datasets/EchoNet-Pediatric/echonetpediatric/pediatric_echo_avi/pediatric_echo_avi"
A4C_DIR      = os.path.join(DATA_DIR, "A4C")
VIDEOS_DIR   = os.path.join(A4C_DIR, "Videos")
FILELIST_CSV = os.path.join(A4C_DIR, "FileList.csv")
TRACINGS_CSV = os.path.join(A4C_DIR, "VolumeTracings.csv")
OUTPUT_DIR   = "outputs/processed/echo"

IMG_SIZE     = 112    # resize frames to 112×112
EF_CUTOFF    = 55.0   # ASE pediatric LV dysfunction threshold (%)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_filelist(csv_path: str) -> pd.DataFrame:
    """Load FileList.csv and derive binary labels from EF."""
    df = pd.read_csv(csv_path)
    # Standardise column names (handle case variations)
    df.columns = [c.strip() for c in df.columns]

    # EF column name varies — find it
    ef_col = next((c for c in df.columns if "EF" in c.upper()), None)
    fn_col = next((c for c in df.columns if "FILE" in c.upper() or "NAME" in c.upper()), None)

    if ef_col is None or fn_col is None:
        raise ValueError(f"Could not find EF or FileName columns. Columns: {df.columns.tolist()}")

    df = df.rename(columns={ef_col: "EF", fn_col: "FileName"})
    df["label"] = (df["EF"] < EF_CUTOFF).astype(int)  # 1 = reduced function
    return df[["FileName", "EF", "label"]].dropna()


def get_ed_es_frames(tracings_df: pd.DataFrame, filename: str) -> tuple[int, int] | None:
    """
    Get ED (end-diastolic) and ES (end-systolic) frame numbers
    from VolumeTracings.csv for a given filename.
    Handles non-numeric Frame values like 'No Systolic' / 'No Diastolic'.
    """
    rows = tracings_df[tracings_df["FileName"] == filename].copy()
    if rows.empty:
        return None

    # Drop rows where Frame is not a valid integer string
    rows["Frame"] = pd.to_numeric(rows["Frame"], errors="coerce")
    rows = rows.dropna(subset=["Frame"])
    if rows.empty:
        return None

    rows["Frame"] = rows["Frame"].astype(int)

    # ED = frame with largest volume, ES = frame with smallest
    if "Volume" in rows.columns:
        rows["Volume"] = pd.to_numeric(rows["Volume"], errors="coerce")
        rows = rows.dropna(subset=["Volume"])
        if rows.empty:
            return None
        ed_row = rows.loc[rows["Volume"].idxmax()]
        es_row = rows.loc[rows["Volume"].idxmin()]
    else:
        ed_row = rows.iloc[0]
        es_row = rows.iloc[-1]

    return int(ed_row["Frame"]), int(es_row["Frame"])


def extract_frame(video_path: str, frame_idx: int, size: int) -> np.ndarray | None:
    """Extract a single frame from an AVI video and resize."""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (size, size))
    normalized = resized.astype(np.float32) / 255.0
    return normalized


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run():
    print("Loading FileList.csv ...")
    filelist_df = load_filelist(FILELIST_CSV)
    print(f"  Total records: {len(filelist_df)}")
    print(f"  Label dist — Normal (0): {(filelist_df['label']==0).sum()}  |  Reduced EF (1): {(filelist_df['label']==1).sum()}")

    print("\nLoading VolumeTracings.csv ...")
    tracings_df = pd.read_csv(TRACINGS_CSV)
    tracings_df.columns = [c.strip() for c in tracings_df.columns]

    all_frames, all_labels, all_meta = [], [], []
    skipped = 0

    for _, row in tqdm(filelist_df.iterrows(), total=len(filelist_df), desc="Processing echo videos"):
        filename = row["FileName"]
        label    = row["label"]

        # Find video file
        video_path = os.path.join(VIDEOS_DIR, filename)
        if not os.path.exists(video_path):
            video_path += ".avi"
        if not os.path.exists(video_path):
            skipped += 1
            continue

        # Get ED/ES frame indices from tracings
        frame_info = get_ed_es_frames(tracings_df, filename)
        if frame_info is None:
            # Fall back: use frame 0 and mid-point
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            ed_idx, es_idx = 0, total_frames // 2
        else:
            ed_idx, es_idx = frame_info

        ed_frame = extract_frame(video_path, ed_idx, IMG_SIZE)
        es_frame = extract_frame(video_path, es_idx, IMG_SIZE)

        if ed_frame is None or es_frame is None:
            skipped += 1
            continue

        # Stack as 2-channel tensor (ED, ES)
        pair = np.stack([ed_frame, es_frame], axis=0)   # (2, H, W)
        all_frames.append(pair)
        all_labels.append(label)
        all_meta.append({
            "filename": filename,
            "EF":       row["EF"],
            "label":    label,
            "ed_frame": ed_idx,
            "es_frame": es_idx,
        })

    print(f"\nSkipped (missing video/frames): {skipped}")
    print(f"Total processed: {len(all_frames)}")
    print(f"Label dist — Normal (0): {all_labels.count(0)}  |  Reduced EF (1): {all_labels.count(1)}")

    if len(all_frames) == 0:
        print("No frames processed. Check DATA_DIR path.")
        return

    frames_tensor = torch.tensor(np.stack(all_frames), dtype=torch.float32)  # (N, 2, H, W)
    labels_tensor = torch.tensor(all_labels, dtype=torch.long)

    torch.save(frames_tensor,  os.path.join(OUTPUT_DIR, "ed_es_frames.pt"))
    torch.save(labels_tensor,  os.path.join(OUTPUT_DIR, "labels.pt"))

    meta_df = pd.DataFrame(all_meta)
    meta_df.to_csv(os.path.join(OUTPUT_DIR, "metadata.csv"), index=False)

    print(f"\n[DONE] Saved to {OUTPUT_DIR}/")
    print(f"   ed_es_frames.pt  shape: {frames_tensor.shape}")
    print(f"   labels.pt        shape: {labels_tensor.shape}")
    print(f"   metadata.csv     rows:  {len(meta_df)}")


if __name__ == "__main__":
    run()
