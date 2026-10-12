# -*- coding: utf-8 -*-
"""
Raw PCG and ECG Signal Visualization  (white / standard matplotlib style)
==========================================================================
Plots raw waveforms for:
  - PCG: CirCor DigiScope dataset (.wav, 4000 Hz, 4 positions: AV, MV, PV, TV)
  - ECG: ZZU-pECG dataset (.dat WFDB format, 500 Hz, 9 leads)
"""

import os
import wave
import struct
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.signal import find_peaks

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
PCG_DIR = r"d:\clg\project\fl_pediatric\dataset\the-circor-digiscope-phonocardiogram-dataset-1.0.3\training_data"
ECG_DIR = r"d:\clg\project\fl_pediatric\datasets\ZZU-pECG\Child_ecg\P00\P00001"
OUT_DIR = r"d:\clg\project\fl_pediatric\outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# Use the classic white-background style
plt.style.use("seaborn-v0_8-whitegrid")

# ─────────────────────────────────────────────
# Colours – standard, readable on white
# ─────────────────────────────────────────────
PCG_COLORS = {
    "AV": "#1f77b4",   # blue
    "MV": "#d62728",   # red
    "PV": "#2ca02c",   # green
    "TV": "#9467bd",   # purple
}
ECG_COLORS = [
    "#1f77b4", "#d62728", "#2ca02c", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def read_wav(path):
    """Return (sample_rate, float32 samples [-1,1]) from a 16-bit WAV file."""
    with wave.open(path, "rb") as wf:
        sr       = wf.getframerate()
        n_frames = wf.getnframes()
        raw      = wf.readframes(n_frames)
    samples = np.array(struct.unpack(f"<{n_frames}h", raw), dtype=np.float32)
    samples /= 32768.0
    return sr, samples


def read_wfdb_dat(hea_path):
    """
    Minimal WFDB reader for 16-bit interleaved .dat files.
    Returns (fs, lead_names, data[n_leads, n_samples]) in mV.
    """
    with open(hea_path) as f:
        lines = [l.strip() for l in f if l.strip()]

    hdr       = lines[0].split()
    n_signals = int(hdr[1])
    fs        = int(hdr[2])
    n_samples = int(hdr[3]) if len(hdr) > 3 else None

    gains, baselines, lead_names = [], [], []
    dat_file = None
    for line in lines[1:]:
        if line.startswith("#"):
            continue
        parts = line.split()
        if dat_file is None:
            dat_file = parts[0]
        fmt_gain = parts[2]
        if "(" in fmt_gain:
            gain_str, rest = fmt_gain.split("(")
            gain     = float(gain_str)
            baseline = float(rest.split(")")[0])
        else:
            gain     = float(fmt_gain.split("/")[0]) if "/" in fmt_gain else float(fmt_gain)
            baseline = 0.0
        gains.append(gain)
        baselines.append(baseline)
        lead_names.append(parts[-1])

    dat_path = os.path.join(os.path.dirname(hea_path), dat_file)
    raw      = np.fromfile(dat_path, dtype=np.int16)
    if n_samples is None:
        n_samples = len(raw) // n_signals
    data = raw[: n_signals * n_samples].reshape(n_samples, n_signals).T.astype(np.float64)
    for i in range(n_signals):
        data[i] = (data[i] - baselines[i]) / gains[i]

    return fs, lead_names, data


def t_axis(n, fs):
    return np.arange(n) / fs


# ══════════════════════════════════════════════════════════════
# 1. PCG  – patient 13918
# ══════════════════════════════════════════════════════════════
print("Generating PCG plot ...")

patient_pcg = "13918"
positions   = ["AV", "MV", "PV", "TV"]
pos_labels  = {
    "AV": "Aortic Valve (AV)",
    "MV": "Mitral Valve (MV)",
    "PV": "Pulmonary Valve (PV)",
    "TV": "Tricuspid Valve (TV)",
}
pcg_data = {}
for pos in positions:
    wav_path = os.path.join(PCG_DIR, f"{patient_pcg}_{pos}.wav")
    if os.path.exists(wav_path):
        sr, sig = read_wav(wav_path)
        pcg_data[pos] = (sr, sig)

fig_pcg, axes = plt.subplots(
    len(positions), 1,
    figsize=(14, 9),
    sharex=False,
    constrained_layout=True,
)

fig_pcg.suptitle(
    f"PCG — Raw Audio Waveforms  |  Patient {patient_pcg}  |  CirCor DigiScope",
    fontsize=13, fontweight="bold"
)

for idx, pos in enumerate(positions):
    ax = axes[idx]
    color = PCG_COLORS[pos]

    if pos not in pcg_data:
        ax.text(0.5, 0.5, f"No {pos} recording", ha="center", va="center",
                transform=ax.transAxes, color="gray")
        ax.set_ylabel(pos_labels[pos], fontsize=9)
        continue

    sr, sig = pcg_data[pos]
    t = t_axis(len(sig), sr)
    dur = len(sig) / sr

    ax.plot(t, sig, color=color, linewidth=0.7, label=pos_labels[pos])
    ax.fill_between(t, sig, alpha=0.15, color=color)

    # horizontal zero line
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--", alpha=0.4)

    ax.set_ylabel("Amplitude", fontsize=8)
    ax.set_xlim([0, t[-1]])
    ax.set_title(
        f"{pos_labels[pos]}  (duration: {dur:.2f} s,  Fs: {sr} Hz)",
        fontsize=9, loc="left", pad=3
    )
    ax.tick_params(labelsize=8)

    if idx == len(positions) - 1:
        ax.set_xlabel("Time (s)", fontsize=9)
    else:
        ax.set_xticklabels([])

# small legend strip at bottom
handles = [
    plt.Line2D([0], [0], color=PCG_COLORS[p], linewidth=2, label=pos_labels[p])
    for p in positions if p in pcg_data
]
fig_pcg.legend(handles=handles, loc="lower center",
               ncol=len(handles), fontsize=8,
               bbox_to_anchor=(0.5, -0.02), frameon=True)

pcg_out = os.path.join(OUT_DIR, "pcg_raw_waveforms.png")
fig_pcg.savefig(pcg_out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig_pcg)
print(f"  [OK] Saved -> {pcg_out}")


# ══════════════════════════════════════════════════════════════
# 2. ECG  – patient P00001
# ══════════════════════════════════════════════════════════════
print("Generating ECG plot ...")

hea_path = os.path.join(ECG_DIR, "P00001_E01.hea")
fs_ecg, lead_names, ecg_data = read_wfdb_dat(hea_path)

n_leads   = len(lead_names)
n_samples = ecg_data.shape[1]
t_ecg     = t_axis(n_samples, fs_ecg)

fig_ecg, axes_ecg = plt.subplots(
    n_leads, 1,
    figsize=(14, 12),
    sharex=True,
    constrained_layout=True,
)

fig_ecg.suptitle(
    f"ECG — Raw Signal  |  Patient P00001  |  ZZU-pECG  |  Diagnosis: Ventricular Septal Defect",
    fontsize=12, fontweight="bold"
)

for i, lead in enumerate(lead_names):
    ax    = axes_ecg[i]
    sig   = ecg_data[i]
    color = ECG_COLORS[i % len(ECG_COLORS)]

    ax.plot(t_ecg, sig, color=color, linewidth=0.8)

    # R-peak markers
    amp_thresh = 0.4 * np.max(sig) if np.max(sig) > 0 else None
    if amp_thresh and amp_thresh > 0:
        peaks, _ = find_peaks(sig, height=amp_thresh, distance=int(0.3 * fs_ecg))
        if len(peaks) > 0:
            ax.scatter(t_ecg[peaks], sig[peaks],
                       color=color, s=20, zorder=5,
                       edgecolors="black", linewidths=0.5)

    ax.axhline(0, color="black", linewidth=0.4, linestyle="--", alpha=0.4)
    ax.set_ylabel(f"{lead}\n(mV)", fontsize=8, rotation=0, labelpad=35, va="center")
    ax.set_xlim([0, t_ecg[-1]])
    ax.tick_params(labelsize=7)

    # lighter minor gridlines for ECG paper look
    ax.set_xticks(np.arange(0, t_ecg[-1], 0.2), minor=False)
    ax.set_xticks(np.arange(0, t_ecg[-1], 0.04), minor=True)
    ax.grid(which="major", linewidth=0.6, linestyle="-",  color="#e0e0e0")
    ax.grid(which="minor", linewidth=0.3, linestyle="--", color="#f0f0f0")

axes_ecg[-1].set_xlabel("Time (s)", fontsize=9)
fig_ecg.text(0.5, -0.01,
    f"Fs = {fs_ecg} Hz  |  Duration = {n_samples/fs_ecg:.1f} s  |  9 Leads",
    ha="center", fontsize=8, color="gray")

ecg_out = os.path.join(OUT_DIR, "ecg_raw_waveforms.png")
fig_ecg.savefig(ecg_out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig_ecg)
print(f"  [OK] Saved -> {ecg_out}")


# ══════════════════════════════════════════════════════════════
# 3. Combined 1-page overview
# ══════════════════════════════════════════════════════════════
print("Generating combined overview ...")

fig_combo = plt.figure(figsize=(16, 16), facecolor="white")
fig_combo.suptitle(
    "Pediatric Cardiac Signals — Raw Data Overview",
    fontsize=14, fontweight="bold", y=0.99
)

gs_combo  = gridspec.GridSpec(2, 1, figure=fig_combo,
                               hspace=0.18, top=0.96, bottom=0.04)
gs_top    = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=gs_combo[0], hspace=0.60)
gs_bottom = gridspec.GridSpecFromSubplotSpec(9, 1, subplot_spec=gs_combo[1], hspace=0.50)

# ── PCG section ──
ax_pcg_title = fig_combo.add_subplot(gs_top[0])
ax_pcg_title.set_visible(False)
fig_combo.text(0.01, 0.975,
    f"PCG  —  Patient {patient_pcg}  |  CirCor DigiScope  |  4000 Hz",
    fontsize=10, fontweight="bold", color="#1f77b4", va="top")

for idx, pos in enumerate(positions):
    ax = fig_combo.add_subplot(gs_top[idx])
    ax.set_facecolor("white")
    if pos not in pcg_data:
        ax.set_visible(False)
        continue
    sr, sig = pcg_data[pos]
    t = t_axis(len(sig), sr)
    ax.plot(t, sig, color=PCG_COLORS[pos], linewidth=0.6)
    ax.fill_between(t, sig, alpha=0.12, color=PCG_COLORS[pos])
    ax.axhline(0, color="black", linewidth=0.4, linestyle="--", alpha=0.3)
    ax.set_ylabel(pos, fontsize=8)
    ax.set_xlim([0, t[-1]])
    ax.tick_params(labelsize=7)
    ax.set_title(pos_labels[pos], fontsize=8, loc="left", pad=2)
    if idx == len(positions) - 1:
        ax.set_xlabel("Time (s)", fontsize=8)

# ── ECG section ──
fig_combo.text(0.01, 0.475,
    "ECG  —  Patient P00001  |  ZZU-pECG  |  500 Hz  |  VSD",
    fontsize=10, fontweight="bold", color="#d62728", va="top")

for i, lead in enumerate(lead_names):
    ax    = fig_combo.add_subplot(gs_bottom[i])
    ax.set_facecolor("white")
    sig   = ecg_data[i]
    color = ECG_COLORS[i % len(ECG_COLORS)]
    ax.plot(t_ecg, sig, color=color, linewidth=0.65)
    ax.axhline(0, color="black", linewidth=0.3, linestyle="--", alpha=0.3)
    ax.set_ylabel(lead, fontsize=7)
    ax.set_xlim([0, t_ecg[-1]])
    ax.tick_params(labelsize=6)
    ax.grid(linewidth=0.4, color="#e8e8e8")
    if i == n_leads - 1:
        ax.set_xlabel("Time (s)", fontsize=8)

combo_out = os.path.join(OUT_DIR, "combined_pcg_ecg_overview.png")
fig_combo.savefig(combo_out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig_combo)
print(f"  [OK] Saved -> {combo_out}")

print("\nAll done! Output files:")
for f in [pcg_out, ecg_out, combo_out]:
    print(f"  {f}")
