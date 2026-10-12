# -*- coding: utf-8 -*-
"""
ES / ED / EF Explanation Diagram
=================================
Visualizes what End-Systole, End-Diastole and Ejection Fraction mean,
using real frames from the EchoNet-Pediatric dataset.
"""

import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.patheffects as pe
import warnings
warnings.filterwarnings("ignore")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

OUT_DIR = r"d:\clg\project\fl_pediatric\outputs"
ECHO_DIR = r"d:\clg\project\fl_pediatric\datasets\EchoNet-Pediatric\echonetpediatric\pediatric_echo_avi\pediatric_echo_avi\A4C\Videos"

# ── sample video: EF=40.83%, frames 39(ED) and 27(ES) ──
VIDEO    = "CR32a7555-CR32a7582-000039.avi"
ED_FRAME = 39    # End-Diastole  (largest volume)
ES_FRAME = 27    # End-Systole   (smallest volume)
EF_VAL   = 40.83

# ═══════════════════════════════════════════════════════════════
# 1. Extract frames
# ═══════════════════════════════════════════════════════════════

def get_frame(video_path, frame_idx):
    if HAS_CV2:
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return None

video_path = os.path.join(ECHO_DIR, VIDEO)
frame_ed = get_frame(video_path, ED_FRAME)
frame_es = get_frame(video_path, ES_FRAME)

# ═══════════════════════════════════════════════════════════════
# 2. Schematic cardiac cycle curve
# ═══════════════════════════════════════════════════════════════
# Simulate LV volume over time (one cardiac cycle)
t = np.linspace(0, 1.0, 500)

# Simplified LV volume waveform:
# stays high (diastole), then drops sharply (systole), returns
def lv_volume_curve(t, EDV=120, ESV=72):
    v = np.zeros_like(t)
    for i, ti in enumerate(t):
        if ti < 0.08:          # isovolumetric contraction
            v[i] = EDV
        elif ti < 0.38:        # ejection (systole)
            frac = (ti - 0.08) / 0.30
            v[i] = EDV - (EDV - ESV) * np.sin(frac * np.pi / 2)
        elif ti < 0.45:        # isovolumetric relaxation
            v[i] = ESV
        elif ti < 0.75:        # filling (diastole)
            frac = (ti - 0.45) / 0.30
            v[i] = ESV + (EDV - ESV) * np.sin(frac * np.pi / 2)
        else:
            v[i] = EDV
    return v

# EF=40.83% → ESV = EDV*(1-EF/100) = 120*(1-0.4083) = ~70.99
EDV = 120.0
ESV = EDV * (1 - EF_VAL / 100)
vol = lv_volume_curve(t, EDV=EDV, ESV=ESV)

t_ED = 0.0    # ED is at start (max volume)
t_ES = 0.38   # ES is at min volume

# ═══════════════════════════════════════════════════════════════
# 3. Build figure
# ═══════════════════════════════════════════════════════════════
plt.style.use("seaborn-v0_8-whitegrid")

fig = plt.figure(figsize=(13, 9), facecolor="white")
fig.suptitle(
    "Echocardiography: ED, ES & EF Explained",
    fontsize=14, fontweight="bold", y=0.99
)

gs_main = gridspec.GridSpec(2, 1, figure=fig,
                             hspace=0.45, top=0.94, bottom=0.04)

# ── Top half: schematic + heart cartoons ──
gs_top = gridspec.GridSpecFromSubplotSpec(
    1, 3, subplot_spec=gs_main[0], wspace=0.35
)

# -- panel A: LV volume curve ──────────────────────────────────
ax_curve = fig.add_subplot(gs_top[0:2])
ax_curve.set_facecolor("white")

ax_curve.plot(t, vol, color="#1565C0", linewidth=2.5, label="LV Volume")
ax_curve.fill_between(t, vol, EDV, alpha=0.08, color="#1565C0")

# shade systolic period
mask_sys = (t >= 0.08) & (t <= 0.45)
ax_curve.fill_between(t[mask_sys], vol[mask_sys], ESV,
                      alpha=0.20, color="#E53935", label="Ejected stroke volume")

# ED annotation
ax_curve.axvline(x=0.0, color="#2E7D32", linewidth=1.8, linestyle="--")
ax_curve.scatter([t_ED], [EDV], color="#2E7D32", s=80, zorder=6)
ax_curve.annotate(
    f"End-Diastole (ED)\nMax Volume = {EDV:.0f} mL",
    xy=(0.0, EDV), xytext=(0.07, EDV - 4),
    fontsize=8.5, color="#2E7D32", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=1.4)
)

# ES annotation
ax_curve.axvline(x=t_ES, color="#E53935", linewidth=1.8, linestyle="--")
ax_curve.scatter([t_ES], [ESV], color="#E53935", s=80, zorder=6)
ax_curve.annotate(
    f"End-Systole (ES)\nMin Volume = {ESV:.0f} mL",
    xy=(t_ES, ESV), xytext=(t_ES + 0.06, ESV + 8),
    fontsize=8.5, color="#E53935", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#E53935", lw=1.4)
)

# EF bracket
mid_t = (t_ED + t_ES) / 2 + 0.04
ax_curve.annotate(
    "", xy=(mid_t, EDV), xytext=(mid_t, ESV),
    arrowprops=dict(arrowstyle="<->", color="#7B1FA2", lw=2.0)
)
ax_curve.text(mid_t + 0.02, (EDV + ESV) / 2,
    f"Stroke\nVolume\n= {EDV-ESV:.0f} mL",
    fontsize=8, color="#7B1FA2", fontweight="bold", va="center")

# EF formula box
ef_text = (
    f"EF  =  (EDV – ESV) / EDV  ×  100\n"
    f"      =  ({EDV:.0f} – {ESV:.0f}) / {EDV:.0f}  ×  100\n"
    f"      =  {EF_VAL:.1f}%   ← Reduced (normal ≥ 55%)"
)
ax_curve.text(0.5, ESV - 8, ef_text,
    fontsize=8, color="#4A148C", va="top", ha="left",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#F3E5F5",
              edgecolor="#7B1FA2", linewidth=1.5, alpha=0.95)
)

ax_curve.set_xlabel("Time (cardiac cycle)", fontsize=9)
ax_curve.set_ylabel("LV Volume (mL)", fontsize=9)
ax_curve.set_xlim([-0.02, 1.02])
ax_curve.set_ylim([ESV - 22, EDV + 12])
ax_curve.set_title(
    "Left Ventricular Volume Over One Cardiac Cycle",
    fontsize=10, fontweight="bold", pad=5
)
ax_curve.legend(fontsize=8, loc="upper right")
ax_curve.set_xticks([0, 0.08, 0.38, 0.45, 0.75, 1.0],
    labels=["ED", "Contraction\nstarts", "ES", "Relaxation\nstarts", "Filling\nends", "ED"],
    fontsize=7)

# -- panel B: what phase labels mean ───────────────────────────
ax_def = fig.add_subplot(gs_top[2])
ax_def.axis("off")

defs = [
    ("ED", "End-Diastole",
     "#2E7D32",
     "The moment JUST BEFORE the\nheart contracts.\n\nVentricle is fully RELAXED\nand FILLED with blood.\n→ Largest volume (EDV).\n→ Captured at the echo frame\n   where LV is biggest."),
    ("ES", "End-Systole",
     "#E53935",
     "The moment JUST AFTER the\nheart finishes contracting.\n\nVentricle has SQUEEZED OUT\nblood into the aorta.\n→ Smallest volume (ESV).\n→ Captured at the echo frame\n   where LV is smallest."),
    ("EF", "Ejection Fraction",
     "#7B1FA2",
     "Percentage of blood pumped\nout per beat:\n\n  EF = (EDV-ESV)/EDV × 100\n\nNormal:  ≥ 55%\nMildly reduced:  40–54%\nModerately:  30–39%\nSeverely:  < 30%"),
]

y = 0.97
for abbr, full, color, desc in defs:
    ax_def.text(0.0, y, f"{abbr}", fontsize=14, fontweight="bold",
                color=color, transform=ax_def.transAxes, va="top")
    ax_def.text(0.20, y, f"— {full}", fontsize=9, fontweight="bold",
                color="black", transform=ax_def.transAxes, va="top")
    ax_def.text(0.0, y - 0.055, desc, fontsize=7.5, color="#37474F",
                transform=ax_def.transAxes, va="top",
                bbox=dict(boxstyle="round,pad=0.4", facecolor=color,
                          alpha=0.07, edgecolor=color, linewidth=1.2))
    y -= 0.34

ax_def.set_title("Definitions", fontsize=10, fontweight="bold", pad=5)

# ── Bottom half: actual echo frames ED vs ES ───────────────────
gs_bot = gridspec.GridSpecFromSubplotSpec(
    1, 2, subplot_spec=gs_main[1], wspace=0.15
)

frame_configs = [
    (frame_ed, ED_FRAME, "End-Diastole (ED)", "#2E7D32",
     f"LV at MAXIMUM volume\nEDV ≈ {EDV:.0f} mL\n(Frame #{ED_FRAME} in video)"),
    (frame_es, ES_FRAME, "End-Systole (ES)", "#E53935",
     f"LV at MINIMUM volume\nESV ≈ {ESV:.0f} mL\n(Frame #{ES_FRAME} in video)"),
]

for col, (frame, fr_idx, title, color, note) in enumerate(frame_configs):
    ax = fig.add_subplot(gs_bot[col])

    if frame is not None:
        ax.imshow(frame, cmap="gray", aspect="auto")
        h, w = frame.shape

        # Draw LV cavity outline (approximate ellipse)
        if col == 0:   # ED — bigger ellipse
            ell = mpatches.Ellipse(
                (w*0.50, h*0.52), w*0.46, h*0.56,
                linewidth=2.5, edgecolor=color,
                facecolor=color, alpha=0.12
            )
        else:          # ES — smaller ellipse
            ell = mpatches.Ellipse(
                (w*0.50, h*0.52), w*0.32, h*0.40,
                linewidth=2.5, edgecolor=color,
                facecolor=color, alpha=0.12
            )
        ax.add_patch(ell)

        # Label inside ellipse
        ax.text(w*0.50, h*0.52, "LV", fontsize=16, fontweight="bold",
                color=color, ha="center", va="center", alpha=0.85,
                path_effects=[pe.withStroke(linewidth=3, foreground="white")])

        # Note box at bottom
        ax.text(w*0.50, h*0.92, note,
                fontsize=7.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor=color, alpha=0.92, linewidth=1.5),
                color="#212121")

    ax.set_title(
        f"{title}\n(Patient: {VIDEO[:12]}…  EF={EF_VAL}%)",
        fontsize=9, fontweight="bold", color=color, pad=4
    )
    for sp in ax.spines.values():
        sp.set_edgecolor(color); sp.set_linewidth(2.5)
    ax.tick_params(left=False, bottom=False,
                   labelleft=False, labelbottom=False)

# ── bottom caption ──────────────────────────────────────────────
fig.text(
    0.5, 0.005,
    "EchoNet-Pediatric dataset  |  A4C view (Apical 4-Chamber)  |  "
    f"Video: {VIDEO}  |  EF={EF_VAL}% (Reduced — normal ≥ 55%)",
    ha="center", fontsize=7.5, color="gray"
)

out_path = os.path.join(OUT_DIR, "echo_ed_es_ef_explained.png")
fig.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"[OK] Saved -> {out_path}")
