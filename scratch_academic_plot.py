import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

# Data
datasets = ['CirCor DigiScope (PCG)', 'ZZU-pECG (ECG)', 'EchoNet-Pediatric (Echo)']
normal_counts = [8822, 2904, 2768]
abnormal_counts = [2340, 11286, 490]

# Standard academic styling
plt.style.use('default')
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(datasets))
width = 0.35

# Plot bars
rects1 = ax.bar(x - width/2, normal_counts, width, label='Normal', color='#2ca02c', edgecolor='black', linewidth=1)
rects2 = ax.bar(x + width/2, abnormal_counts, width, label='Abnormal', color='#d62728', edgecolor='black', linewidth=1)

# Formatting
ax.set_ylabel('Number of Samples', fontsize=12, fontweight='bold')
ax.set_title('Class Distribution Across Datasets', fontsize=14, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(datasets, fontsize=11)
ax.legend(fontsize=11)
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Add value labels
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:,}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

autolabel(rects1)
autolabel(rects2)

plt.tight_layout()

# Save locally to artifacts directory
out_path = r"C:\Users\allan\.gemini\antigravity-ide\brain\a41cc8a6-5b69-4f50-bbf9-a6d42c89dfec\academic_dataset_balance.png"
fig.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Saved plot to {out_path}")
