# BioTarget: End-to-End AI Drug Discovery Pipeline 🧬💊

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![GNINA](https://img.shields.io/badge/GNINA-Molecular_Docking-orange.svg)](https://github.com/gnina/gnina)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

BioTarget is a state-of-the-art, open-source CLI pipeline designed to accelerate the early stages of the AI drug-discovery workflow. It seamlessly links target discovery, 3D protein structure prediction, deep-learning-based contrastive molecular screening, and physics-based CNN docking into a single cohesive framework.

The pipeline leverages **DrugCLIP** (a dual-encoder graph-text architecture) to act as a generative filter for toxicity and therapeutic intent, and **gnina** for structure-aware binding affinity predictions.

After install, simply use it by one command:
```bash
python biotarget/cli.py run full \
  --disease "Alzheimer" --top-ligands 20
```

For more info, visit [BioTarget on GitHub](https://github.com/homerquan/biotarget).

---

## 🎯 The Pipeline Architecture

BioTarget executes a 5-stage workflow designed for rapid, iterative drug discovery:

### 1. Stage A: Disease $\rightarrow$ Target Ranking
Retrieves and ranks disease-relevant protein targets by querying extensive biomedical knowledge graphs.
* **Sources:** Open Targets Platform, DisGeNET, STRING, Reactome.
* **Methodology:** Ranks protein targets via heterogeneous Graph Neural Networks (GNN) and biological pathway evidence mapping.

### 2. Stage B: Protein Structure Generation
Fetches or predicts the 3D conformation of the selected target proteins.
* **Primary:** Experimental structures (PDB).
* **Generator:** [OpenFold-3](https://github.com/aqlaboratory/openfold) for de novo prediction of variants, mutants, or unmapped isoforms.

### 3. Stage C: Generative AI & Candidate Extraction
Instead of blindly docking massive lookup libraries (like ChEMBL), BioTarget employs a highly optimized generative filtering approach.
* **DrugCLIP Guidance:** Thousands of virtual compounds are geometrically folded on the CPU array. `DrugCLIP` encodes a textual representation of the disease and isolates the Top 10× geometrically/semantically aligned molecular structures.

### 4. Stage D: Multi-Objective Binding & Toxicity Evaluation
Evaluates candidates simultaneously for efficacy (physics/CNN docking) and safety (latent space contrastive geometry).
* **Binding Evaluation (`gnina`)**: Generates 3D structural Spatial Data Files (`.sdf`) via RDKit and calls the actual `gnina` subprocess. Evaluates ligand-receptor binding affinity using Convolutional Neural Networks on voxelized binding sites.
* **Toxicity Penalty (`DrugCLIP`)**: Computes semantic embedding for clinical failure and calculates the normalized Cosine Similarity against the ligand's structural embedding.

### 5. Stage E: Ranking & Reporting
* **Final Ranking**: $\mathcal{S}_{final} = \mathcal{S}_{binding} - (0.5 \cdot \mathcal{S}_{tox})$
Aggregates hits, flags highly toxic compounds (⚠️), and outputs a ranked manifest of candidate SMILES ready for Molecular Dynamics (MD) refinement via OpenMM.

---

## 🚀 Installation & Setup

BioTarget requires Python 3.9+ and leverages PyTorch for its deep learning models. Follow these steps to get a fully functioning environment.

### 1. Base Installation

```bash
# Clone the repository
git clone https://github.com/homerquan/biotarget.git
cd biotarget

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the base dependencies
pip install -r requirements.txt
```

### 2. Install DrugCLIP (Required)

BioTarget relies on a specialized, multi-modal package called `drugclip` to handle the graph-text contrastive filtering.

```bash
pip install git+https://github.com/homerquan/drugclip.git
```
*(Note: If `drugclip` is not yet public, you will need the appropriate SSH keys or access tokens configured on your machine, or you must place the package locally in your `PYTHONPATH`)*

### 3. External Dependencies (Required)

Due to licensing and packaging constraints for massive C++ binaries, `gnina` is automatically installed during the pip setup process if you have an NVIDIA GPU. 

#### GNINA (Physics-Based Binding Evaluation)
For **Stage D** to execute high-accuracy CNN molecular docking, the `gnina` binary is **required**. BioTarget will automatically download and install `gnina` when you install the package using pip, provided you meet the hardware requirements.

**Hardware Requirements:**
* **NVIDIA GPU is mandatory** for `gnina` to run.
* `nvcc` or `nvidia-smi` must be accessible in your `$PATH` during the `pip install` process. If an NVIDIA GPU is not detected, the installation will fail with an error.

*(Note: Docker or macOS fallbacks are no longer supported. You must run this pipeline on a Linux machine with an NVIDIA GPU.)*

#### OpenFold-3 / AlphaFold DB (Protein Structure Prediction)
For **Stage B**, the pipeline attempts to fetch validated 3D structures.
* By default, the pipeline has been upgraded to automatically pull `.pdb` files from the **AlphaFold Protein Structure Database** via their API.
* If you specifically need to fold novel variants *de novo*, you will need OpenFold-3 weights. These fall under a strict CC-BY-NC license. Request access via [AQLaboratory/OpenFold](https://github.com/aqlaboratory/openfold) and place the `.pt` files in `~/.biotarget/openfold3_weights/`.

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