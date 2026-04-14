import os
import pandas as pd
from drugclip.utils.chemistry import smiles_to_schnet_data


def get_seed_smiles(max_samples=2000):
    """Helper to get some valid SMILES to act as our 'generative AI' output for the demo."""
    csv_path = "data/chembl/chembl.csv"
    if not os.path.exists(csv_path):
        csv_path = "../DRUG_DISCOVER/data/chembl/chembl.csv"
        if not os.path.exists(csv_path):
            csv_path = "../DRUG_DISCOVER/data/tdc_tox/tox21.csv"

    try:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            print("[*] Local dataset not found, downloading Tox21 sample dataset...")
            df = pd.read_csv(
                "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz"
            )

        col_name = "Drug" if "Drug" in df.columns else "smiles"
        return (
            df[col_name]
            .dropna()
            .sample(min(max_samples, len(df)), random_state=42)
            .tolist()
        )
    except Exception as e:
        print(f"[!] Error loading dataset: {e}")
        return [
            "CC(=O)OC1=CC=CC=C1C(=O)O",
            "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
            "C1=CC=C(C=C1)S(=O)(=O)N",
            "CCOc1ccc(CC(=O)N(C)O)cc1",
            "CCC1(CC)Cc2ccccc2-c2nc(NCCO)[nH]c(=O)c21",
        ]


def process_single_molecule(sm):
    graph_dict = smiles_to_schnet_data(sm, return_dict=True)
    if graph_dict is not None:
        return (sm, graph_dict)
    return None


def normalize_01(tensor):
    """Min-Max Normalize a tensor to [0, 1]"""
    min_val = tensor.min()
    max_val = tensor.max()
    return (tensor - min_val) / (max_val - min_val + 1e-8)
