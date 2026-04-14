import requests


def stage_a_target_discovery(disease):
    print(f"\n[Stage A] Disease -> Protein Target Ranking")
    print(f"[*] Querying Open Targets Platform for '{disease}'...")

    # 1. Search for disease to get the best matching EFO/MONDO ID
    search_query = (
        """
    query { 
      search(queryString: "%s", entityNames: ["disease"]) { 
        hits { id name } 
      } 
    }
    """
        % disease
    )

    try:
        response = requests.post(
            "https://api.platform.opentargets.org/api/v4/graphql",
            json={"query": search_query},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        hits = data.get("data", {}).get("search", {}).get("hits", [])

        if not hits:
            print(f"[!] No disease found for '{disease}'. Using fallback mock data.")
            return _mock_targets()

        best_disease_id = hits[0]["id"]
        best_disease_name = hits[0]["name"]
        print(f"[*] Found disease match: {best_disease_name} ({best_disease_id})")

        # 2. Get associated targets for this disease (with Uniprot IDs)
        targets_query = (
            """
        query { 
          disease(efoId: "%s") { 
            associatedTargets(page: {index: 0, size: 10}) { 
              rows { 
                target { 
                  id 
                  approvedSymbol 
                  approvedName 
                  proteinIds { id source }
                } 
                score 
              } 
            } 
          } 
        }
        """
            % best_disease_id
        )

        response = requests.post(
            "https://api.platform.opentargets.org/api/v4/graphql",
            json={"query": targets_query},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        rows = (
            data.get("data", {})
            .get("disease", {})
            .get("associatedTargets", {})
            .get("rows", [])
        )

        targets = []
        for row in rows:
            target_info = row.get("target", {})

            # Find Uniprot ID
            uniprot_id = None
            for p_id in target_info.get("proteinIds", []):
                if p_id.get("source") == "uniprot_swissprot":
                    uniprot_id = p_id.get("id")
                    break

            if not uniprot_id:
                # Fallback to the first available if swissprot not found
                if target_info.get("proteinIds"):
                    uniprot_id = target_info.get("proteinIds")[0].get("id")

            targets.append(
                {
                    "protein_id": uniprot_id or target_info.get("id"),
                    "gene": target_info.get("approvedSymbol"),
                    "score_opentargets": row.get("score"),
                }
            )

        if not targets:
            print(
                f"[!] No targets found for disease ID {best_disease_id}. Using fallback mock data."
            )
            return _mock_targets()

        print(f"[*] Found {len(targets)} highly ranked targets.")
        return targets

    except Exception as e:
        print(f"[!] API Request failed: {e}. Using fallback mock data.")
        return _mock_targets()


def _mock_targets():
    return [
        {"protein_id": "P04062", "gene": "GBA", "score_opentargets": 0.95},
        {"protein_id": "Q5S007", "gene": "LRRK2", "score_opentargets": 0.88},
        {"protein_id": "P37840", "gene": "SNCA", "score_opentargets": 0.82},
    ]
