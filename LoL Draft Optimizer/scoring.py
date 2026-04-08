import pandas as pd

def compute_scores(pairs_df, ally_data, enemy_data, target_role=None):
    scores = {}
    
    # 1. Filtrage des candidats par ton rôle
    if target_role and target_role != "AUTO":
        candidates = pairs_df[pairs_df["role1"] == target_role]["champ1"].unique()
    else:
        candidates = pairs_df["champ1"].unique()

    for candidate in candidates:
        all_rates = []

        # 2. Synergies (Alliés)
        for ally in ally_data:
            # On cherche dans les deux sens (Candidat-Allié ou Allié-Candidat)
            mask = (
                ((pairs_df["champ1"] == candidate) & (pairs_df["champ2"] == ally["champ"])) |
                ((pairs_df["champ1"] == ally["champ"]) & (pairs_df["champ2"] == candidate))
            ) & (pairs_df["same_team"] == True)
            
            if ally["role"] != "AUTO":
                # On vérifie le rôle du partenaire
                mask &= ((pairs_df["role1"] == ally["role"]) | (pairs_df["role2"] == ally["role"]))
            
            sub = pairs_df[mask]
            # ON MONTE LE SEUIL À 10 POUR ÉVITER LES 100% WR SUR 1 MATCH
            if len(sub) >= 10: 
                all_rates.append(sub["win"].mean())

        # 3. Counters (Ennemis)
        for en in enemy_data:
            # IMPORTANT : Ici on ne cherche que Candidate = champ1 
            # pour être sûr que la colonne 'win' correspond bien à NOTRE victoire
            mask = (pairs_df["champ1"] == candidate) & \
                   (pairs_df["champ2"] == en["champ"]) & \
                   (pairs_df["same_team"] == False)
            
            if en["role"] != "AUTO":
                mask &= (pairs_df["role2"] == en["role"])
            
            sub = pairs_df[mask]
            if len(sub) >= 10: # Seuil de sécurité
                all_rates.append(sub["win"].mean())

        # 4. Calcul de la moyenne des probabilités
        if all_rates:
            scores[candidate] = (sum(all_rates) / len(all_rates)) * 100

    return pd.Series(scores).sort_values(ascending=False)