import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from biotarget.stages.stage_d_evaluation import run_gnina

receptor_path = os.path.abspath("./runs/structures/EGFR_P00533.pdb")
ligand_smiles = "CCCCCCCCCCCCCCCBr"

print("Running gnina...")
score, success = run_gnina(receptor_path, ligand_smiles)
print(f"Score: {score}, Success: {success}")
