import pandas as pd
import numpy as np
import joblib
import os
from db import get_candidates
from features import build_feature_vector, get_global_winrates, get_winrate_by_role

MODEL_PATH = "models/xgboost_draft.pkl"

def compute_scores(ally_data, enemy_data, target_role=None):
    # Charge le modèle si disponible, sinon fallback sur la moyenne
    use_model = os.path.exists(MODEL_PATH)
    if use_model:
        model      = joblib.load(MODEL_PATH)
        feat_cols  = joblib.load("models/feature_cols.pkl")
        global_wr  = get_global_winrates()
        role_wr    = get_winrate_by_role()
    
    candidates = get_candidates(target_role)
    scores = {}

    for candidate in candidates:
        if use_model:
            # Scoring via XGBoost
            fv    = build_feature_vector(candidate, ally_data, enemy_data,
                                         target_role or "", global_wr, role_wr)
            X     = pd.DataFrame([fv])[feat_cols].fillna(0)
            proba = model.predict_proba(X)[0][1]  # probabilité de victoire
            scores[candidate] = proba * 100
        else:
            # Fallback : moyenne simple (ancien système)
            from db import query_pairs
            all_rates = []
            for ally in ally_data:
                count, wr = query_pairs(candidate, ally["champ"], same_team=True)
                if count >= 3:
                    all_rates.append(wr)
            for en in enemy_data:
                count, wr = query_pairs(candidate, en["champ"], same_team=False)
                if count >= 3:
                    all_rates.append(wr)
            if all_rates:
                scores[candidate] = (sum(all_rates) / len(all_rates)) * 100

    return pd.Series(scores).sort_values(ascending=False)
