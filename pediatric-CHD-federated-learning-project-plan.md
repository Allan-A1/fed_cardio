# Multimodal Heterogeneous Federated Learning for Pediatric Cardiac Screening

**A 6-week research project plan — frozen after Week 1, not revised afterward.**
**v2 — updated dataset design (see Section 3a for what changed and why).**

---

## 1. Research question (final wording)

> Can hospitals with structurally different cardiac diagnostic equipment — a digital stethoscope, an ECG machine, and an echocardiography suite — collaboratively improve a pediatric cardiac **screening** model (flagging children who need specialist follow-up) without sharing patient data, and without assuming they use the same model architecture?

The shared task across all clients is **binary screening triage: normal vs. abnormal (refer to specialist)** — not multi-class CHD diagnosis. This is the single most important scoping decision in the project and is frozen after Week 1.

---

## 2. The two things this project is actually about (everything else is secondary)

| # | Core objective | Why it's the novelty | Effort |
|---|---|---|---|
| 1 | **Same-architecture aggregation sanity check.** Before trusting cross-modal aggregation, verify FedAvg/FedProx actually helps in the easy, controlled case: split the ECG dataset (Hospital B) into two non-IID shards (9-lead vs. 12-lead) as an internal methodology ablation, not a fourth hospital in the main narrative. | Standard method, used here as a positive control, not the headline result | Low–Medium |
| 2 | **Cross-modality knowledge exchange across three genuinely different real datasets** (heart sound, ECG, echo) without shared architecture or raw data — models influence each other via lightweight class-prototype alignment, not weight averaging | This is the actual research contribution: a workable, low-complexity protocol for hospitals whose models can never share a parameter space | High |

If time runs short, cut explainability/fairness/the Leipzig stress-test first — never these two.

---

## 3a. What changed from v1, and why

The first draft simulated Hospital A and B by splitting one ECG dataset in two, because no public dataset had a genuine third modality with a clean screening-relevant label. That's no longer necessary: **CirCor DigiScope** (PhysioNet) is a real, public, pediatric heart-sound dataset collected during a rural screening campaign, with real cardiologist-assigned normal/abnormal labels. It is a better match for "Hospital A: rural clinic" than an ECG subset ever was — a digital stethoscope is cheaper and more portable than any ECG machine — and it makes the "multimodal" claim in the title literal rather than approximate: three hospitals, three genuinely different signal types, three real datasets, no synthetic splitting required for the core clinical narrative.

The 9-lead/12-lead ECG split from v1 is kept, but demoted to an internal ablation (Core objective 1 above) used only to validate that the aggregation code works correctly in a simple, same-architecture case before it's trusted in the harder cross-modal case.

---

## 3. Datasets — verified facts, roles, and access

### Hospital A — CirCor DigiScope Phonocardiogram Dataset (rural clinic)

- 5,282 heart-sound recordings from 1,568 patients, collected via digital stethoscope during two mass pediatric cardiology screening campaigns in rural Northeast Brazil (2014–2015), sampled at 4 kHz, ~313 hours total.
- Real cardiologist-assigned clinical outcome label (normal/abnormal) plus detailed murmur annotations (timing, pitch, grading, location — pulmonary, aortic, mitral, tricuspid).
- Ages span roughly 0–30 years (0.1–356.1 months); **filter to pediatric ages (≤18 years) in Week 1 preprocessing** to match the project's scope — don't skip this.
- Hosted on PhysioNet, used in the official 2022 PhysioNet Challenge; openly documented, no unusual access barrier expected, but confirm the exact license/citation terms at download time.
- Note: only ~60–70% of the originally collected data was publicly released (the rest held back for challenge evaluation) — expect roughly 1,000+ usable pediatric patients after filtering, which is still solid for this project's scale.

### Hospital B — ZZU-pECG (district hospital)

- 14,190 ECG records from 11,643 children aged 0–14, First Affiliated Hospital of Zhengzhou University, 2018–2024, 500 Hz, 5–120 s recordings.
- 2,641 normal / 11,549 abnormal records; ~19 ICD-10-coded CVD categories including CHD, myocarditis, cardiomyopathy, Kawasaki disease, arrhythmia.
- Also contains a documented 12-lead (12,334 records) vs. 9-lead (1,856 records) split — used for the internal same-architecture ablation in Core objective 1, not as a second "hospital" in the main narrative.
- **Access:** published via Nature *Scientific Data* (2025) — check the paper's data availability statement for the current repository link; may require a data use agreement. Do this in Week 1, day 1.

### Hospital C — EchoNet-Pediatric (children's heart center)

- 7,643 labeled echo video clips (apical-4-chamber, parasternal short-axis) from ~1,958 patients aged 0–18, Lucile Packard Children's Hospital at Stanford, 2014–2021. Only ED/ES frames are annotated with EF and expert tracings.
- Confirmed by a 2026 open-access cardiovascular imaging scoping review to be **the only publicly available large-scale pediatric echocardiography dataset** — there is no better public alternative with direct CHD labels, so EF-based derivation (below) is the correct approach, not a shortcut.
- **No CHD labels exist in this dataset.** Binarize EF into "normal vs. reduced systolic function" using a clinically sourced pediatric cutoff (confirm the exact threshold from pediatric echo literature, e.g., ASE pediatric guidelines, before Week 2 — do not guess a number).
- **Access:** Stanford AIMI / Stanford Redivis, requires registration and a signed non-commercial Research Use Agreement.

### Leipzig Heart Center ECG-Database — external stress-test only (Week 6), not a training client

- Only 29 pediatric subjects, all already diagnosed with arrhythmia/CHD, no healthy controls, labels are rhythm types not CHD presence. Hosted on PhysioNet, 12-lead + intracardiac electrograms, ~977 Hz.
- **Role:** run the federated ECG model on Leipzig recordings and check whether it still fires "abnormal" on genuinely abnormal, differently-instrumented pediatric ECGs. Sensitivity-only check (no true negatives available) — report as such.

### Optional appendix — EchoNext (adult, real paired ECG+echo, method-validation only)

- A newly released PhysioNet dataset: 100,000 ECGs paired with echocardiogram-confirmed structural heart disease labels from Columbia/Allen hospitals — but this is an **adult** dataset (ages capped at 90).
- Not part of the core project (wrong population), but a legitimate optional Week 6 appendix: pretrain or sanity-check the cross-modal prototype-alignment mechanism on real paired data (where ground truth pairing exists) to show the method works in principle, before applying it to the true pediatric setting where no pairing exists. Skip this unless the core plan finishes early — it strengthens the paper but isn't required.

### Datasets checked and ruled out

- Real paired pediatric ECG+echo data **does exist** — Boston Children's Hospital, Children's Hospital of Philadelphia, and Mount Sinai have all published strong results (AUROC 0.95–0.96) using ECG-echo pairs ≤2 days apart for pediatric CHD and LV dysfunction prediction. This confirms the clinical premise of your project is real and important. But this data lives inside each hospital's private EHR/MUSE system under IRB approval — it is not publicly downloadable, and there is no substitute for it in open data today.

### 3b. Direct dataset links

| Dataset | Link | Access |
|---|---|---|
| CirCor DigiScope (Hospital A, PCG) | https://physionet.org/content/circor-heart-sound/1.0.3/ | Open, PhysioNet account |
| ZZU-pECG (Hospital B, ECG) | https://doi.org/10.6084/m9.figshare.27078763 (data); https://doi.org/10.1038/s41597-025-05225-z (paper) | Open, figshare |
| EchoNet-Pediatric (Hospital C, Echo) | https://echonet.github.io/pediatric/ ; registration via https://stanfordaimi.azurewebsites.net/datasets/a84b6be6-0d33-41f9-8996-86e5df53b005 | Registration + signed non-commercial research use agreement |
| Leipzig Heart Center ECG-Database (Week 6 stress test) | https://physionet.org/content/leipzig-heart-center-ecg/1.0.0/ | Open, PhysioNet account |
| EchoNext (optional appendix, adult) | https://physionet.org/content/echonext/1.1.1/ | Listed as restricted in at least one third-party catalogue — confirm current tier when you register; it may require a credentialing step similar to MIMIC |

---

## 4. Shared label scheme

| Client | Raw label available | Screening flag derivation |
|---|---|---|
| Hospital A (CirCor, PCG) | Cardiologist outcome: normal/abnormal | Used directly |
| Hospital B (ZZU-pECG) | Normal / one of ~19 CVD categories | Normal → 0; any CVD category → 1 |
| Hospital C (EchoNet-Pediatric) | Continuous EF % | EF below the confirmed pediatric cutoff → 1; else 0 |

Keep a **secondary, client-local-only head** on Hospital B for the full multi-label CVD diagnosis (already benchmarked in the literature, gives a richer results section) — never federate that head across modalities. Only the binary screening head is shared/aggregated.

---

## 5. System architecture

**Local models**
- Hospital A (PCG): 1D CNN on raw or mel-spectrogram-transformed heart sound audio.
- Hospital B (ECG): compact 1D ResNet (4–6 residual blocks) on filtered, fixed-length ECG signal.
- Hospital C (Echo): 2D CNN (ResNet-18 or EfficientNet-B0) on the ED/ES frame pair — **not** a full 3D video transformer; EchoNet-Pediatric's own annotations are frame-level, so this is the label-appropriate scope, not a simplification of the task.

**Federation protocol**
1. Each of the three clients trains its local model.
2. Server-side sanity check (internal ablation, Core objective 1): split Hospital B's ECG data into 9-lead/12-lead shards, run FedAvg and FedProx between them, confirm federation beats both solo shards. This validates the aggregation code before the harder step.
3. All three real clients (A, B, C) periodically compute two class-prototype vectors each (mean penultimate-layer embedding for "normal," "abnormal") and send only those — small, aggregate, not reconstructable to a patient.
4. Server learns a lightweight linear projection per client that pulls same-class prototypes together across modalities and pushes different-class prototypes apart.
5. This projection calibrates each client's decision threshold/confidence so "abnormal" means a comparably-calibrated risk level regardless of source modality, and (stretch goal) supplies a soft distillation signal added to each client's local loss.

**Implementation note:** the aggregation logic here is non-standard (FedAvg for the internal ablation + a custom prototype step across three real clients), so a plain PyTorch simulation loop is very likely simpler and more transparent than adopting a full FL framework like Flower.

**Honesty note for the write-up:** this is a *simulated* multi-institution study using three real but disjoint public datasets to emulate heterogeneity, not a real multi-hospital deployment — standard, accepted methodology in FL research, but must be stated plainly as a limitation.

---

## 6. Week-by-week plan

**Weeks 1–4 are the non-negotiable core.** Weeks 5–6 add rigor and polish. A 4-week version stops after Week 4 and folds a half-day each of explainability and fairness into Week 4.

### Week 1 — Freeze the plan
- Register for / download CirCor DigiScope, ZZU-pECG, and EchoNet-Pediatric (start day 1 — access approval can take days, especially Stanford AIMI's agreement).
- Inspect actual label distributions: CirCor normal/abnormal counts after pediatric age filtering, ZZU-pECG normal/abnormal and lead-count counts, EchoNet-Pediatric EF distribution (pick and cite the pediatric dysfunction cutoff).
- Freeze: the screening-flag label scheme (Section 4), the three-client design (Section 3), the model architectures (Section 5).
- **Exit criteria:** all three core datasets downloaded and inspected; label scheme written down and not revisited again.
- **Go/no-go:** if EchoNet-Pediatric access is delayed past day 4, start Weeks 1–2 on Hospitals A and B only and slot echo in once access clears.

### Week 2 — Preprocessing + solo baselines
- PCG pipeline: pediatric age filter, resample/segment audio, mel-spectrogram or raw-waveform features.
- ECG pipeline: filtering, resampling, fixed-length padding.
- Echo pipeline: ED/ES frame extraction, resize, normalize.
- Train three **solo** baselines (Hospital A alone, B alone, C alone).
- **Exit criteria:** baseline metrics table (AUROC, sensitivity/specificity at a fixed operating point) for all three.

### Week 3 — Internal same-architecture ablation (Core objective 1)
- Split Hospital B's ECG data into 9-lead/12-lead shards; implement FedAvg and FedProx between them.
- Produce the sanity-check results table: solo 9-lead, solo 12-lead, FedAvg, FedProx, centralized-pooled.
- **Success check:** federation should beat both solo shards and approach the centralized-pooled upper bound. If it doesn't, investigate before moving on — this is the easy case and it needs to work before Week 4's harder case is trustworthy.

### Week 4 — Cross-modality prototype bridge across all three real hospitals (the core contribution)
- Implement per-client class-prototype computation and the server-side alignment projection across Hospitals A, B, and C.
- Run the fused pipeline end to end; report modality-specific metrics plus the effect of the prototype bridge on cross-modality calibration/agreement.
- **Exit criteria:** full pipeline produces final numbers; this is the last week architecture decisions can change.

### Week 5 — Explainability + fairness (evaluation only)
- Grad-CAM/saliency on PCG (time/frequency-band importance), ECG (lead + time-segment importance), and echo frames (spatial region importance). If you have any access to a pediatric cardiologist or resident, 20–30 minutes reviewing 10–20 example explanations is worth more than additional model tuning.
- Fairness audit: slice AUROC/sensitivity/specificity by age band, sex, and site on the held-out test set. Report disparities — do not train a fairness-optimized model; that's future work.

### Week 6 — Robustness, ablations, writing
- Run the Leipzig sensitivity-only stress-test (Section 3).
- Optional: EchoNext appendix experiment (Section 3), only if the core plan finished early.
- Cheap ablations: FedAvg vs. FedProx; sensitivity to non-IID partition severity.
- Finalize figures/tables; write methods, results, discussion, and a limitations section covering: simulated (not real) multi-institution deployment, no real paired cohort, no formal differential privacy, no prospective clinical validation.
- Package the code repository.

---

## 7. Evaluation plan

**Primary metric:** AUROC and sensitivity at a fixed, clinically motivated operating point (screening tools typically prioritize sensitivity), per client and pooled.

**Success criterion 1 (sanity check):** FedAvg/FedProx on the internal 9-lead/12-lead ECG split beats both solo shards, ideally approaching the centralized-pooled reference.

**Success criterion 2 (core novelty claim):** the prototype-bridge mechanism across the three real hospitals produces a measurable, reportable effect on cross-modality calibration agreement. A modest or null effect at this data scale is a legitimate, honestly-reportable finding, not a project failure.

---

## 8. Explicitly out of scope (future work, not silently dropped)

- Formal differential privacy (DP-SGD with tuned epsilon/clipping) — core privacy mechanism is structural (only weights, gradients, and small aggregate prototypes ever leave a client).
- Fairness-*optimized* training (vs. auditing).
- Full 3D video transformer for echo.
- SHAP-based dashboards (Grad-CAM/saliency is faster and standard in this literature).
- Secure aggregation / cryptographic protocols.
- Real multi-institution deployment (this is a simulated study on public datasets).
- Acquiring real paired pediatric ECG+echo data (confirmed not publicly available anywhere).

---

## 9. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| EchoNet-Pediatric access delayed (registration/agreement) | Medium | Start Weeks 1–2 on Hospitals A and B; slot echo in once access clears |
| CirCor's non-pediatric subjects contaminate the sample | Low–Medium | Apply and document an explicit ≤18-year age filter in Week 1 |
| Pediatric EF dysfunction cutoff unclear or contested in literature | Medium | Pick one well-cited threshold, state it explicitly as an assumption |
| Same-architecture ablation (Week 3) doesn't beat solo baselines | Low–Medium | Investigate non-IID severity and local-epoch count before concluding failure |
| Cross-modal prototype bridge shows negligible effect | Medium | Still a reportable, honest research finding — pre-register this as acceptable |
| No real paired ECG+echo/PCG cohort available | High (expected, confirmed) | Documented as a known constraint of using disjoint public datasets, not a fixable bug |

---

## 10. Final deliverables checklist

- [ ] Codebase: preprocessing (PCG, ECG, echo), local models, FL simulation loop, prototype-bridge module
- [ ] Results tables: same-architecture ablation (Week 3); solo vs. fused pipeline (Week 4)
- [ ] Grad-CAM explainability figures (PCG, ECG, echo)
- [ ] Fairness audit table (age, sex, site)
- [ ] Leipzig external stress-test result
- [ ] Optional: EchoNext appendix result
- [ ] Written report/paper draft: methods, results, discussion, limitations
- [ ] This document, updated only in Section 6's checkboxes — not re-planned

---

## 11. Key references

### Aggregation mechanism — direct precedent, 2022–2026

The class-prototype cross-modal bridge in Section 5 is not a speculative idea; it sits on a specific, traceable line of published work:

- Tan, Y., Long, G., Liu, L., Zhou, T., Lu, Q., Jiang, J., & Zhang, C. (2022). *FedProto: Federated Prototype Learning across Heterogeneous Clients.* AAAI 2022. https://ojs.aaai.org/index.php/AAAI/article/view/20819 (code: https://github.com/yuetan031/FedProto) — the foundational method: clients send only mean per-class embedding vectors ("prototypes") instead of gradients or weights; the server averages them into global prototypes and sends those back to regularize local training. This is a unimodal, cross-*architecture* method — the direct ancestor of the mechanism in this plan.
- Dai, Y., Chen, Z., Li, J., Heinecke, S., Sun, L., & Xu, R. (2023). *Tackling Data Heterogeneity in Federated Learning with Class Prototypes.* AAAI 2023.
- Huang, W., Ye, M., Shi, Z., Li, H., & Du, B. (2023). *Rethinking Federated Learning with Domain Shift: A Prototype View.* CVPR 2023.
- Zhang, J., Liu, Y., Hua, Y., & Cao, J. (2024). *FedTGP: Trainable Global Prototypes with Adaptive-Margin-Enhanced Contrastive Learning for Data and Model Heterogeneity in Federated Learning.* AAAI 2024.
- Le, H. Q. et al. (2024). *Cross-Modal Prototype based Multimodal Federated Learning under Severely Missing Modality (MFCPL).* arXiv:2401.13898. https://arxiv.org/abs/2401.13898 — extends prototype-sharing explicitly to clients with **different modalities**, with the paper explicitly noting prior prototype-FL work "solely focused on scenarios involving unimodal data" before this extension. Closest published match to Section 5's mechanism.
- *Adaptive Prototype Knowledge Transfer for Federated Learning with Mixed Modalities and Heterogeneous Tasks (AproMFL).* (2025). arXiv:2502.04400. https://arxiv.org/abs/2502.04400 — client-adaptive prototype alignment across mixed modalities and heterogeneous tasks.
- *Cross-Modal Federated Learning among Unimodal Devices (FedCMD).* (2025). ACM IMWUT. https://dl.acm.org/doi/10.1145/3749467 — clients each hold a single modality (not multimodal per-client data), share prototypes for cross-modal feature alignment; the client setup here is the closest published match to "an ECG-only hospital and an echo-only hospital."
- Wang, Y. et al. *CreamFL* — cross-modal federated learning via global-local contrastive learning on shared representations, frequently cited as the benchmark method for modality-heterogeneous FL in 2024–2026 surveys.

In short: prototype-sharing for architecture heterogeneity is well-established since 2022, and its extension to modality heterogeneity specifically is an active line of published work from 2024 onward. This project's version is a deliberately simplified instance of that line (two class centroids, a linear projection, no contrastive loss over hard negatives) — scoped down for a 4–6 week timeline, not an unprecedented mechanism.

### Datasets and domain context

- Li, D. & Wang, J. (2019). *FedMD: Heterogenous Federated Learning via Model Distillation.* arXiv:1910.03581.
- Lin, T., Kong, L., Stich, S. U., & Jaggi, M. (2020). *Ensemble Distillation for Robust Model Fusion in Federated Learning (FedDF).* NeurIPS 2020.
- Li, T., Sahu, A. K., Zaheer, M., Sanjabi, M., Talwalkar, A., & Smith, V. (2020). *Federated Optimization in Heterogeneous Networks (FedProx).* MLSys 2020.
- Oliveira, J. et al. (2022). *The CirCor DigiScope Phonocardiogram Dataset.* PhysioNet, v1.0.3. https://physionet.org/content/circor-heart-sound/1.0.3/
- Reyna, M. et al. (2022). *Heart Murmur Detection from Phonocardiogram Recordings: The George B. Moody PhysioNet Challenge 2022.* PLOS Digital Health.
- ZZU-pECG: *A pediatric ECG database with disease diagnosis covering 11,643 children.* Scientific Data (2025).
- EchoNet-Pediatric: *Video-Based Deep Learning for Automated Assessment of Left Ventricular Ejection Fraction in Pediatric Patients.* J. Am. Soc. Echocardiography (2023).
- Leipzig Heart Center ECG-Database (PhysioNet, 2025).
- Elias, P. & Finer, J. (2025). *EchoNext: A Dataset for Detecting Echocardiogram-Confirmed Structural Heart Disease from ECGs.* PhysioNet.
- Boston Children's Hospital / CHOP pediatric AI-ECG studies (Lancet Digital Health, 2025; PubMed 38953953, 38314583) — evidence that paired pediatric ECG-echo prediction is real and clinically valuable, though not publicly downloadable.
- *Open-access datasets for cardiovascular imaging: A scoping review.* ScienceDirect (2026) — confirms EchoNet-Pediatric is the only large-scale public pediatric echo dataset.
- Heterogeneous Federated Learning: State-of-the-art and Research Challenges, arXiv:2307.10616.
