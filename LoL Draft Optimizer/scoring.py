from db import get_candidates, query_pairs
import pandas as pd

def compute_scores(ally_data, enemy_data, target_role=None):
    candidates = get_candidates(target_role)
    scores = {}

    for candidate in candidates:
        all_rates = []

        # Synergies avec les alliés
        for ally in ally_data:
            count, wr = query_pairs(candidate, ally["champ"], same_team=True, role2=ally["role"])
            if count >= 4:
                all_rates.append(float(wr))

        # Matchups contre les ennemis
        for en in enemy_data:
            count, wr = query_pairs(candidate, en["champ"], same_team=False, role2=en["role"])
            if count >= 4:
                all_rates.append(float(wr))

        # Calcul du score final
        if all_rates:
            # Maintenant sum() ne plantera plus car tous les éléments sont des floats
            scores[candidate] = (sum(all_rates) / len(all_rates)) * 100

    return pd.Series(scores).sort_values(ascending=False)
