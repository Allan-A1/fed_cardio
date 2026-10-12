# Deep Research: Combining 3 Different Architectures in Federated Learning

## The Core Problem

Your project has **three hospitals with three completely different model architectures:**

| Hospital | Modality | Model | Architecture | Parameters |
|----------|----------|-------|-------------|------------|
| A (Rural clinic) | PCG Heart Sound | PCGNet | 2D CNN (3 blocks) | ~353K |
| B (District hospital) | ECG Signal | ECGResNet | 1D ResNet (4 blocks) | ~590K |
| C (Heart center) | Echo Video | EchoNet | ResNet-18 (2D) | ~11.2M |

**FedAvg and FedProx CANNOT work here** because they average model *weights*. This requires every client to have the exact same model architecture with the exact same number of parameters. Your three models have completely different:
- Layer types (Conv1d vs Conv2d)
- Number of layers
- Number of parameters (353K vs 590K vs 11.2M)
- Input dimensions (1D audio vs 1D signal vs 2D image)

> [!IMPORTANT]
> **This is not a limitation — it's the exact research problem your project is designed to solve.** The literature has well-established solutions, and they are all based on the same key insight: **share knowledge at a higher abstraction level than raw weights.**

---

## The 5 Major Approaches (with Paper Citations)

### Approach 1: FedProto — Federated Prototype Learning ⭐ RECOMMENDED

**Paper:** Tan, Y., Long, G., Liu, L., Zhou, T., Lu, Q., Jiang, J., & Zhang, C. (2022). *FedProto: Federated Prototype Learning across Heterogeneous Clients.* **AAAI Conference on Artificial Intelligence (AAAI-22)**, 36(8), 8432–8440. https://ojs.aaai.org/index.php/AAAI/article/view/20819

**Code:** https://github.com/yuetan031/FedProto

#### How It Works

Instead of sharing model weights (impossible across different architectures), clients share **class prototypes** — the mean embedding vector for each class computed from the penultimate layer.

```mermaid
graph LR
    subgraph "Hospital A (PCG)"
        A1[PCGNet] --> A2["Embed: 128-d"]
        A2 --> A3["Proto_normal<br/>Proto_abnormal"]
    end
    subgraph "Hospital B (ECG)"
        B1[ECGResNet] --> B2["Embed: 128-d"]
        B2 --> B3["Proto_normal<br/>Proto_abnormal"]
    end
    subgraph "Hospital C (Echo)"
        C1[EchoNet] --> C2["Embed: 128-d"]
        C2 --> C3["Proto_normal<br/>Proto_abnormal"]
    end
    
    A3 --> S["Server:<br/>Aggregate Global Prototypes"]
    B3 --> S
    C3 --> S
    S --> A1
    S --> B1
    S --> C1
```

#### Mathematical Formulation

**Step 1: Local Prototype Computation** — Each client `i` computes the mean embedding for each class `j`:

$$C_{i}^{j} = \frac{1}{|D_{i,j}|} \sum_{(x,y) \in D_{i,j}} f_i(\theta_i; x)$$

Where `f_i(θ_i; x)` is the output of the **penultimate layer** (the 128-d embedding in your models).

**Step 2: Global Prototype Aggregation** — The server averages prototypes across clients:

$$G^{j} = \frac{\sum_{i} |D_{i,j}| \cdot C_{i}^{j}}{\sum_{i} |D_{i,j}|}$$

Where `|D_{i,j}|` is the number of samples client `i` has for class `j` (weighted average).

**Step 3: Prototype-Regularized Local Training** — Each client trains with a composite loss:

$$\mathcal{L}_{total} = \mathcal{L}_{CE}(logits, y) + \lambda \sum_{j} \| f_i(\theta_i; x) - G^{j} \|^2$$

Where:
- `L_CE` = standard cross-entropy loss
- `λ` = regularization strength (hyperparameter, typically 0.1–1.0)
- The second term pulls local embeddings toward the global prototypes

#### Why It's Perfect for Your Project

1. **Architecture-agnostic:** Only requires that all models output embeddings in the same dimensionality. ✅ *Your models all have `embed_dim=128`*
2. **Your models are already designed for it:** All three models have `return_embedding=True` in their `forward()` method
3. **Communication cost is tiny:** Only 2 vectors × 128 floats = 256 floats per client per round (vs. millions of parameters in FedAvg)
4. **Privacy-preserving:** Prototype vectors are aggregate statistics, not individual patient data
5. **Proven convergence:** The paper provides theoretical convergence analysis under non-convex objectives
6. **Simple to implement:** ~100 lines of Python on top of your existing code

#### What Gets Communicated

| Direction | What's Sent | Size (per client) |
|-----------|-------------|-------------------|
| Client → Server | 2 prototype vectors (normal, abnormal) + sample counts | 2 × 128 floats + 2 ints = **1,028 bytes** |
| Server → Client | 2 global prototype vectors | 2 × 128 floats = **1,024 bytes** |

Compare this to FedAvg which would send the **entire model** (353K–11.2M parameters = 1.4MB–44.8MB).

---

### Approach 2: FedTGP — Trainable Global Prototypes

**Paper:** Zhang, J., Liu, Y., Hua, Y., & Cao, J. (2024). *FedTGP: Trainable Global Prototypes with Adaptive-Margin-Enhanced Contrastive Learning for Data and Model Heterogeneity in Federated Learning.* **AAAI Conference on Artificial Intelligence (AAAI-24)**, 38(15), 16768–16776.

**Code:** https://github.com/TsingZ0/FedTGP

#### How It Improves on FedProto

FedProto simply averages local prototypes to form global prototypes. FedTGP argues this causes **"prototype margin shrinking"** — the global prototypes for different classes drift too close together, losing discriminative power.

FedTGP instead:
1. **Learns** global prototypes (not averages them) via gradient descent on the server
2. Uses **Adaptive-margin Contrastive Learning (ACL)** to ensure global prototypes for different classes remain well-separated
3. Reports up to **9.08% accuracy improvement** over FedProto

#### Trade-off for Your Project

- **Pros:** Better global prototype quality, especially with class imbalance (your PCG is 79% normal / 21% abnormal)
- **Cons:** More complex server-side logic; requires tuning the margin hyperparameter; published in 2024 so fewer community implementations

---

### Approach 3: FedMD — Federated Model Distillation

**Paper:** Li, D. & Wang, J. (2019). *FedMD: Heterogenous Federated Learning via Model Distillation.* arXiv:1910.03581.

#### How It Works

1. A small **public dataset** is shared among all clients (or held on the server)
2. Each client runs its local model on this public dataset and produces **logits** (prediction scores)
3. The server aggregates the logits (averaging them) to form a **consensus prediction**
4. Each client then trains its local model to match these consensus predictions (knowledge distillation)

#### Why NOT Recommended for Your Project

> [!WARNING]
> FedMD requires a **shared public dataset** that all models can process. Your three models take completely different inputs (audio spectrograms, ECG signals, echo frames). **There is no public dataset that contains all three modalities for the same patients.** You confirmed this in your research plan — real paired pediatric ECG+echo+PCG data does not exist publicly.

---

### Approach 4: FedDF — Ensemble Distillation

**Paper:** Lin, T., Kong, L., Stich, S.U., & Jaggi, M. (2020). *Ensemble Distillation for Robust Model Fusion in Federated Learning.* **NeurIPS 2020**.

#### How It Works

Similar to FedMD but uses an **unlabeled proxy dataset** on the server. The server trains a "student" model by distilling the ensemble of client predictions.

#### Why NOT Recommended for Your Project

Same fundamental problem as FedMD — requires a shared dataset processable by all models. Also, the server would need to maintain a separate student model, adding complexity.

---

### Approach 5: FedCMD / MFCPL — Cross-Modal Prototype Methods

**Papers:**
- Le, H.Q. et al. (2024). *Cross-Modal Prototype based Multimodal Federated Learning under Severely Missing Modality (MFCPL).* arXiv:2401.13898.
- *Cross-Modal Federated Learning among Unimodal Devices (FedCMD).* (2025). **ACM IMWUT** (Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies). https://dl.acm.org/doi/10.1145/3749467
- Gai, K. et al. (2025). *Adaptive Prototype Knowledge Transfer for Federated Learning with Mixed Modalities and Heterogeneous Tasks (AproMFL).* arXiv:2502.04400.

#### How They Extend FedProto to Cross-Modal Settings

These are the **most recent papers (2024–2025)** specifically addressing your exact scenario: clients with **different modalities** (not just different architectures).

**MFCPL** adds two mechanisms on top of FedProto:
1. **Cross-Modal Prototype Regularization (CMPR):** Aligns modality-shared features with global prototypes
2. **Cross-Modal Contrastive Learning:** Pushes same-class prototypes from different modalities together, different-class apart

**FedCMD** specifically handles **unimodal clients** (each client has only one modality — exactly your scenario):
1. First trains unimodal encoders via federated learning
2. Shares prototypes across modalities for cross-modal feature alignment
3. Uses prototypes as "complements" for missing modalities

#### Relevance to Your Project

These are the **closest published precedents** to your project's core contribution. However, they are more complex than what you need for a 6-week timeline. Your project can be positioned as a simplified, clinically-grounded implementation of this line of work.

---

## Decision Matrix

| Method | Handles Different Architectures | Handles Different Modalities | No Shared Dataset Needed | Complexity | Proven Convergence | Code Available |
|--------|---|----|---|----|---|----|
| FedAvg/FedProx | ❌ | ❌ | ✅ | Low | ✅ | ✅ |
| **FedProto** | **✅** | **✅** | **✅** | **Low** | **✅** | **✅** |
| FedTGP | ✅ | ✅ | ✅ | Medium | ✅ | ✅ |
| FedMD | ✅ | ❌ | ❌ (needs public data) | Medium | ✅ | ✅ |
| FedDF | ✅ | ❌ | ❌ (needs proxy data) | Medium | ✅ | ✅ |
| MFCPL/FedCMD | ✅ | ✅ | ✅ | High | Partial | Limited |

---

## ⭐ RECOMMENDATION: FedProto (with optional FedTGP enhancement)

> [!IMPORTANT]
> **Use FedProto as your primary cross-modal federation method.** It is the best fit because:
> 1. It's published at a top venue (AAAI 2022) with 600+ citations
> 2. It has proven theoretical convergence guarantees
> 3. Your models are already perfectly designed for it (128-d embeddings, `return_embedding=True`)
> 4. It requires zero shared data across hospitals
> 5. It can be implemented in ~100 lines of code
> 6. The cross-modal extension is a natural, well-motivated application

### How It Maps to Your Existing Code

Your models already have the exact interface FedProto needs:

```python
# All three models already support this:
logits, embedding = model(x, return_embedding=True)
# embedding.shape = (batch_size, 128)  ← This IS the prototype feature
```

### The FedProto Training Loop for Your Project

```
For each federation round t = 1, 2, ..., T:
    
    1. LOCAL TRAINING (each hospital independently):
       - Hospital A: Train PCGNet on heart sounds for E local epochs
       - Hospital B: Train ECGResNet on ECG signals for E local epochs  
       - Hospital C: Train EchoNet on echo frames for E local epochs
       - Loss = CrossEntropy + λ * PrototypeRegularization
    
    2. PROTOTYPE COMPUTATION (each hospital):
       - For each class c ∈ {normal, abnormal}:
           - Run all training samples of class c through the model
           - Collect the 128-d embeddings
           - Compute the mean: proto_c = mean(embeddings_c)
       - Send (proto_normal, proto_abnormal, n_normal, n_abnormal) to server
    
    3. SERVER AGGREGATION:
       - For each class c:
           - global_proto_c = weighted_average(all client protos for class c)
           - Weights = number of samples each client has for class c
       - Send (global_proto_normal, global_proto_abnormal) back to all clients
    
    4. NEXT ROUND:
       - Clients use global prototypes in their loss function
       - Local embeddings are pulled toward global prototypes
```

### The Key Insight: Why This Works Across Modalities

Even though a heart sound spectrogram and an ECG signal look nothing alike, **the clinical meaning is the same**: both are trying to distinguish "normal" from "abnormal" hearts. FedProto forces all three models to learn embeddings where:

- **Normal heart sounds**, **normal ECGs**, and **normal echoes** all cluster in the same region of the 128-d embedding space
- **Abnormal** ones cluster in a different region

This is **semantic alignment** — the models don't share parameters, but they share a common understanding of what "normal" and "abnormal" mean in their respective domains.

---

## Complete Reference List

### Primary Method Papers

| # | Paper | Venue | Year | Relevance |
|---|-------|-------|------|-----------|
| 1 | Tan, Y. et al. *FedProto: Federated Prototype Learning across Heterogeneous Clients* | **AAAI** | 2022 | **Primary method** — architecture-agnostic prototype sharing |
| 2 | Zhang, J. et al. *FedTGP: Trainable Global Prototypes with Adaptive-Margin-Enhanced Contrastive Learning* | **AAAI** | 2024 | Enhancement — learned prototypes, better margin |
| 3 | Dai, Y. et al. *Tackling Data Heterogeneity in Federated Learning with Class Prototypes* | **AAAI** | 2023 | Extension — prototype-based data heterogeneity handling |
| 4 | Huang, W. et al. *Rethinking Federated Learning with Domain Shift: A Prototype View* | **CVPR** | 2023 | Prototype view of domain shift in FL |

### Cross-Modal / Multimodal FL Papers

| # | Paper | Venue | Year | Relevance |
|---|-------|-------|------|-----------|
| 5 | Le, H.Q. et al. *Cross-Modal Prototype based Multimodal Federated Learning under Severely Missing Modality (MFCPL)* | arXiv:2401.13898 | 2024 | **Closest precedent** — cross-modal prototype alignment |
| 6 | *Cross-Modal Federated Learning among Unimodal Devices (FedCMD)* | **ACM IMWUT** | 2025 | Exactly your setup: each client has single modality |
| 7 | Gai, K. et al. *Adaptive Prototype Knowledge Transfer for Federated Learning with Mixed Modalities and Heterogeneous Tasks (AproMFL)* | arXiv:2502.04400 | 2025 | Adaptive prototype construction for modality heterogeneity |
| 8 | Yu, Q. et al. *CreamFL: Contrastive Representation Ensemble and Aggregation for Multimodal FL* | **ICLR** | 2023 | Benchmark method for modality-heterogeneous FL |

### Baseline / Alternative Methods

| # | Paper | Venue | Year | Relevance |
|---|-------|-------|------|-----------|
| 9 | Li, D. & Wang, J. *FedMD: Heterogenous Federated Learning via Model Distillation* | arXiv:1910.03581 | 2019 | Alternative: logit-based distillation (needs shared data) |
| 10 | Lin, T. et al. *FedDF: Ensemble Distillation for Robust Model Fusion in FL* | **NeurIPS** | 2020 | Alternative: ensemble distillation (needs proxy data) |
| 11 | Li, T. et al. *FedProx: Federated Optimization in Heterogeneous Networks* | **MLSys** | 2020 | Baseline: same-architecture FL with proximal term |
| 12 | Yi, Z. et al. *FedGH: Heterogeneous Federated Learning with Generalized Global Header* | **ACM MM** | 2023 | Alternative: shared classifier head approach |

### Surveys

| # | Paper | Venue | Year | Relevance |
|---|-------|-------|------|-----------|
| 13 | Ye, M. et al. *Heterogeneous Federated Learning: State-of-the-art and Research Challenges* | arXiv:2307.10616 | 2023 | **Comprehensive survey** — taxonomy of all HFL methods |
| 14 | *FedCVD: A Real-World FL Benchmark for Cardiovascular Disease* | OpenReview | 2024 | Benchmark for cardiac FL across institutions |

---

## How FedProto Concretely Fits Into Your Code

Here's how the implementation maps to your existing files:

| Existing File | What It Already Has | What FedProto Adds |
|---|---|---|
| [pcg_model.py](file:///d:/clg/project/fl_pediatric/src/models/pcg_model.py) | `forward(x, return_embedding=True)` → 128-d | Nothing — already ready |
| [ecg_model.py](file:///d:/clg/project/fl_pediatric/src/models/ecg_model.py) | `forward(x, return_embedding=True)` → 128-d | Nothing — already ready |
| [echo_model.py](file:///d:/clg/project/fl_pediatric/src/models/echo_model.py) | `forward(x, return_embedding=True)` → 128-d | Nothing — already ready |
| [datasets.py](file:///d:/clg/project/fl_pediatric/src/datasets.py) | PCGDataset, ECGDataset, EchoDataset | Nothing — already ready |
| [train_utils.py](file:///d:/clg/project/fl_pediatric/src/utils/train_utils.py) | `train_one_epoch()`, `evaluate()` | Modify to accept `global_protos` and add regularization |
| `src/federation/__init__.py` | **EMPTY** | **NEW:** `fedproto.py` — prototype computation + aggregation |
| — | — | **NEW:** `run_fedproto.py` — end-to-end federation runner |

### The New Loss Function (what changes in training)

```python
# Current loss (solo baseline):
loss = criterion(logits, labels)

# FedProto loss (federated):
loss_ce = criterion(logits, labels)
loss_proto = 0
for j in [0, 1]:  # for each class
    mask = (labels == j)
    if mask.sum() > 0:
        local_embeds = embeddings[mask]  # (n_j, 128)
        global_proto = global_protos[j]   # (128,)
        loss_proto += torch.mean((local_embeds - global_proto) ** 2)
loss = loss_ce + lambda_proto * loss_proto
```

This is literally the only code change needed in the training loop. Everything else (model architectures, data loading, evaluation) stays exactly the same.

---

## Why This Is a Legitimate Research Contribution

Your project is **not** just re-implementing FedProto. Your contribution is:

1. **Novel application domain:** FedProto was tested on MNIST/CIFAR/FEMNIST — image classification with different CNN architectures. **Nobody has applied it to cross-modal cardiac screening (PCG + ECG + Echo).**

2. **Clinically motivated:** The three modalities represent real hospital tiers (rural stethoscope → district ECG → tertiary echo), which is a genuine clinical scenario.

3. **Validated with a controlled ablation:** Your 9-lead/12-lead ECG split tests FedAvg/FedProx as a positive control, proving the aggregation code works before the harder cross-modal case.

4. **Positioned within a clear literature lineage:** FedProto (2022) → MFCPL (2024) → FedCMD (2025) → **your work** (2026, simplified clinical instance).

> [!TIP]
> In your paper, cite FedProto as the foundational method, cite MFCPL/FedCMD as the closest cross-modal extensions, and position your work as *"a clinically-grounded, simplified instance of cross-modal prototype FL applied to pediatric cardiac screening across three genuinely different modalities."*
