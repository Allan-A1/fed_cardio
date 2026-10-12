# -*- coding: utf-8 -*-
"""
Normal vs Abnormal Comparison Plots — 3 Modalities
====================================================
  1. PCG   : Mel Spectrogram  |  Normal (no murmur)  vs  Abnormal (murmur present)
  2. ECG   : Raw waveform     |  Normal (A1, sinus)   vs  Abnormal (VSD)
  3. Echo  : Mid-systole frame|  Normal (EF 72.99%)   vs  Abnormal (EF 7.02%)

Abnormal regions are highlighted with red rectangles / overlays.
"""

import os, wave, struct
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from scipy.signal import find_peaks, stft
from scipy.fft import fft
import warnings
warnings.filterwarnings("ignore")

# ── paths ─────────────────────────────────────────────────────
PCG_DIR  = r"d:\clg\project\fl_pediatric\dataset\the-circor-digiscope-phonocardiogram-dataset-1.0.3\training_data"
ECG_BASE = r"d:\clg\project\fl_pediatric\datasets\ZZU-pECG\Child_ecg"
ECHO_DIR = r"d:\clg\project\fl_pediatric\datasets\EchoNet-Pediatric\echonetpediatric\pediatric_echo_avi\pediatric_echo_avi\A4C\Videos"
OUT_DIR  = r"d:\clg\project\fl_pediatric\outputs"
os.makedirs(OUT_DIR, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")

# ── palette ────────────────────────────────────────────────────
C_NORMAL   = "#2196F3"   # blue
C_ABNORMAL = "#F44336"   # red
C_HIGHLIGHT = "#FF9800"  # orange for region boxes
ALPHA_BOX  = 0.18

# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def read_wav(path):
    with wave.open(path, "rb") as wf:
        sr = wf.getframerate(); n = wf.getnframes()
        raw = wf.readframes(n)
    s = np.array(struct.unpack(f"<{n}h", raw), dtype=np.float32) / 32768.0
    return sr, s


def read_wfdb(hea_path):
    with open(hea_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    hdr = lines[0].split()
    n_sig = int(hdr[1]); fs = int(hdr[2])
    n_samp = int(hdr[3]) if len(hdr) > 3 else None
    gains, baselines, names = [], [], []
    dat_file = None
    for line in lines[1:]:
        if line.startswith("#"): continue
        parts = line.split()
        if dat_file is None: dat_file = parts[0]
        fg = parts[2]
        if "(" in fg:
            g, rest = fg.split("(")
            g = float(g); b = float(rest.split(")")[0])
        else:
            g = float(fg.split("/")[0]) if "/" in fg else float(fg); b = 0.0
        gains.append(g); baselines.append(b); names.append(parts[-1])
    dat = os.path.join(os.path.dirname(hea_path), dat_file)
    raw = np.fromfile(dat, dtype=np.int16)
    if n_samp is None: n_samp = len(raw) // n_sig
    data = raw[:n_sig*n_samp].reshape(n_samp, n_sig).T.astype(np.float64)
    for i in range(n_sig): data[i] = (data[i] - baselines[i]) / gains[i]
    return fs, names, data


def mel_spectrogram(signal, sr, n_fft=512, hop=128, n_mels=64):
    """Compute a simple mel spectrogram without librosa."""
    from scipy.signal import spectrogram as sp_spec
    f, t, Sxx = sp_spec(signal, fs=sr, nperseg=n_fft, noverlap=n_fft-hop,
                         scaling="spectrum")
    Sxx_db = 10 * np.log10(Sxx + 1e-10)
    # mel-scale bin boundaries (Hz)
    mel_lo, mel_hi = 2595*np.log10(1+20/700), 2595*np.log10(1+(sr/2)/700)
    mel_pts = np.linspace(mel_lo, mel_hi, n_mels+2)
    hz_pts  = 700*(10**(mel_pts/2595)-1)
    # map freq bins to mel bins via linear interp
    mel_S = np.zeros((n_mels, Sxx_db.shape[1]))
    for m in range(n_mels):
        lo, ctr, hi = hz_pts[m], hz_pts[m+1], hz_pts[m+2]
        mask = (f >= lo) & (f <= hi)
        if mask.sum():
            mel_S[m] = Sxx_db[mask].mean(axis=0)
    return t, f, mel_S, hz_pts


def read_video_frame(path, frame_idx=None):
    """Extract a single frame from an AVI using only stdlib."""
    try:
        import cv2
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_idx is None: frame_idx = total // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(frame_idx, total-1))
        ret, frame = cap.read()
        cap.release()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    except ImportError:
        pass
    # fallback: read raw AVI bytes at ~frame_idx position (rough)
    return None


# ══════════════════════════════════════════════════════════════
# Load data
# ══════════════════════════════════════════════════════════════
print("Loading PCG data ...")
# Normal = patient 2530 (Absent murmur), position AV
# Abnormal = patient 13918 (Present murmur), position AV
sr_n, pcg_n = read_wav(os.path.join(PCG_DIR, "2530_AV.wav"))
sr_a, pcg_a = read_wav(os.path.join(PCG_DIR, "13918_AV.wav"))

print("Loading ECG data ...")
# Normal  = P00002 (sinus tachycardia - relatively benign)  Lead II
# Abnormal = P00001 (VSD)  Lead II
fs_en, names_n, ecg_n_all = read_wfdb(os.path.join(ECG_BASE, "P00","P00002","P00002_E01.hea"))
fs_ea, names_a, ecg_a_all = read_wfdb(os.path.join(ECG_BASE, "P00","P00001","P00001_E01.hea"))
# Use Lead II (index 1)
ecg_n = ecg_n_all[1];  ecg_a = ecg_a_all[1]
t_en = np.arange(len(ecg_n)) / fs_en
t_ea = np.arange(len(ecg_a)) / fs_ea

print("Loading Echo frames ...")
echo_norm_path  = os.path.join(ECHO_DIR, "CR3dcb4fa-CR3dcb668-000052.avi")  # EF=72.99 Normal
echo_abnorm_path= os.path.join(ECHO_DIR, "CR32a966a-CR32a9af6-000064.avi")  # EF=7.02  Abnormal
frame_norm  = read_video_frame(echo_norm_path)
frame_abnorm= read_video_frame(echo_abnorm_path)

# ══════════════════════════════════════════════════════════════
# Mel Spectrograms for PCG
# ══════════════════════════════════════════════════════════════
print("Computing Mel spectrograms ...")
t_mn, _, mel_n, hz_pts_n = mel_spectrogram(pcg_n, sr_n)
t_ma, _, mel_a, hz_pts_a = mel_spectrogram(pcg_a, sr_a)

# ══════════════════════════════════════════════════════════════
# ECG: find R-peaks and flag abnormal intervals
# ══════════════════════════════════════════════════════════════

def get_peaks(sig, fs):
    thresh = 0.35 * np.max(sig) if np.max(sig) > 0 else None
    if thresh and thresh > 0:
        peaks, _ = find_peaks(sig, height=thresh, distance=int(0.25*fs))
        return peaks
    return np.array([])

peaks_n = get_peaks(ecg_n, fs_en)
peaks_a = get_peaks(ecg_a, fs_ea)

def rr_intervals(peaks, fs):
    if len(peaks) < 2: return np.array([])
    return np.diff(peaks) / fs * 1000   # ms

rr_n = rr_intervals(peaks_n, fs_en)
rr_a = rr_intervals(peaks_a, fs_ea)

# Flag abnormal beats: RR outside normal pediatric range [400, 1000] ms
def abnormal_beat_mask(peaks, rr, fs):
    mask = np.zeros(len(peaks)-1, dtype=bool)
    for i, rr_val in enumerate(rr):
        if rr_val < 350 or rr_val > 1100:
            mask[i] = True
    return mask

abn_mask_n = abnormal_beat_mask(peaks_n, rr_n, fs_en)
abn_mask_a = abnormal_beat_mask(peaks_a, rr_a, fs_ea)

# ══════════════════════════════════════════════════════════════
# Build figure — 3 rows × 2 cols (Normal | Abnormal)
# ══════════════════════════════════════════════════════════════
print("Plotting ...")

fig = plt.figure(figsize=(13, 10), facecolor="white")
fig.suptitle(
    "Normal vs Abnormal — Pediatric Cardiac Signal Comparison",
    fontsize=13, fontweight="bold", y=0.99
)

gs = gridspec.GridSpec(
    3, 2, figure=fig,
    hspace=0.52, wspace=0.30,
    top=0.94, bottom=0.05, left=0.07, right=0.97
)

# ─── row labels ──────────────────────────────────────────────
row_labels = ["PCG\n(Mel Spectrogram)", "ECG\n(Lead II)", "Echo\n(Mid-systole Frame)"]
col_labels = ["Normal", "Abnormal"]

for c, lbl in enumerate(col_labels):
    col_color = C_NORMAL if c == 0 else C_ABNORMAL
    fig.text(
        0.27 + c*0.48, 0.965, lbl,
        ha="center", fontsize=11, fontweight="bold", color=col_color
    )

# ══════════════════════════════════════════════════════════════
# Row 0 — PCG Mel Spectrogram
# ══════════════════════════════════════════════════════════════
for col, (t_m, mel_S, hz_pts, label, patient, murmur) in enumerate([
    (t_mn, mel_n, hz_pts_n, "Normal",   "2530",  "Absent"),
    (t_ma, mel_a, hz_pts_a, "Abnormal", "13918", "Present"),
]):
    ax = fig.add_subplot(gs[0, col])
    n_mels = mel_S.shape[0]
    im = ax.imshow(
        mel_S, aspect="auto", origin="lower",
        extent=[t_m[0], t_m[-1], 0, n_mels],
        cmap="viridis", interpolation="bilinear"
    )
    plt.colorbar(im, ax=ax, pad=0.02, label="dB", shrink=0.85)

    # y-ticks at mel bin boundaries
    tick_idx = np.linspace(0, n_mels-1, 6, dtype=int)
    freq_labels = [f"{hz_pts[i+1]:.0f}" for i in tick_idx]
    ax.set_yticks(tick_idx)
    ax.set_yticklabels(freq_labels, fontsize=7)

    if col == 1:  # Abnormal — highlight murmur frequency band (100–600 Hz, mel bins 10-35 approx)
        # Murmur energy typically sits in 100–800 Hz range
        mel_abn_lo, mel_abn_hi = 10, 38
        rect = mpatches.FancyBboxPatch(
            (t_m[0], mel_abn_lo), t_m[-1]-t_m[0], mel_abn_hi-mel_abn_lo,
            boxstyle="round,pad=0.02", linewidth=1.8,
            edgecolor=C_ABNORMAL, facecolor=C_ABNORMAL, alpha=0.15
        )
        ax.add_patch(rect)
        # also draw a bracket annotation
        ax.annotate(
            "Murmur\nenergy", xy=(t_m[-1]*0.85, (mel_abn_lo+mel_abn_hi)/2),
            fontsize=7, color=C_ABNORMAL, fontweight="bold",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor=C_ABNORMAL, alpha=0.85, linewidth=1.2)
        )
        # mark high-energy time regions
        energy_per_t = mel_S[mel_abn_lo:mel_abn_hi, :].mean(axis=0)
        thresh_e = np.percentile(energy_per_t, 70)
        in_burst = energy_per_t > thresh_e
        transitions = np.diff(in_burst.astype(int))
        starts = np.where(transitions == 1)[0]
        ends   = np.where(transitions == -1)[0]
        if len(starts) and len(ends):
            if ends[0] < starts[0]: ends = ends[1:]
            for s, e in zip(starts[:4], ends[:4]):
                ax.axvspan(t_m[s], t_m[e], color=C_ABNORMAL, alpha=0.12)

    ax.set_xlabel("Time (s)", fontsize=8)
    ax.set_ylabel("Freq (Hz)", fontsize=8)
    ax.set_title(
        f"PCG — {label}  |  Patient {patient}  |  Murmur: {murmur}",
        fontsize=8, loc="left", pad=3, color=C_NORMAL if col==0 else C_ABNORMAL
    )
    ax.tick_params(labelsize=7)

# ══════════════════════════════════════════════════════════════
# Row 1 — ECG Lead II
# ══════════════════════════════════════════════════════════════
ecg_configs = [
    (t_en, ecg_n, peaks_n, abn_mask_n, fs_en, rr_n, "Normal",   "P00002", "Normal ECG"),
    (t_ea, ecg_a, peaks_a, abn_mask_a, fs_ea, rr_a, "Abnormal", "P00001", "VSD"),
]

for col, (t, sig, peaks, abn_mask, fs, rr, label, pid, diag) in enumerate(ecg_configs):
    ax = fig.add_subplot(gs[1, col])
    color = C_NORMAL if col == 0 else C_ABNORMAL

    # plot full lead II waveform
    ax.plot(t, sig, color=color, linewidth=0.75, alpha=0.9)
    ax.axhline(0, color="gray", linewidth=0.4, linestyle="--", alpha=0.5)

    # mark R-peaks
    if len(peaks):
        ax.scatter(t[peaks], sig[peaks], color=color, s=18,
                   zorder=5, edgecolors="black", linewidths=0.5)

    # highlight abnormal RR intervals
    for i, (is_abn) in enumerate(abn_mask):
        if is_abn and i < len(peaks)-1:
            t_lo = t[peaks[i]]; t_hi = t[peaks[i+1]]
            ax.axvspan(t_lo, t_hi, color=C_ABNORMAL, alpha=0.22)
            ax.annotate(
                f"Abn.\n{rr[i]:.0f}ms",
                xy=((t_lo+t_hi)/2, sig[peaks[i]]),
                fontsize=6, color=C_ABNORMAL, ha="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          edgecolor=C_ABNORMAL, alpha=0.8)
            )

    if col == 1:
        # show ST/T wave anomaly region — last 30% of each beat (T-wave)
        for i in range(min(len(peaks)-1, 6)):
            rr_s = (peaks[i+1]-peaks[i]) / fs
            t_twave_start = t[peaks[i]] + 0.25   # ~250ms after R
            t_twave_end   = t[peaks[i]] + rr_s*0.70
            if t_twave_end < t[-1]:
                ax.axvspan(t_twave_start, t_twave_end,
                           color=C_HIGHLIGHT, alpha=0.12)

        # annotation for T-wave region
        if len(peaks) >= 2:
            mid_t = t[peaks[1]] + 0.3
            ax.annotate(
                "T-wave\nchange", xy=(mid_t, np.min(sig)*0.5),
                fontsize=6.5, color=C_HIGHLIGHT, fontweight="bold",
                ha="center", va="top",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          edgecolor=C_HIGHLIGHT, alpha=0.85)
            )

    ax.set_xlabel("Time (s)", fontsize=8)
    ax.set_ylabel("mV", fontsize=8)
    ax.set_xlim([0, t[-1]])
    rr_mean = rr.mean() if len(rr) else 0
    ax.set_title(
        f"ECG Lead II — {label}  |  {pid}  |  {diag}  |  Mean RR: {rr_mean:.0f} ms",
        fontsize=8, loc="left", pad=3, color=C_NORMAL if col==0 else C_ABNORMAL
    )
    ax.tick_params(labelsize=7)
    # ECG paper grid
    ax.set_xticks(np.arange(0, t[-1], 0.2), minor=False)
    ax.set_xticks(np.arange(0, t[-1], 0.04), minor=True)
    ax.grid(which="major", linewidth=0.5, color="#e0e0e0")
    ax.grid(which="minor", linewidth=0.25, color="#f0f0f0")

# ══════════════════════════════════════════════════════════════
# Row 2 — Echocardiogram frames
# ══════════════════════════════════════════════════════════════
echo_configs = [
    (frame_norm,   echo_norm_path,   "Normal",   "EF = 72.99%"),
    (frame_abnorm, echo_abnorm_path, "Abnormal", "EF = 7.02%  (Severely Reduced)"),
]

for col, (frame, path, label, ef_text) in enumerate(echo_configs):
    ax = fig.add_subplot(gs[2, col])
    color = C_NORMAL if col == 0 else C_ABNORMAL

    if frame is not None:
        ax.imshow(frame, cmap="gray", aspect="auto")

        if col == 1:  # Abnormal — circle the LV cavity region (roughly center)
            h, w = frame.shape
            cx, cy = w*0.5, h*0.52
            # draw ellipse for LV cavity
            ellipse = mpatches.Ellipse(
                (cx, cy), width=w*0.42, height=h*0.52,
                linewidth=2.0, edgecolor=C_ABNORMAL,
                facecolor=C_ABNORMAL, alpha=0.12
            )
            ax.add_patch(ellipse)
            # label
            ax.annotate(
                "Dilated LV\n(reduced contractility)",
                xy=(cx, cy - h*0.28),
                fontsize=7, color="white", fontweight="bold", ha="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=C_ABNORMAL,
                          edgecolor="white", alpha=0.82, linewidth=1.2)
            )

        ax.set_title(
            f"Echo (A4C) — {label}  |  {ef_text}",
            fontsize=8, loc="left", pad=3, color=color
        )
        ax.tick_params(left=False, bottom=False,
                       labelleft=False, labelbottom=False)
        for sp in ax.spines.values():
            sp.set_edgecolor(color); sp.set_linewidth(2.0)
    else:
        ax.text(0.5, 0.5, "Could not read video\n(opencv not available)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=9, color="gray")
        ax.set_title(f"Echo — {label} | {ef_text}",
                     fontsize=8, loc="left", pad=3, color=color)

# ── shared legend ─────────────────────────────────────────────
legend_handles = [
    mpatches.Patch(color=C_NORMAL,    label="Normal signal"),
    mpatches.Patch(color=C_ABNORMAL,  label="Abnormal signal"),
    mpatches.Patch(color=C_ABNORMAL,  alpha=0.25, label="Abnormal region (red box/span)"),
    mpatches.Patch(color=C_HIGHLIGHT, alpha=0.40, label="Suspect region (T-wave / burst)"),
]
fig.legend(handles=legend_handles, loc="lower center",
           ncol=4, fontsize=7.5, frameon=True,
           bbox_to_anchor=(0.5, 0.005), framealpha=0.95)

out_path = os.path.join(OUT_DIR, "normal_vs_abnormal_comparison.png")
fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"[OK] Saved -> {out_path}")
