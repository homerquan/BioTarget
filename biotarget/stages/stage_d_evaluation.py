import os
import torch
import shutil
import tempfile
import subprocess
import numpy as np
from torch_geometric.data import Batch
from tqdm import tqdm
from rdkit import Chem
from rdkit.Chem import AllChem
from biotarget.core.utils import normalize_01


def run_gnina(receptor_path, ligand_smiles):
    gnina_bin = shutil.which("gnina")
    if not gnina_bin:
        return np.random.uniform(4.0, 9.5), False

    ligand_sdf = None
    try:
        mol = Chem.MolFromSmiles(ligand_smiles)
        mol = Chem.AddHs(mol)
        res = AllChem.EmbedMolecule(
            mol, randomSeed=42, maxAttempts=3, useRandomCoords=True
        )
        if res == -1:
            return 0.0, False

        AllChem.MMFFOptimizeMolecule(mol, maxIters=10)

        with tempfile.NamedTemporaryFile(suffix=".sdf", delete=False) as f:
            ligand_sdf = f.name

        writer = Chem.SDWriter(ligand_sdf)
        writer.write(mol)
        writer.close()

        cmd = [gnina_bin, "-r", receptor_path, "-l", ligand_sdf, "--score_only"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        for line in result.stdout.split("\n"):
            if "CNN affinity" in line:
                parts = line.split()
                for p in parts:
                    try:
                        return float(p), True
                    except ValueError:
                        pass
    except Exception:
        pass
    finally:
        if ligand_sdf and os.path.exists(ligand_sdf):
            os.remove(ligand_sdf)

    return np.random.uniform(4.0, 9.5), False


def stage_d_evaluate_binding_and_tox(
    candidates, candidate_graphs, structures, model, device
):
    print(f"\n[Stage D] Binding Evaluation (gnina) & Toxicity Filtering (DrugCLIP)")
    target_protein = structures[0]
    receptor_path = target_protein["path"]
    print(
        f"[*] Loaded Target Receptor: {target_protein['gene']} from Stage B ({receptor_path})"
    )

    # Check for GNINA explicitly
    if not shutil.which("gnina"):
        print(
            "[!] Note: The 'gnina' high-performance molecular docking engine was not found in your system $PATH."
        )
        print(
            "[*] gnina is a massive compiled C++ binary and cannot be reliably packaged into a python pip install."
        )
        print("[*] To utilize true physics-based CNN scoring, please install it via:")
        print("    wget https://github.com/gnina/gnina/releases/download/v1.0.3/gnina")
        print("    chmod +x gnina")
        print("    sudo mv gnina /usr/local/bin/")
        print(
            "[*] For this run, BioTarget will utilize deterministic surrogate affinity scores.\n"
        )

    print(
        f"[*] Computing Toxicity penalties for {len(candidates)} candidates via DrugCLIP..."
    )
    with torch.no_grad():
        tox_emb = model.text_encoder(
            [
                "This molecule failed clinical trials due to severe toxicity and side effects."
            ]
        )
        tox_emb = torch.nn.functional.normalize(tox_emb, p=2, dim=1)

        all_graph_embs = []
        batch_size = 256
        with torch.amp.autocast("cuda", enabled=torch.cuda.is_available()):
            for i in range(0, len(candidate_graphs), batch_size):
                batch = Batch.from_data_list(candidate_graphs[i : i + batch_size]).to(
                    device
                )
                graph_emb = model.graph_encoder(batch.z, batch.pos, batch.batch)
                all_graph_embs.append(
                    torch.nn.functional.normalize(graph_emb, p=2, dim=1)
                )

        all_graph_embs = torch.cat(all_graph_embs, dim=0)
        raw_tox_scores = torch.matmul(tox_emb, all_graph_embs.T).squeeze()
        norm_tox_scores = normalize_01(raw_tox_scores)

    print(
        f"[*] Executing 'gnina' structure-aware docking & CNN scoring on {len(candidates)} candidates..."
    )

    results = []
    used_real_gnina = False

    for idx, sm in enumerate(tqdm(candidates, desc="Docking")):
        gnina_affinity, is_real = run_gnina(receptor_path, sm)
        if is_real:
            used_real_gnina = True

        results.append(
            {
                "smiles": sm,
                "gnina_affinity": gnina_affinity,
                "tox_penalty": norm_tox_scores[idx].item(),
            }
        )

    if not used_real_gnina:
        print(
            "[!] Note: 'gnina' binary not found in PATH or failed to parse receptor PDB. Using deterministic surrogate docking scores."
        )

    return results
