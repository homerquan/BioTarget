# BioTarget: End-to-End AI Drug Discovery Pipeline 🧬💊

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![GNINA](https://img.shields.io/badge/GNINA-Molecular_Docking-orange.svg)](https://github.com/gnina/gnina)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

BioTarget is a state-of-the-art, open-source CLI pipeline designed to accelerate the early stages of the AI drug-discovery workflow. It seamlessly links target discovery, 3D protein structure prediction, deep-learning-based contrastive molecular screening, and physics-based CNN docking into a single cohesive framework.

**[▶️ Watch the demo on YouTube](https://youtu.be/XHGxoba29H0)**

The pipeline leverages **DrugCLIP** (a dual-encoder graph-text architecture) to act as a generative filter for toxicity and therapeutic intent, and **gnina** for structure-aware binding affinity predictions.

After install, simply use it by one command:
```bash
python biotarget/cli.py run full \
  --disease "Alzheimer" --top-ligands 20
```

For more info, visit [BioTarget on GitHub](https://github.com/homerquan/biotarget).

---

## 🚀 Installation & Setup

BioTarget requires Python 3.9+ and PyTorch.

### 0. Install GNINA (Docker-based dependency)

Before installing Python dependencies, set up the GNINA Docker environment:

```bash
chmod +x scripts/install_gnina_docker.sh
./scripts/install_gnina_docker.sh
```

**Requirements:**
- Docker installed and running  
- NVIDIA GPU recommended  
- `nvidia-container-toolkit` for GPU acceleration  

---

### 1. Base Installation

```bash
git clone https://github.com/homerquan/biotarget.git
cd biotarget

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

### 2. Install DrugCLIP

```bash
pip install git+https://github.com/homerquan/drugclip.git
```

---

### 3. Protein Structure Sources

- Default: AlphaFold Protein Structure Database  
- Optional: OpenFold weights placed in:

```bash
~/.biotarget/openfold3_weights/
```

---

## 🔬 Running the Pipeline

```bash
biotarget run full \
  --disease "Alzheimer" \
  --target-model hetero-gnn \
  --structure-engine openfold3 \
  --binding-engine gnina \
  --top-ligands 10
```

---

## 🧩 Pipeline Architecture

### Stage A: Disease → Target Ranking

- Data: Open Targets, DisGeNET, STRING, Reactome  
- Method: heterogeneous graph neural networks  

---

### Stage B: Protein Structure Generation

- PDB structures when available  
- OpenFold predictions otherwise  

---

### Stage C: Candidate Generation

- Text to candidate drug molecules(a graph). We are using a trained model `DrugCLIP` (Project page) [https://github.com/homerquan/DrugCLIP]  
- Produces filtered candidate set  

---

### Stage D: Binding and Toxicity Evaluation

- GNINA docking (CNN-based scoring)  
- Embedding-based toxicity proxy  

---

### Stage E: Ranking

Final score:

S_final = S_binding - 0.5 * S_tox

Outputs ranked candidate molecules for downstream simulation. **Note**: the binding score is rough estimate, only useful to filter out bad candidates.

---

## 🔬 Running the BioTarget Pipeline

The pipeline is invoked via the unified `biotarget/cli.py` orchestrator (or via the `biotarget` command if installed globally).

To execute the end-to-end pipeline for a specific disease:

```bash
python biotarget/cli.py run full \
  --disease "Alzheimer" \
  --target-model hetero-gnn \
  --structure-engine openfold3 \
  --binding-engine gnina \
  --top-targets 3 \
  --top-ligands 10
```

### Example Output
```text
[Stage A] Disease -> Protein Target Ranking
[*] Querying Open Targets & DisGeNET for 'Alzheimer'...
[*] Found 3 highly ranked targets.

[Stage B] Protein Structure Generation
[*] Using engine: openfold3
[*] Folding GBA (P04062) with OpenFold-3...

[Stage C] Generative AI: De Novo Candidate Generation
[*] Generating 3000 de novo molecular structures...
[*] Generating 3D conformers for the generative pool using 64 CPU cores...
[*] Using DrugCLIP to guide selection of the top 100 generated candidates...
[*] Successfully finalized 10x generative candidate pool (N=100).

[Stage D] Binding Evaluation (gnina) & Toxicity Filtering (DrugCLIP)
[*] Loaded Target Receptor: GBA from Stage B (/runs/structures/GBA_openfold3.pdb)
[*] Computing Toxicity penalties for 100 candidates via DrugCLIP...
[*] Executing 'gnina' structure-aware docking & CNN scoring on 100 candidates...

[Stage E] Reporting
=====================================================================================
BIOTARGET PIPELINE FINAL RESULTS FOR: 'Alzheimer'
=====================================================================================
Rank  | Final  | Gnina (pK_d) | Tox Penalty   | SMILES
-------------------------------------------------------------------------------------
#1    | 0.9944 | 9.4457 (0.99) | 0.0000 OK      | CCC1(C(C)(C)C)CCOC1=O...
#2    | 0.8108 | 8.9903 (0.91) | 0.2005 OK      | COc1ccccc1N=C(S)N(CCN1CCOCC1)Cc1ccc...
#3    | 0.7631 | 9.2345 (0.96) | 0.3852 OK      | CCOC(=O)C1CCCN(c2c(NCCCN(C)Cc3ccccc...
#4    | 0.5101 | 8.8713 (0.87) | 0.7225 ⚠️ HIGH | CCCC(N=C(S)NCC1CCCO1)C12CC3CC(CC(C3...
```

---

## 🛠 Model Extensibility (The Roadmap)

While this framework establishes the AI-driven core, it is intentionally modular to support the integration of downstream biophysics tools:
* **Generative Expansion:** Swapping the simulated candidate subset for an active autoregressive/diffusion generative model to perform closed-loop optimization.
* **MD Refinement:** Automated hand-off of the top $K$ hits to OpenMM for physical stability analysis and short MD relaxation.
