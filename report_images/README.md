# 📁 FedCardio Report Images Catalog

This directory contains all high-resolution figures, waveforms, dashboards, convergence plots, and confusion matrices generated for the **FedCardio B.Tech Project Report** (`report.tex`).

---

## 🖼️ Primary Figures Embedded in `report.tex`

| # | Filename | Description | Chapter / Section |
|---|---|---|---|
| 1 | `combined_pcg_ecg_overview.png` | Physiological signal comparison: PCG heart sounds & multi-lead ECG traces | Chapter 1 (Clinical Screening Modalities) |
| 2 | `echo_ed_es_ef_explained.png` | Echocardiogram End-Diastole (ED) / End-Systole (ES) frames and LVEF calculation | Chapter 1 (Echocardiography) |
| 3 | `federation_dashboard.png` | FedCardio Cross-Modal System Architecture & Federation Topology | Chapter 3 (System Design Overview) |
| 4 | `normal_vs_abnormal_comparison.png` | Normal vs. Abnormal acoustic & electrical waveform comparisons | Chapter 4 (Dataset Preprocessing) |
| 5 | `12_grand_summary_dashboard.png` | Grand summary clinical screening and federated telemetry platform dashboard | Chapter 4 (Full-Stack Platform) |
| 6 | `federation_auroc_curves.png` | Multi-round validation AUROC curves vs. isolated single-center baselines | Chapter 5 (Overall Performance) |
| 7 | `prototype_convergence.png` | Prototype cosine distance convergence over 30 federated rounds (<0.001) | Chapter 5 (Representation Alignment) |
| 8 | `embedding_tsne.png` | t-SNE latent manifold visualization: cross-modal alignment without domain collapse | Chapter 5 (Latent Space Alignment) |
| 9 | `federation_loss_breakdown.png` | Decomposition of local losses ($\mathcal{L}_{\text{CE}}$, $\mathcal{L}_{\text{proto}}$, $\mathcal{L}_{\text{contrast}}$) | Chapter 5 (Ablation Analysis) |
| 10 | `10_youden_threshold.png` | Youden's $J$ statistic curve across operating decision thresholds | Chapter 5 (Threshold Optimization) |
| 11 | `03_metric_comparison.png` | Comparative multi-metric bar chart (AUROC, Accuracy, F1, F2, MCC) | Chapter 5 (Extended Evaluation) |
| 12 | `04_confusion_matrices.png` | Test set confusion matrix heatmaps (Solo Baseline vs. CrossFedProto) | Chapter 5 (Confusion Analysis) |

---

## 📊 Extended Diagnostic & Analytical Figures

These additional figures are available for presentations, slides, and viva examination defense:

| # | Filename | Description |
|---|---|---|
| 13 | `01_roc_curves.png` | High-resolution Receiver Operating Characteristic (ROC) curves with AUC shading |
| 14 | `02_pr_curves.png` | Precision-Recall (PR) curves for evaluating imbalanced medical screening cohorts |
| 15 | `05_mcc_f1_f2.png` | Matthews Correlation Coefficient (MCC), F1-Score, and F2-Score progression |
| 16 | `06_dataset_statistics.png` | Multi-center dataset demographic distributions and class balance radar charts |
| 17 | `07_communication_efficiency.png` | Transmitted bandwidth comparison: FedCardio (512 bytes) vs. FedAvg (54.2 MB) |
| 18 | `08_federated_fairness.png` | Inter-client performance parity and federated fairness analysis |
| 19 | `09_radar_chart.png` | Holistic clinical radar comparison across Sensitivity, Specificity, AUROC, and MCC |
| 20 | `11_privacy_utility.png` | Privacy-utility trade-off curves under varying noise and differential privacy |
| 21 | `pcg_raw_waveforms.png` | Raw acoustic heart sound audio waveforms from the CirCor DigiScope dataset |
| 22 | `ecg_raw_waveforms.png` | Raw 9-lead pediatric electrocardiogram traces from the ZZU-pECG database |
| 23 | `pcg_baseline_curve.png` | Training loss and validation AUROC curve for isolated PCGNet baseline |
| 24 | `ecg_baseline_curve.png` | Training loss and validation AUROC curve for isolated ECGResNet baseline |
| 25 | `echo_baseline_curve.png` | Training loss and validation AUROC curve for isolated EchoNet baseline |
| 26 | `federation_sens_spec.png` | Sensitivity vs. Specificity trajectories over federated training rounds |

---

## 🚀 Usage in LaTeX
All figures can be included directly in `report.tex` with:
```latex
\includegraphics[width=0.9\linewidth]{report_images/<filename>.png}
```
Or, since `\graphicspath{{report_images/}{./}}` is set in the preamble:
```latex
\includegraphics[width=0.9\linewidth]{<filename>.png}
```
