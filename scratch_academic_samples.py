import os
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Paths
PCG_DIR = os.path.join('outputs', 'processed', 'pcg')
ECG_DIR = os.path.join('outputs', 'processed', 'ecg')
ECHO_DIR = os.path.join('outputs', 'processed', 'echo')
OUT_DIR = r"C:\Users\allan\.gemini\antigravity-ide\brain\a41cc8a6-5b69-4f50-bbf9-a6d42c89dfec"

# Academic styling
plt.style.use('default')
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
})

def plot_pcg_academic():
    print("Plotting PCG...")
    specs = torch.load(os.path.join(PCG_DIR, 'spectrograms.pt'), weights_only=True, map_location='cpu')
    labels = torch.load(os.path.join(PCG_DIR, 'labels.pt'), weights_only=True, map_location='cpu')
    
    n_idx = (labels == 0).nonzero(as_tuple=True)[0][0].item()
    a_idx = (labels == 1).nonzero(as_tuple=True)[0][0].item()
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # Normal
    im1 = axes[0].imshow(specs[n_idx].numpy(), aspect='auto', origin='lower', cmap='viridis')
    axes[0].set_title('Normal PCG Mel-Spectrogram')
    axes[0].set_xlabel('Time Frame')
    axes[0].set_ylabel('Mel Bin')
    plt.colorbar(im1, ax=axes[0])
    
    # Abnormal
    im2 = axes[1].imshow(specs[a_idx].numpy(), aspect='auto', origin='lower', cmap='viridis')
    axes[1].set_title('Abnormal PCG Mel-Spectrogram (Murmur)')
    axes[1].set_xlabel('Time Frame')
    axes[1].set_ylabel('Mel Bin')
    plt.colorbar(im2, ax=axes[1])
    
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'academic_pcg_sample.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_ecg_academic():
    print("Plotting ECG...")
    sigs = torch.load(os.path.join(ECG_DIR, 'ecg_signals.pt'), weights_only=True, map_location='cpu')
    labels = torch.load(os.path.join(ECG_DIR, 'labels.pt'), weights_only=True, map_location='cpu')
    
    n_idx = (labels == 0).nonzero(as_tuple=True)[0][5].item()
    a_idx = (labels == 1).nonzero(as_tuple=True)[0][5].item()
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    lead_names = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V4', 'V6']
    t = np.arange(2500) / 500.0  # 5 seconds
    
    # Normal
    ecg_n = sigs[n_idx].numpy()
    for lead in range(9):
        offset = lead * 2.5
        axes[0].plot(t, ecg_n[lead, :2500] + offset, color='black', linewidth=0.8)
        axes[0].text(-0.1, offset, lead_names[lead], ha='right', va='center')
        
    axes[0].set_title('Normal 9-Lead ECG')
    axes[0].set_ylabel('Amplitude (normalized)')
    axes[0].grid(True, linestyle=':', alpha=0.6)
    
    # Abnormal
    ecg_a = sigs[a_idx].numpy()
    for lead in range(9):
        offset = lead * 2.5
        axes[1].plot(t, ecg_a[lead, :2500] + offset, color='black', linewidth=0.8)
        axes[1].text(-0.1, offset, lead_names[lead], ha='right', va='center')
        
    axes[1].set_title('Abnormal 9-Lead ECG (CVD)')
    axes[1].set_xlabel('Time (seconds)')
    axes[1].set_ylabel('Amplitude (normalized)')
    axes[1].set_xlim(0, 5)
    axes[1].grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'academic_ecg_sample.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_echo_academic():
    print("Plotting Echo...")
    frames = torch.load(os.path.join(ECHO_DIR, 'ed_es_frames.pt'), weights_only=True, map_location='cpu')
    labels = torch.load(os.path.join(ECHO_DIR, 'labels.pt'), weights_only=True, map_location='cpu')
    
    n_idx = (labels == 0).nonzero(as_tuple=True)[0][0].item()
    a_idx = (labels == 1).nonzero(as_tuple=True)[0][0].item()
    
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    
    # Normal
    axes[0].imshow(frames[n_idx][0].numpy(), cmap='gray')
    axes[0].set_title('Normal Echocardiogram (ED Frame)')
    axes[0].axis('off')
    
    # Abnormal
    axes[1].imshow(frames[a_idx][0].numpy(), cmap='gray')
    axes[1].set_title('Reduced EF Echocardiogram (ED Frame)')
    axes[1].axis('off')
    
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'academic_echo_sample.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

if __name__ == '__main__':
    plot_pcg_academic()
    plot_ecg_academic()
    plot_echo_academic()
    print("Done!")
