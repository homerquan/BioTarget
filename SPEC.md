# SPEC.md — Multimodal Graph–Text Drug Design CLI

## 1) Product goal
Build a **CLI tool** for **drug discovery / small-molecule design** that can:

1. **Train** a multimodal model with:
   - a **molecular graph encoder**
   - a **text encoder**
   - a **shared aligned embedding space**
   - optional **property prediction heads**
2. **Infer / design** from:
   - a **text goal** such as `"design a non-toxic kinase inhibitor with good oral ADMET"`
   - an optional **similar known drug / seed molecule** (SMILES or name)
3. Return **Top-N candidate molecules** ranked by:
   - goal-text relevance
   - similarity / novelty balance
   - predicted ADMET / toxicity / synthesizability / docking proxy scores

This should feel closer to **image-text generation + retrieval** than to a pure property classifier:
- **text** = design intent / prompt
- **reference molecule** = analogous to an image prompt or reference image
- **output** = a ranked set of candidate drug designs

---

## 2) Honest architecture opinion

### Recommended core design
Start with **two encoders + alignment loss**, similar to CLIP:
- one encoder for the **molecular graph**
- one encoder for **text**
- train both to land in a **compatible embedding space**
- add small **property heads** and a **ranking head**

### Why this is the right starting point
For this product, the main problem is not only prediction. It is:
- matching chemical structures to human design intent
- retrieving and ranking promising candidates
- leveraging known compounds as references
- staying trainable and extensible

A CLIP-style alignment system is the cleanest first step.

### What should *not* be the starting point
Do **not** start with:
- a pure VAE shared latent model as the center of the system
- RL as the main training method
- fully autoregressive molecule generation from day one

### Why not VAE first
A shared-latent VAE is elegant, but for an initial production-quality tool it is usually harder to stabilize and less directly useful than contrastive alignment plus reranking. VAE / diffusion / flow-based generation make more sense later when generation itself becomes the center of the product. Multimodal molecule-text work such as **MoleculeSTM** is built around contrastive alignment on structure-text pairs, not a pure VAE-first design. citeturn498535search22turn276799search5

### Why not RL first
RL is better reserved for **later-stage constrained optimization** after you already have:
- a strong retriever / scorer
- a calibrated property predictor
- a candidate generator

For early versions, **supervised learning + contrastive alignment + reranking** is the right default. TDC and mainstream ADMET benchmarks are built around supervised evaluation rather than RL-centric training. citeturn498535search9turn498535search13

---

## 3) Product input / output definition

## Inference input

### Required input
- `goal_text: str`

Example:
- `"Design a liver-safe, low-cardiotoxic, orally available small molecule similar to osimertinib but with lower hERG risk."`

### Optional input
- `reference_molecule`: one of
  - SMILES string
  - SDF/MOL file
  - known drug name resolved to structure upstream
- `target_profile`: structured JSON or YAML constraints
- `top_n`: integer
- `novelty_weight`, `similarity_weight`, `toxicity_weight`, etc.

### Optional advanced input
- target protein ID / assay family
- hard filters such as molecular weight, logP, TPSA, HBD/HBA, rotatable bonds
- medicinal chemistry exclusion rules / SMARTS alerts

## Inference output
Return **Top-N candidates** with:
- canonical SMILES
- 2D depiction path or inline rendering
- similarity to reference compound
- text-goal alignment score
- predicted properties:
  - toxicity
  - hERG / DILI / BBB / solubility / oral bioavailability proxies
  - synthetic accessibility / QED
- novelty score
- final combined rank score
- short textual rationale

Example output object:
```json
{
  "goal_text": "Design a low-toxicity oral kinase inhibitor similar to osimertinib",
  "reference": "osimertinib",
  "top_candidates": [
    {
      "rank": 1,
      "smiles": "CC1=...",
      "alignment_score": 0.88,
      "similarity_to_reference": 0.71,
      "toxicity_score": 0.11,
      "herg_risk": 0.09,
      "sa_score": 2.9,
      "qed": 0.72,
      "final_score": 0.81,
      "why": "Matches EGFR-inhibitor-like scaffold features while lowering predicted toxicity and maintaining oral-like property profile."
    }
  ]
}
```

---

## 4) Model scope

This spec is for **small-molecule drug discovery**.

That means:
- graph nodes = **atoms**
- graph edges = **chemical bonds** plus optional geometric / pharmacophore relations

This is a better fit for:
- text-conditioned molecule retrieval
- lead optimization
- ADMET-aware reranking
- similar-drug-guided design

The earlier protein-graph idea still matters as a reusable pattern, but this CLI should center on **small molecules** because the user flow is “drug design from text + reference compound.”

---

## 5) Core modeling strategy

## Version 1: multimodal retrieval + ranking + candidate proposal

### Encoder A — molecular graph encoder
Use a graph encoder over molecular graphs:
- atom type, valence, aromaticity, formal charge, chirality, ring membership
- bond type, conjugation, stereochemistry
- optional 3D conformer features if available

### Encoder B — text encoder
Use a biomedical / chemistry-capable text encoder over:
- design goal text
- assay descriptions
- mechanism notes
- ADMET constraint descriptions
- scaffold / medicinal chemistry notes

### Shared embedding space
Train so that matched graph-text pairs are close and mismatched pairs are far.

### Additional heads
Add:
- property prediction heads
- similarity / novelty scoring
- optional pairwise ranker

### Inference pipeline
At inference:
1. Encode `goal_text`
2. Encode `reference_molecule` if provided
3. Search a candidate pool or generator output set
4. Score candidates by:
   - text alignment
   - reference similarity
   - ADMET / toxicity
   - synthesizability
   - novelty
5. Return Top-N

This is analogous to:
- text-to-image retrieval / reranking
- reference-guided generation
- CLIP embedding search

---

## 6) Best graph encoder today for this tool

There is no single universally best graph encoder for every medicinal chemistry task, but the strongest practical family is:

### Tier 1 default
**Message-passing molecular GNN in PyG**, optionally with graph transformer blocks.

Good choices:
- GIN / GINE baseline
- MPNN / AttentiveFP-style baseline
- Graph Transformer / GraphGPS-style upgrade later

### Honest recommendation
For a 0 → 1 CLI product, use:
1. **GINE / MPNN-level encoder first**
2. rich atom / bond featurization
3. optional 3D branch later
4. text alignment as the differentiator

Why:
- easier to train and debug than exotic chemistry foundation models
- straightforward to integrate with PyG
- sufficient to validate the product loop

### Where NVIDIA models fit
NVIDIA’s drug-discovery catalog is useful, but mainly as **supporting models** rather than your core graph encoder. On NVIDIA Build, **ESM2-650M** is a protein embedding model and **OpenFold3 / OpenFold2 / Boltz-2** are structure-prediction models; those are more relevant for protein workflows than for a small-molecule graph backbone. citeturn276799search2

So for *this* CLI:
- use standard molecular GNNs as the main graph encoder
- use NVIDIA biology models only if you later add protein-side conditioning or target-side modeling

---

## 7) Best Python library stack

## Recommendation

### Core graph library
**PyTorch Geometric (PyG)**

Why:
- strongest flexibility for custom molecular graph encoders
- rich ecosystem for GNN experimentation
- easiest path if you want custom ranking / multimodal heads

### Chemistry toolkit
**RDKit**

Why:
- canonical molecular parsing and sanitization
- fingerprints, descriptors, SMARTS filters
- conformer generation
- depiction for CLI outputs

### Text / training stack
- **Transformers** for text encoder
- **PyTorch Lightning** or plain PyTorch for training loops
- **scikit-learn** for metrics and split utilities

### Optional libraries
- **TDC** for benchmark datasets and standard ADMET tasks
- **DeepChem** for chemistry utilities and baseline models
- **FAISS** for nearest-neighbor retrieval in embedding space

### Final library choice
For this CLI, prefer:
- **PyG + RDKit + Transformers + TDC**

PyG is the better long-term choice here than TorchDrug because the product is centered on **small-molecule graph + text alignment**, not protein-native graph abstractions.

---

## 8) Best public datasets to download

There is no single dataset that covers everything. The best setup is **two-layered**:

## A. Best dataset for graph–text pretraining

### Recommended default: PubChemSTM
Use for:
- molecule-text contrastive pretraining
- text / structure retrieval
- learning the shared graph-text embedding space

Why:
- specifically built for **molecule structure + text** alignment
- publicly referenced, reproducible, and already used in MoleculeSTM
- suitable for CLIP-style training on chemical structures and textual descriptions. MoleculeSTM reports over **280,000** structure-text pairs in **PubChemSTM**. citeturn276799search5turn498535search22

### Recommended scale-up option: MolTextNet
Use for:
- larger-scale molecule-text pretraining
- stronger text-conditioned retrieval / ranking

Why:
- much larger recent molecule-text dataset from **ChEMBL35**
- around **2.5 million** molecule-text pairs
- better if you want to train a stronger multimodal foundation model, but newer and less battle-tested than PubChemSTM. citeturn276799academia13

## B. Best dataset family for property fine-tuning / reranking

### Recommended default: TDC ADMET + toxicity tasks
Use for:
- toxicity and ADMET property heads
- standard benchmark splits
- reproducible supervised evaluation

Why:
- TDC provides a broad ecosystem of **AI-ready therapeutic datasets** and benchmark groupings, including toxicity / ADMET tasks and standard data access through Python. citeturn498535search9turn498535search13

### Specific recommended tasks
Start with:
- **Tox21**
- **ClinTox**
- additional TDC ADMET tasks relevant to your design goals

TDC’s toxicity task overview and ADMET benchmark are appropriate for the supervised property heads in this system. citeturn498535search1turn498535search13turn498535search21

## C. Similar-known-drug pool / candidate library
Use:
- **ChEMBL** as the main public candidate and nearest-neighbor library
- optional **PubChem** subset for larger retrieval space

Why:
- contains real drug-like molecules and bioactivity-linked chemistry
- natural source for “similar to known drug” retrieval and scaffold seeding

## Final dataset recommendation
If you want one practical default stack:

### Pretraining
- **PubChemSTM** for graph-text alignment

### Fine-tuning / scoring
- **TDC ADMET / Tox21 / ClinTox** for toxicity and ADMET heads

### Candidate search space
- **ChEMBL** subset filtered for drug-like compounds

### Scale-up option
- replace or augment PubChemSTM with **MolTextNet** later

---

## 9) Dataset quality standard

### Must-have rules
1. Deduplicate by canonical SMILES / InChIKey
2. Split by scaffold, not random rows
3. Keep source dataset provenance
4. Keep property units / assay metadata
5. Remove label conflicts where possible
6. Track train / valid / test leakage via near-neighbor similarity
7. Keep a frozen external test set
8. Mark synthetic text vs human-authored text if mixing datasets

### Recommended split strategy
- Bemis–Murcko scaffold split for small molecules
- optional temporal split where available
- external holdout from a different source

This matters a lot because random splits can inflate performance in medicinal chemistry.

---

## 10) Training method

## Recommended training pipeline

### Stage 1 — graph-text contrastive pretraining
Losses:
- InfoNCE / CLIP-style contrastive loss
- optional graph-text matching loss

Inputs:
- molecule graph
- paired text description

Output:
- aligned embedding space

### Stage 2 — supervised property fine-tuning
Losses:
- BCE / focal loss for binary toxicity tasks
- regression loss for continuous ADMET endpoints where applicable

Heads:
- toxicity
- hERG proxy
- DILI proxy
- solubility / lipophilicity / permeability / oral-like tasks

### Stage 3 — retrieval + reranking training
Train a scorer over:
- text alignment score
- similarity to reference compound
- property scores
- novelty / synthesizability

### Stage 4 — optional candidate generator
Only after the retrieval/scoring stack is working:
- fragment recombination
- scaffold decoration
- diffusion / flow / language-model generation over SMILES or graphs

## Where RL fits
RL is a **phase-2 or phase-3 optimization layer only**.

Use RL only if you later want:
- text-conditioned molecular editing
- multi-objective optimization under hard constraints
- active search over generator proposals

The practical roadmap is:
**alignment + supervised heads → reranker → generator → RL/search**

---

## 11) Candidate generation strategy

Version 1 does **not** need to invent molecules from scratch.

### Recommended v1 strategy
Generate candidates from one or more of:
- nearest neighbors in ChEMBL / PubChem embedding space
- scaffold analog expansion from the reference molecule
- medicinal-chemistry transformations / matched molecular pairs
- fragment replacement templates

Then rerank.

### Why this is smart
This gets you a useful product sooner because:
- outputs are more realistic
- easier to validate
- easier to keep synthesizable
- easier to explain to users

### Version 2 generation
Later add:
- graph diffusion
- SMILES-based generator
- constrained molecular editing

---

## 12) Scoring formula for Top-N design

## Example final score
```text
final_score =
  w_text * text_alignment
+ w_ref  * similarity_to_reference
+ w_prop * property_score
+ w_sa   * synthesizability
+ w_qed  * drug_likeness
+ w_nov  * novelty
- w_tox  * predicted_toxicity
- w_alert * structural_alert_penalty
```

### Default idea
- keep reference similarity in a **moderate band**, not maximum
- reward novelty only after minimum plausibility is met
- hard-filter obvious toxophores or rule violations before ranking

---

## 13) CLI design

## Package name
Example package name:
- `drugclip`

## CLI commands

### 1. Download datasets
```bash
drugclip data download pubchemstm
drugclip data download tdc-tox
drugclip data download chembl
```

### 2. Preprocess
```bash
drugclip data preprocess --config configs/pretrain_pubchemstm.yaml
```

### 3. Train graph-text alignment
```bash
drugclip train align --config configs/align_pubchemstm.yaml
```

### 4. Train property heads
```bash
drugclip train property --config configs/property_tdc.yaml
```

### 5. Build retrieval index
```bash
drugclip index build --molecules data/chembl/filtered.smi --checkpoint runs/align/best.ckpt
```

### 6. Inference / design
```bash
drugclip infer \
  --goal-text "Design a low-toxicity oral kinase inhibitor similar to osimertinib" \
  --reference-smiles "COc1cc..." \
  --top-n 20 \
  --checkpoint runs/final/model.ckpt
```

### 7. Batch inference
```bash
drugclip infer-batch --input prompts/design_tasks.jsonl --output outputs/candidates.jsonl
```

## CLI output artifacts
- ranked JSON / JSONL
- CSV summary
- optional SDF file with top candidates
- optional PNG depictions
- markdown report

---

## 14) Suggested project structure

```text
project/
  drugclip/
    cli.py
    config.py
    data/
      download.py
      preprocess.py
      chembl.py
      pubchemstm.py
      tdc_tasks.py
    featurizers/
      graph.py
      text.py
      descriptors.py
    models/
      graph_encoder.py
      text_encoder.py
      align_model.py
      property_heads.py
      reranker.py
    training/
      train_align.py
      train_property.py
      losses.py
      metrics.py
    inference/
      retrieve.py
      generate.py
      rank.py
      filters.py
      explain.py
    index/
      build_faiss.py
    utils/
      chemistry.py
      io.py
      logging.py
  configs/
    align_pubchemstm.yaml
    property_tdc.yaml
    infer_default.yaml
  tests/
  README.md
```

---

## 15) Minimal model spec

## Graph encoder input
Per atom:
- atom type
- degree
- formal charge
- aromaticity
- hybridization
- chirality
- ring membership

Per bond:
- bond type
- conjugation
- aromatic bond flag
- stereo
- ring bond flag

Optional global features:
- RDKit descriptors
- Morgan fingerprint
- SA / QED

## Text encoder input
- raw design goal text
- optional structured prompt template
- optional target / assay / ADMET constraints

## Embedding heads
- projection MLP for graph embedding
- projection MLP for text embedding
- normalized shared space

## Heads
- binary / multi-task property heads
- pairwise ranker

---

## 16) Inference workflow

### Step 1
Parse text goal into:
- target/mechanism hints
- ADMET constraints
- positive and negative attributes

### Step 2
Resolve reference molecule if given:
- name → SMILES
- sanitize with RDKit

### Step 3
Retrieve initial pool:
- embedding nearest neighbors from ChEMBL
- fingerprint neighbors
- scaffold analogs

### Step 4
Score pool:
- graph-text alignment
- reference similarity
- property heads
- alerts / rule filters

### Step 5
Return Top-N and rationale

---

## 17) Explainability

Add:
- nearest-neighbor examples from training data
- atom / substructure attribution where possible
- reasons for rejection / filtering
- textual explanation of why the candidate matched the prompt

This matters because medicinal chemistry users will want to know **why** a candidate was ranked highly.

---

## 18) Future upgrades

### Phase 2
- text-conditioned molecular editing
- graph diffusion / flow matching candidate generator
- target protein conditioning
- docking-informed reranking

### Phase 3
- active learning loop with wet-lab feedback
- RL or search over generator proposals
- multimodal target + ligand + text modeling

---

## 19) Final recommendation

## Best practical first build

### Core model
- **graph encoder + text encoder + CLIP-style alignment**

### Library stack
- **PyG + RDKit + Transformers + TDC + FAISS**

### Best dataset stack
- **PubChemSTM** for graph-text alignment pretraining
- **TDC ADMET / Tox21 / ClinTox** for property heads
- **ChEMBL** as retrieval / candidate library
- **MolTextNet** as the later scale-up option

### Training method
- contrastive pretraining
- supervised multitask property fine-tuning
- reranker training
- no RL at the beginning

### Product behavior
Input:
- **text design goal**
- optional **similar drug / reference molecule**

Output:
- **Top-N drug candidates** with scores and reasons

That is the most realistic, extensible, and technically grounded starting point.
