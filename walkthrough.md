# FedProto Pipeline — Walkthrough

## What Was Built

A complete **cross-modal federated prototype learning pipeline** that enables 3 hospitals with different cardiac modalities (PCG, ECG, Echo) to collaboratively improve their models **without sharing any patient data or model weights**.

---

## GPU Setup

| Item | Result |
|------|--------|
| GPU Detected | NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM) |
| Python | Downgraded venv from 3.14 → 3.12 (PyTorch CUDA wheels not yet available for 3.14) |
| PyTorch | `2.6.0+cu124` — CUDA 12.4 bundled, GPU fully active |

---

## Files Created (7 new, 0 modified)

### Federation Core (`src/federation/`)

| File | Purpose | Lines |
|------|---------|-------|
| [projection.py](file:///d:/clg/project/fl_pediatric/src/federation/projection.py) | `ProjectionHead` — maps 128-d native embedding → 64-d shared space (8,256 params) | 56 |
| [losses.py](file:///d:/clg/project/fl_pediatric/src/federation/losses.py) | `prototype_alignment_loss` (L2 pull) + `contrastive_prototype_loss` (InfoNCE push/pull) | 128 |
| [client.py](file:///d:/clg/project/fl_pediatric/src/federation/client.py) | `FederatedClient` — wraps model + proj_head + optimizer, handles local training & prototype computation | 268 |
| [server.py](file:///d:/clg/project/fl_pediatric/src/federation/server.py) | `FederatedServer` — weighted-average prototype aggregation, convergence tracking, alignment metrics | 192 |
| [federation_utils.py](file:///d:/clg/project/fl_pediatric/src/federation/federation_utils.py) | 6 visualization functions + JSON serialization + baseline comparison loader | 441 |
| [__init__.py](file:///d:/clg/project/fl_pediatric/src/federation/__init__.py) | Package exports | 25 |

### Pipeline Orchestrator

| File | Purpose | Lines |
|------|---------|-------|
| [run_federation.py](file:///d:/clg/project/fl_pediatric/src/run_federation.py) | Main entry point — complete training pipeline with early stopping, convergence detection, CLI flags | 529 |

**Total: ~1,639 lines of new code. Zero existing files modified.**

---

## Pipeline Flow

```
Round 0:  Warmup (CE only) → each client trains N epochs locally
          → compute initial projected prototypes → server aggregates

Rounds 1-N:
  For each client:
    1. Train locally with L_CE + lambda_proto * L_proto + lambda_contrast * L_contrast
    2. Compute projected prototypes (mean of proj_head(embedding) per class)
  
  Server:
    3. Weighted-average all client prototypes → global prototypes
    4. Broadcast global prototypes back to clients
  
  Evaluate:
    5. Val AUROC / Sensitivity / Specificity per client
    6. Check convergence (prototype shift < threshold for N rounds)
    7. Early stopping if avg AUROC plateaus

Final:
  8. Load best checkpoint per client → test evaluation
  9. Generate 6 visualization figures + results JSON
```

---

## Smoke Test Results

Ran with `--smoke_test --clients pcg,echo` (100 samples per client, 3 rounds, 1 epoch each):

| Metric | Result |
|--------|--------|
| Total time | **6 seconds** (on RTX 4050 GPU) |
| PCG Test AUROC | 0.8143 |
| Echo Test AUROC | 0.5286 |
| Proto alignment (cos_dist) | 1.03 → 0.04 (97% reduction in 3 rounds!) |
| All outputs generated | Yes (6 figures, 2 checkpoints, 1 JSON) |

---

## Generated Outputs

All saved to `outputs/federation/`:

```
outputs/federation/
├── checkpoints/
│   ├── pcg_federated_best.pt
│   └── echo_federated_best.pt
├── figures/
│   ├── federation_auroc_curves.png
│   ├── federation_loss_breakdown.png
│   ├── prototype_convergence.png
│   ├── federation_sens_spec.png
│   ├── embedding_tsne.png
│   └── federation_dashboard.png
├── results/
│   └── federation_results.json
└── logs/
    └── federation_log.txt
```

### Visualization Previews

````carousel
![AUROC curves over federation rounds](file:///d:/clg/project/fl_pediatric/outputs/federation/figures/federation_auroc_curves.png)
<!-- slide -->
![Loss component breakdown per client](file:///d:/clg/project/fl_pediatric/outputs/federation/figures/federation_loss_breakdown.png)
<!-- slide -->
![Prototype convergence analysis](file:///d:/clg/project/fl_pediatric/outputs/federation/figures/prototype_convergence.png)
<!-- slide -->
![Sensitivity and specificity over rounds](file:///d:/clg/project/fl_pediatric/outputs/federation/figures/federation_sens_spec.png)
<!-- slide -->
![t-SNE of projected embeddings in shared alignment space](file:///d:/clg/project/fl_pediatric/outputs/federation/figures/embedding_tsne.png)
<!-- slide -->
![Federation dashboard - all-in-one summary](file:///d:/clg/project/fl_pediatric/outputs/federation/figures/federation_dashboard.png)
````

---

## How to Run

```bash
# Quick smoke test (~6 seconds)
python -m src.run_federation --smoke_test

# Full run with all 3 clients (30 rounds x 5 epochs)
python -m src.run_federation

# Custom configuration
python -m src.run_federation --rounds 20 --local_epochs 3 --clients pcg,echo

# All available flags
python -m src.run_federation --help
```

---

## Key Design Decisions

1. **Classifier uses native 128-d embedding** — the projection head is a parallel, non-destructive addition. Local classification performance is NOT degraded.

2. **Cold-start** — federated training starts from random init (not from solo baselines) to cleanly isolate the federated learning effect.

3. **Early stopping on average AUROC** — stops when the mean val AUROC across all clients plateaus for 8 rounds.

4. **Convergence detection** — independently tracks prototype shift magnitude. When the global prototypes stop moving (shift < 0.01 for 5 consecutive rounds), it reports convergence.

5. **Communication cost** — only 2 × 64 floats (~512 bytes) per client per round. No model weights are ever transmitted.
