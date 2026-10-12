# FL Pediatric CHD — Project Status

_Last updated: 2026-08-01_

---

## ✅ Done

- [x] Project plan written & frozen (`pediatric-CHD-federated-learning-project-plan.md`)
- [x] Python virtual environment created (`.venv`)
- [x] Project folder structure created (`src/`, `notebooks/`, `outputs/`, etc.)
- [x] All packages installed (`requirements.txt` — torch, librosa, wfdb, opencv, etc.)
- [x] **Hospital A** — CirCor DigiScope (PCG) downloaded & extracted → `datasets/CirCor_DigiScope/`
- [x] **Hospital B** — ZZU-pECG (ECG) downloaded → `datasets/ZZU-pECG/` _(needs extraction — split zip: `.zip` + `.z01`, use 7-Zip)_
- [x] **Hospital C** — EchoNet-Pediatric (Echo) downloaded → `datasets/EchoNet-Pediatric/` _(videos + CSVs present)_
- [x] **PCG preprocessing** — 11,162 segments | Normal: 8,822 | Abnormal: 2,340 → `outputs/processed/pcg/`
- [x] **Echo preprocessing** — 3,258 ED/ES pairs | Normal: 2,768 | Reduced EF: 490 → `outputs/processed/echo/`

---

## 🔄 In Progress

- [ ] **Leipzig Heart Center ECG-Database** — downloading (for Week 6 stress test) → move to `datasets/Leipzig_ECG/` when done

---

## 🔴 Now — Building (Leipzig NOT required)

1. ~~Set up project folder structure + `requirements.txt` + install all packages~~ done
2. ~~PCG preprocessing pipeline~~ done (11,162 segments saved)
3. ~~Echo preprocessing pipeline~~ done (3,258 ED/ES pairs saved)
4. **[NEXT]** Extract ZZU-pECG — use 7-Zip on `Child_ecg.zip` + `Child_ecg.z01`
5. **[NEXT]** Build solo baseline models — Hospital A (PCG CNN) + Hospital C (Echo ResNet-18)

---

## 🟡 Medium Priority — Week 2–3

- [ ] Inspect label distributions for all 3 datasets
- [ ] Train solo baselines (Hospital A, B, C independently)
- [ ] ECG internal ablation: split ZZU-pECG into 9-lead vs 12-lead shards
- [ ] Run FedAvg / FedProx on the 9-lead/12-lead split

---

## 🟢 Later — Week 4–6

- [ ] Implement cross-modal prototype bridge (Hospitals A + B + C)
- [ ] Grad-CAM explainability (PCG, ECG, echo)
- [ ] Fairness audit (age, sex, site)
- [ ] Leipzig external stress test (Week 6)
- [ ] Write report / paper draft

---

## 📁 Dataset Summary

| Dataset | Modality | Location | Status |
|---|---|---|---|
| CirCor DigiScope | PCG (Heart Sound) | `datasets/CirCor_DigiScope/` | ✅ Ready |
| ZZU-pECG | ECG | `datasets/ZZU-pECG/` | ⚠️ Needs extraction |
| EchoNet-Pediatric | Echocardiography | `datasets/EchoNet-Pediatric/` | ✅ Ready |
| Leipzig Heart Center ECG | ECG (Stress test) | `datasets/Leipzig_ECG/` | 🔄 Downloading |
