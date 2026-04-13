import time

def stage_a_target_discovery(disease):
    print(f"\n[Stage A] Disease -> Protein Target Ranking")
    print(f"[*] Querying Open Targets & DisGeNET for '{disease}'...")
    time.sleep(1)  # Simulate API call
    targets = [
        {"protein_id": "P04062", "gene": "GBA", "score_opentargets": 0.95},
        {"protein_id": "Q5S007", "gene": "LRRK2", "score_opentargets": 0.88},
        {"protein_id": "P37840", "gene": "SNCA", "score_opentargets": 0.82},
    ]
    print(f"[*] Found {len(targets)} highly ranked targets.")
    return targets
