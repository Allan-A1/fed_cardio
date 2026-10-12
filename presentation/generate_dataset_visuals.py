"""
Generate real dataset visualizations for the presentation.
Loads actual data from all 3 modalities and creates publication-quality plots.
"""

import os
import sys
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')

# Paths
PCG_DIR = os.path.join('outputs', 'processed', 'pcg')
ECG_DIR = os.path.join('outputs', 'processed', 'ecg')
ECHO_DIR = os.path.join('outputs', 'processed', 'echo')
OUT_DIR = os.path.join('presentation', 'figures')
os.makedirs(OUT_DIR, exist_ok=True)

# ── Dark theme setup ────────────────────────────────────────────────────
BG_COLOR = '#0a0f1a'
CARD_COLOR = '#111827'
TEXT_COLOR = '#e2e8f0'
TEXT_MUTED = '#94a3b8'
GRID_COLOR = '#1e293b'
TEAL = '#06b6d4'
ORANGE = '#f97316'
PURPLE = '#a855f7'
GREEN = '#34d399'
RED = '#f87171'
YELLOW = '#fbbf24'

plt.rcParams.update({
    'figure.facecolor': BG_COLOR,
    'axes.facecolor': CARD_COLOR,
    'axes.edgecolor': GRID_COLOR,
    'axes.labelcolor': TEXT_MUTED,
    'text.color': TEXT_COLOR,
    'xtick.color': TEXT_MUTED,
    'ytick.color': TEXT_MUTED,
    'grid.color': GRID_COLOR,
    'grid.alpha': 0.3,
    'font.family': 'sans-serif',
    'font.size': 11,
})


def plot_pcg_spectrograms(spectrograms, labels):
    """Plot sample PCG mel-spectrograms — Normal vs Abnormal."""
    print("  Plotting PCG spectrograms...")

    # Find one Normal and one Abnormal
    normal_idx = (labels == 0).nonzero(as_tuple=True)[0][:3]
    abnormal_idx = (labels == 1).nonzero(as_tuple=True)[0][:3]

    fig, axes = plt.subplots(2, 3, figsize=(16, 7))
    fig.suptitle('PCG Mel-Spectrograms — CirCor DigiScope (Hospital A)',
                 fontsize=16, fontweight='bold', color=TEAL, y=0.98)

    for i, idx in enumerate(normal_idx):
        spec = spectrograms[idx].numpy()
        im = axes[0, i].imshow(spec, aspect='auto', origin='lower',
                               cmap='viridis', interpolation='bilinear')
        axes[0, i].set_title(f'Normal (#{idx.item()})', fontsize=11, color=GREEN, fontweight='600')
        axes[0, i].set_ylabel('Mel Bin' if i == 0 else '', fontsize=10)
        axes[0, i].set_xlabel('Time Frame', fontsize=10)

    for i, idx in enumerate(abnormal_idx):
        spec = spectrograms[idx].numpy()
        im = axes[1, i].imshow(spec, aspect='auto', origin='lower',
                               cmap='magma', interpolation='bilinear')
        axes[1, i].set_title(f'Abnormal (#{idx.item()})', fontsize=11, color=RED, fontweight='600')
        axes[1, i].set_ylabel('Mel Bin' if i == 0 else '', fontsize=10)
        axes[1, i].set_xlabel('Time Frame', fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    path = os.path.join(OUT_DIR, 'pcg_spectrograms_real.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    Saved: {path}")


def plot_ecg_signals(signals, labels):
    """Plot sample ECG multi-lead signals — Normal vs Abnormal."""
    print("  Plotting ECG signals...")

    normal_idx = (labels == 0).nonzero(as_tuple=True)[0]
    abnormal_idx = (labels == 1).nonzero(as_tuple=True)[0]

    # Pick one of each
    n_idx = normal_idx[5].item()
    a_idx = abnormal_idx[5].item()

    fig, axes = plt.subplots(2, 1, figsize=(16, 8))
    fig.suptitle('9-Lead Pediatric ECG Signals — ZZU-pECG (Hospital B)',
                 fontsize=16, fontweight='bold', color=ORANGE, y=0.98)

    lead_names = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V4', 'V6']
    colors_n = plt.cm.cool(np.linspace(0.2, 0.9, 9))
    colors_a = plt.cm.autumn(np.linspace(0.2, 0.9, 9))

    # Normal
    ecg_normal = signals[n_idx].numpy()  # (9, 5000)
    time_axis = np.arange(ecg_normal.shape[1]) / 500.0  # 500 Hz

    for lead in range(min(9, ecg_normal.shape[0])):
        offset = lead * 2.5
        axes[0].plot(time_axis, ecg_normal[lead] + offset,
                     color=colors_n[lead], linewidth=0.6, alpha=0.9)
        axes[0].text(-0.15, offset, lead_names[lead] if lead < len(lead_names) else f'L{lead}',
                     fontsize=8, color=TEXT_MUTED, ha='right', va='center',
                     transform=axes[0].get_yaxis_transform())

    axes[0].set_title(f'Normal ECG (Patient #{n_idx})', fontsize=13, color=GREEN, fontweight='600')
    axes[0].set_xlabel('Time (seconds)', fontsize=10)
    axes[0].set_ylabel('Amplitude (normalized)', fontsize=10)
    axes[0].set_xlim(0, min(5, time_axis[-1]))  # Show first 5 seconds
    axes[0].grid(True, alpha=0.15)

    # Abnormal
    ecg_abnormal = signals[a_idx].numpy()
    time_axis_a = np.arange(ecg_abnormal.shape[1]) / 500.0

    for lead in range(min(9, ecg_abnormal.shape[0])):
        offset = lead * 2.5
        axes[1].plot(time_axis_a, ecg_abnormal[lead] + offset,
                     color=colors_a[lead], linewidth=0.6, alpha=0.9)
        axes[1].text(-0.15, offset, lead_names[lead] if lead < len(lead_names) else f'L{lead}',
                     fontsize=8, color=TEXT_MUTED, ha='right', va='center',
                     transform=axes[1].get_yaxis_transform())

    axes[1].set_title(f'Abnormal ECG (Patient #{a_idx})', fontsize=13, color=RED, fontweight='600')
    axes[1].set_xlabel('Time (seconds)', fontsize=10)
    axes[1].set_ylabel('Amplitude (normalized)', fontsize=10)
    axes[1].set_xlim(0, min(5, time_axis_a[-1]))
    axes[1].grid(True, alpha=0.15)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    path = os.path.join(OUT_DIR, 'ecg_signals_real.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    Saved: {path}")


def plot_echo_frames(frames, labels):
    """Plot sample Echo ED/ES frame pairs — Normal vs Reduced EF."""
    print("  Plotting Echo frames...")

    normal_idx = (labels == 0).nonzero(as_tuple=True)[0]
    abnormal_idx = (labels == 1).nonzero(as_tuple=True)[0]

    n_samples = min(4, len(normal_idx))
    a_samples = min(4, len(abnormal_idx))

    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    fig.suptitle('Echocardiogram ED/ES Frames — EchoNet-Pediatric (Hospital C)',
                 fontsize=16, fontweight='bold', color=PURPLE, y=0.98)

    # Normal pairs
    for i in range(n_samples):
        idx = normal_idx[i * 10].item()  # Skip some for variety
        frame_pair = frames[idx].numpy()  # (2, H, W) — ED and ES

        # Combine ED and ES side by side, or show ED only
        if frame_pair.shape[0] >= 2:
            ed_frame = frame_pair[0]
            es_frame = frame_pair[1]
        else:
            ed_frame = frame_pair[0]
            es_frame = frame_pair[0]

        # Show ED frame
        if i < 2:
            axes[0, i].imshow(ed_frame, cmap='gray', interpolation='bilinear')
            axes[0, i].set_title(f'Normal ED (#{idx})', fontsize=10, color=GREEN, fontweight='600')
        else:
            axes[0, i].imshow(es_frame, cmap='gray', interpolation='bilinear')
            axes[0, i].set_title(f'Normal ES (#{idx})', fontsize=10, color=GREEN, fontweight='600')
        axes[0, i].axis('off')

    # Abnormal pairs
    for i in range(a_samples):
        idx = abnormal_idx[min(i * 5, len(abnormal_idx)-1)].item()
        frame_pair = frames[idx].numpy()

        if frame_pair.shape[0] >= 2:
            ed_frame = frame_pair[0]
            es_frame = frame_pair[1]
        else:
            ed_frame = frame_pair[0]
            es_frame = frame_pair[0]

        if i < 2:
            axes[1, i].imshow(ed_frame, cmap='gray', interpolation='bilinear')
            axes[1, i].set_title(f'Reduced EF - ED (#{idx})', fontsize=10, color=RED, fontweight='600')
        else:
            axes[1, i].imshow(es_frame, cmap='gray', interpolation='bilinear')
            axes[1, i].set_title(f'Reduced EF - ES (#{idx})', fontsize=10, color=RED, fontweight='600')
        axes[1, i].axis('off')

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    path = os.path.join(OUT_DIR, 'echo_frames_real.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    Saved: {path}")


def plot_label_distributions(pcg_labels, ecg_labels, echo_labels):
    """Plot class distributions across all 3 datasets."""
    print("  Plotting label distributions...")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('Class Distribution Across All 3 Datasets',
                 fontsize=16, fontweight='bold', color=TEXT_COLOR, y=1.02)

    datasets = [
        ('CirCor DigiScope (PCG)', pcg_labels, TEAL, ['Normal', 'Abnormal']),
        ('ZZU-pECG (ECG)', ecg_labels, ORANGE, ['Normal', 'Abnormal']),
        ('EchoNet-Pediatric (Echo)', echo_labels, PURPLE, ['Normal', 'Reduced EF']),
    ]

    for i, (name, labels, color, class_names) in enumerate(datasets):
        counts = [(labels == 0).sum().item(), (labels == 1).sum().item()]
        total = sum(counts)
        bars = axes[i].bar(class_names, counts,
                          color=[GREEN, RED],
                          edgecolor='none', width=0.6, alpha=0.85)

        # Add value labels
        for bar, count in zip(bars, counts):
            pct = count / total * 100
            axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + total*0.02,
                        f'{count:,}\n({pct:.1f}%)',
                        ha='center', va='bottom', fontsize=10, color=TEXT_COLOR,
                        fontweight='600')

        axes[i].set_title(name, fontsize=13, color=color, fontweight='700', pad=12)
        axes[i].set_ylabel('Sample Count' if i == 0 else '', fontsize=10)
        axes[i].spines['top'].set_visible(False)
        axes[i].spines['right'].set_visible(False)
        axes[i].grid(axis='y', alpha=0.15)
        axes[i].set_ylim(0, max(counts) * 1.25)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'label_distributions.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    Saved: {path}")


def plot_combined_dashboard(pcg_specs, pcg_labels, ecg_sigs, ecg_labels, echo_frames, echo_labels):
    """Create a single combined dashboard showing one sample from each modality."""
    print("  Plotting combined dashboard...")

    fig = plt.figure(figsize=(18, 10))
    fig.suptitle('CrossFedProto — Real Dataset Samples From 3 Modalities',
                 fontsize=18, fontweight='bold', color=TEXT_COLOR, y=0.98)

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    # ── PCG: Spectrogram ──
    ax1 = fig.add_subplot(gs[0, 0])
    n_idx = (pcg_labels == 0).nonzero(as_tuple=True)[0][10].item()
    spec = pcg_specs[n_idx].numpy()
    ax1.imshow(spec, aspect='auto', origin='lower', cmap='viridis', interpolation='bilinear')
    ax1.set_title('Hospital A — PCG Mel-Spectrogram', fontsize=12, color=TEAL, fontweight='700')
    ax1.set_xlabel('Time Frame', fontsize=9)
    ax1.set_ylabel('Mel Bin', fontsize=9)

    ax2 = fig.add_subplot(gs[1, 0])
    a_idx = (pcg_labels == 1).nonzero(as_tuple=True)[0][10].item()
    spec_a = pcg_specs[a_idx].numpy()
    ax2.imshow(spec_a, aspect='auto', origin='lower', cmap='magma', interpolation='bilinear')
    ax2.set_title('Abnormal Heart Sound', fontsize=11, color=RED, fontweight='600')
    ax2.set_xlabel('Time Frame', fontsize=9)
    ax2.set_ylabel('Mel Bin', fontsize=9)

    # ── ECG: Multi-lead ──
    ax3 = fig.add_subplot(gs[0, 1])
    ecg_n = ecg_sigs[(ecg_labels == 0).nonzero(as_tuple=True)[0][3].item()].numpy()
    lead_names = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V4', 'V6']
    t = np.arange(min(2500, ecg_n.shape[1])) / 500.0

    for lead in range(min(9, ecg_n.shape[0])):
        offset = lead * 2.0
        ax3.plot(t, ecg_n[lead, :len(t)] + offset,
                color=plt.cm.cool(lead / 9), linewidth=0.5, alpha=0.85)

    ax3.set_title('Hospital B — Normal 9-Lead ECG', fontsize=12, color=ORANGE, fontweight='700')
    ax3.set_xlabel('Time (s)', fontsize=9)
    ax3.set_xlim(0, 5)
    ax3.grid(True, alpha=0.1)

    ax4 = fig.add_subplot(gs[1, 1])
    ecg_a = ecg_sigs[(ecg_labels == 1).nonzero(as_tuple=True)[0][3].item()].numpy()

    for lead in range(min(9, ecg_a.shape[0])):
        offset = lead * 2.0
        ax4.plot(t, ecg_a[lead, :len(t)] + offset,
                color=plt.cm.autumn(lead / 9), linewidth=0.5, alpha=0.85)

    ax4.set_title('Abnormal ECG (CVD)', fontsize=11, color=RED, fontweight='600')
    ax4.set_xlabel('Time (s)', fontsize=9)
    ax4.set_xlim(0, 5)
    ax4.grid(True, alpha=0.1)

    # ── Echo: ED/ES Frames ──
    ax5 = fig.add_subplot(gs[0, 2])
    echo_n = echo_frames[(echo_labels == 0).nonzero(as_tuple=True)[0][20].item()].numpy()
    ax5.imshow(echo_n[0], cmap='gray', interpolation='bilinear')
    ax5.set_title('Hospital C — Normal Echo (ED)', fontsize=12, color=PURPLE, fontweight='700')
    ax5.axis('off')

    ax6 = fig.add_subplot(gs[1, 2])
    echo_a_idx = (echo_labels == 1).nonzero(as_tuple=True)[0]
    echo_a = echo_frames[echo_a_idx[min(5, len(echo_a_idx)-1)].item()].numpy()
    ax6.imshow(echo_a[0], cmap='gray', interpolation='bilinear')
    ax6.set_title('Reduced EF Echo (ED)', fontsize=11, color=RED, fontweight='600')
    ax6.axis('off')

    path = os.path.join(OUT_DIR, 'dataset_dashboard_real.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    Saved: {path}")


def plot_results_comparison():
    """Plot solo vs federated results bar chart."""
    print("  Plotting results comparison...")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    fig.suptitle('Solo Baseline vs. CrossFedProto — Test Set Metrics',
                 fontsize=16, fontweight='bold', color=TEXT_COLOR, y=1.02)

    metrics = ['AUROC', 'Sensitivity', 'Specificity']
    solo = {
        'PCG': [0.9196, 0.8262, 0.8573],
        'ECG': [0.9461, 0.8878, 0.8581],
        'Echo': [0.8280, 0.4459, 0.9712],
    }
    fed = {
        'PCG': [0.9170, 0.8946, 0.6873],
        'ECG': [0.9594, 0.8689, 0.9268],
        'Echo': [0.8267, 0.4324, 0.9663],
    }
    colors_map = {'PCG': TEAL, 'ECG': ORANGE, 'Echo': PURPLE}

    for i, metric in enumerate(metrics):
        modalities = list(solo.keys())
        x = np.arange(len(modalities))
        width = 0.35

        solo_vals = [solo[m][i] for m in modalities]
        fed_vals = [fed[m][i] for m in modalities]

        bars1 = axes[i].bar(x - width/2, solo_vals, width,
                           label='Solo Baseline', color='#475569',
                           edgecolor='none', alpha=0.7)
        bars2 = axes[i].bar(x + width/2, fed_vals, width,
                           label='CrossFedProto',
                           color=[colors_map[m] for m in modalities],
                           edgecolor='none', alpha=0.9)

        # Value labels
        for bar, val in zip(bars1, solo_vals):
            axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{val:.3f}', ha='center', va='bottom', fontsize=8.5,
                        color=TEXT_MUTED, fontweight='500')
        for bar, val in zip(bars2, fed_vals):
            axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{val:.3f}', ha='center', va='bottom', fontsize=8.5,
                        color=TEXT_COLOR, fontweight='700')

        axes[i].set_title(metric, fontsize=14, fontweight='700', pad=10)
        axes[i].set_xticks(x)
        axes[i].set_xticklabels(modalities, fontsize=11)
        axes[i].set_ylim(0, 1.12)
        axes[i].spines['top'].set_visible(False)
        axes[i].spines['right'].set_visible(False)
        axes[i].grid(axis='y', alpha=0.15)

        if i == 0:
            axes[i].legend(loc='upper left', fontsize=9, framealpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'results_comparison.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    Saved: {path}")


def plot_prototype_convergence_custom():
    """Plot prototype alignment convergence from federation results."""
    print("  Plotting prototype convergence...")
    import json

    results_path = os.path.join('outputs', 'federation', 'results', 'federation_results.json')
    if not os.path.exists(results_path):
        print("    Skipping — federation results not found")
        return

    with open(results_path, 'r') as f:
        results = json.load(f)

    shifts = results['server_history']['proto_shift']
    # Replace 'inf' string with a large number
    shifts = [20.0 if s == 'inf' else float(s) for s in shifts]
    rounds = list(range(len(shifts)))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(rounds, shifts, color=TEAL, linewidth=2.5, marker='o', markersize=5,
            markerfacecolor=TEAL, markeredgecolor='white', markeredgewidth=1)
    ax.fill_between(rounds, shifts, alpha=0.15, color=TEAL)

    ax.set_title('Global Prototype Shift Over Federated Rounds',
                 fontsize=15, fontweight='bold', color=TEXT_COLOR)
    ax.set_xlabel('Round', fontsize=12)
    ax.set_ylabel('Prototype Shift (L2 distance)', fontsize=12)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.15)
    ax.axhline(y=0.01, color=GREEN, linestyle='--', alpha=0.5, linewidth=1)
    ax.text(len(rounds)-1, 0.012, 'Convergence threshold', fontsize=9,
            color=GREEN, ha='right', alpha=0.7)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    path = os.path.join(OUT_DIR, 'prototype_shift.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    Saved: {path}")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Generating Real Dataset Visualizations")
    print("=" * 60)

    # ── Load processed data ──
    print("\n[1] Loading PCG spectrograms...")
    pcg_specs = torch.load(os.path.join(PCG_DIR, 'spectrograms.pt'), weights_only=True, map_location='cpu')
    pcg_labels = torch.load(os.path.join(PCG_DIR, 'labels.pt'), weights_only=True, map_location='cpu')
    print(f"    PCG: {pcg_specs.shape} spectrograms, {pcg_labels.shape} labels")
    print(f"    Normal: {(pcg_labels==0).sum().item()}, Abnormal: {(pcg_labels==1).sum().item()}")

    print("\n[2] Loading ECG signals...")
    ecg_sigs = torch.load(os.path.join(ECG_DIR, 'ecg_signals.pt'), weights_only=True, map_location='cpu')
    ecg_labels = torch.load(os.path.join(ECG_DIR, 'labels.pt'), weights_only=True, map_location='cpu')
    print(f"    ECG: {ecg_sigs.shape} signals, {ecg_labels.shape} labels")
    print(f"    Normal: {(ecg_labels==0).sum().item()}, Abnormal: {(ecg_labels==1).sum().item()}")

    print("\n[3] Loading Echo frames...")
    echo_frames = torch.load(os.path.join(ECHO_DIR, 'ed_es_frames.pt'), weights_only=True, map_location='cpu')
    echo_labels = torch.load(os.path.join(ECHO_DIR, 'labels.pt'), weights_only=True, map_location='cpu')
    print(f"    Echo: {echo_frames.shape} frames, {echo_labels.shape} labels")
    print(f"    Normal: {(echo_labels==0).sum().item()}, Reduced EF: {(echo_labels==1).sum().item()}")

    # ── Generate visualizations ──
    print("\n[4] Generating visualizations...\n")

    plot_pcg_spectrograms(pcg_specs, pcg_labels)
    plot_ecg_signals(ecg_sigs, ecg_labels)
    plot_echo_frames(echo_frames, echo_labels)
    plot_label_distributions(pcg_labels, ecg_labels, echo_labels)
    plot_combined_dashboard(pcg_specs, pcg_labels, ecg_sigs, ecg_labels, echo_frames, echo_labels)
    plot_results_comparison()
    plot_prototype_convergence_custom()

    print(f"\n{'=' * 60}")
    print(f"  Done! All figures saved to: {OUT_DIR}/")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
