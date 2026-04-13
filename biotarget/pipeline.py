import torch
import os
from drugclip.models.align_model import DrugCLIP
from drugclip.utils.model_utils import get_default_checkpoint

from biotarget.core.config import DEVICE
from biotarget.stages.stage_a_discovery import stage_a_target_discovery
from biotarget.stages.stage_b_structure import stage_b_structure_generation
from biotarget.stages.stage_c_generative import stage_c_generative_ai
from biotarget.stages.stage_d_evaluation import stage_d_evaluate_binding_and_tox
from biotarget.stages.stage_e_reporting import stage_e_reporting

def run_pipeline(disease, checkpoint_path=None, top_ligands=10):
    resolved_ckpt = get_default_checkpoint(checkpoint_path)
    if not resolved_ckpt:
        print("[!] DrugCLIP Checkpoint could not be loaded from Hugging Face.")
        return

    # Load DrugCLIP Model
    model = DrugCLIP(hidden_channels=64, out_dim=128, text_model="distilbert-base-uncased")
    model.load_state_dict(torch.load(resolved_ckpt, map_location=DEVICE, weights_only=True))
    model = model.to(DEVICE)
    model.eval()

    # Stage A: Disease to Protein Ranking
    targets = stage_a_target_discovery(disease)

    # Stage B: Target Structure Generation
    structures = stage_b_structure_generation(targets[:1], engine="openfold3")

    # Stage C: Generative AI (10x Candidates via DrugCLIP guidance)
    num_candidates_needed = top_ligands * 10
    candidates_smiles, candidate_graphs = stage_c_generative_ai(
        disease, model, DEVICE, num_candidates_needed
    )

    # Stage D: Gnina Binding & DrugCLIP Toxicity Evaluation
    evaluation_results = stage_d_evaluate_binding_and_tox(
        candidates_smiles, candidate_graphs, structures, model, DEVICE
    )

    # Stage E: Ranking and Reporting
    stage_e_reporting(disease, evaluation_results, top_ligands)
