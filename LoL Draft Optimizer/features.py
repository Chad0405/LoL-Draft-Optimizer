import pandas as pd
import numpy as np
from db import get_conn

def get_global_winrates() -> dict:
    """Winrate global de chaque champion."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT champ1, COUNT(*) as nb, AVG(win::int) as wr
                FROM champion_pairs
                GROUP BY champ1
            """)
            return {row[0]: {"nb": row[1], "wr": float(row[2])} for row in cur.fetchall()}

def get_winrate_by_role() -> dict:
    """Winrate par champion + rôle."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT champ1, role1, COUNT(*) as nb, AVG(win::int) as wr
                FROM champion_pairs
                WHERE role1 != ''
                GROUP BY champ1, role1
            """)
            result = {}
            for row in cur.fetchall():
                result[(row[0], row[1])] = {"nb": row[2], "wr": float(row[3])}
            return result

def build_feature_vector(candidate: str, ally_data: list, enemy_data: list,
                          target_role: str, global_wr: dict, role_wr: dict) -> dict:
    """
    Construit un vecteur de features pour un champion candidat.
    ally_data/enemy_data : [{"champ": "Nom", "role": "ROLE"}]
    """
    features = {}

    # 1. Winrate global
    gwr = global_wr.get(candidate, {})
    features["wr_global"]    = gwr.get("wr", 0.5)
    features["nb_matchs"]    = gwr.get("nb", 0)

    # 2. Winrate sur le rôle cible
    rwr = role_wr.get((candidate, target_role), {})
    features["wr_role"]      = rwr.get("wr", features["wr_global"])
    features["nb_role"]      = rwr.get("nb", 0)

    # 3. Synergies avec les alliés
    with get_conn() as conn:
        with conn.cursor() as cur:
            syn_rates = []
            for ally in ally_data:
                cur.execute("""
                    SELECT COUNT(*), AVG(win::int)
                    FROM champion_pairs
                    WHERE champ1 = %s AND champ2 = %s AND same_team = TRUE
                """, (candidate, ally["champ"]))
                row = cur.fetchone()
                if row[0] and row[0] >= 3:
                    syn_rates.append(float(row[1]))

            features["wr_synergie_moy"] = np.mean(syn_rates) if syn_rates else features["wr_global"]
            features["nb_synergies"]    = len(syn_rates)

            # 4. Counter contre les ennemis
            ctr_rates = []
            for en in enemy_data:
                cur.execute("""
                    SELECT COUNT(*), AVG(win::int)
                    FROM champion_pairs
                    WHERE champ1 = %s AND champ2 = %s AND same_team = FALSE
                """, (candidate, en["champ"]))
                row = cur.fetchone()
                if row[0] and row[0] >= 3:
                    ctr_rates.append(float(row[1]))

            features["wr_counter_moy"] = np.mean(ctr_rates) if ctr_rates else features["wr_global"]
            features["nb_counters"]    = len(ctr_rates)

    # 5. Score composition AP/AD (simple)
    ap_champs = {"Lux", "Syndra", "Orianna", "Viktor", "Cassiopeia", "Twisted Fate",
                 "Ahri", "Zoe", "Veigar", "Annie", "Brand", "Heimerdinger"}
    ally_names = [a["champ"] for a in ally_data]
    ap_count   = sum(1 for c in ally_names if c in ap_champs)
    features["team_ap_ratio"] = ap_count / max(len(ally_names), 1)

    return features

def build_training_dataset():
    print("Chargement des données...")
    with get_conn() as conn:
        df = pd.read_sql("""
            SELECT match_id, champ1, role1, champ2, role2, same_team, win
            FROM champion_pairs ORDER BY RANDOM() LIMIT 100000
        """, conn)

    print(f"{len(df)} lignes chargées. Construction des features...")
    global_wr = get_global_winrates()
    role_wr   = get_winrate_by_role()

    # Précalcul des synergies et counters en mémoire (évite les requêtes SQL par champion)
    print("Précalcul des synergies...")
    syn_df = df[df["same_team"] == True].groupby(["champ1", "champ2"])["win"].agg(["count", "mean"]).reset_index()
    syn_df.columns = ["champ1", "champ2", "count", "wr"]
    syn_lookup = {(r.champ1, r.champ2): (r["count"], r["wr"]) for _, r in syn_df.iterrows()}

    ctr_df = df[df["same_team"] == False].groupby(["champ1", "champ2"])["win"].agg(["count", "mean"]).reset_index()
    ctr_df.columns = ["champ1", "champ2", "count", "wr"]
    ctr_lookup = {(r.champ1, r.champ2): (r["count"], r["wr"]) for _, r in ctr_df.iterrows()}

    ap_champs = {"Lux","Syndra","Orianna","Viktor","Cassiopeia","TwistedFate",
                 "Ahri","Zoe","Veigar","Annie","Brand"}

    rows = []
    matches = df.groupby("match_id")
    total = len(matches)

    for i, (match_id, group) in enumerate(matches):
        if i % 200 == 0:
            print(f"  {i}/{total} matchs traités...", end="\r")

        allies_group  = group[group["same_team"] == True]
        enemies_group = group[group["same_team"] == False]

        for _, p in allies_group.iterrows():
            candidate = p["champ1"]
            allies    = [c for c in allies_group["champ1"].unique() if c != candidate]
            enemies   = enemies_group["champ1"].unique().tolist()

            # Features globales
            gwr = global_wr.get(candidate, {})
            rwr = role_wr.get((candidate, p["role1"]), {})

            # Synergies depuis le lookup mémoire
            syn_rates = [syn_lookup[(candidate, a)][1] for a in allies
                         if (candidate, a) in syn_lookup and syn_lookup[(candidate, a)][0] >= 3]

            # Counters depuis le lookup mémoire
            ctr_rates = [ctr_lookup[(candidate, e)][1] for e in enemies
                         if (candidate, e) in ctr_lookup and ctr_lookup[(candidate, e)][0] >= 3]

            ap_count = sum(1 for c in allies if c in ap_champs)

            rows.append({
                "wr_global":        gwr.get("wr", 0.5),
                "nb_matchs":        gwr.get("nb", 0),
                "wr_role":          rwr.get("wr", gwr.get("wr", 0.5)),
                "nb_role":          rwr.get("nb", 0),
                "wr_synergie_moy":  float(np.mean(syn_rates)) if syn_rates else gwr.get("wr", 0.5),
                "nb_synergies":     len(syn_rates),
                "wr_counter_moy":   float(np.mean(ctr_rates)) if ctr_rates else gwr.get("wr", 0.5),
                "nb_counters":      len(ctr_rates),
                "team_ap_ratio":    ap_count / max(len(allies), 1),
                "champion":         candidate,
                "win":              int(p["win"]),
            })

    print(f"\n{len(rows)} exemples construits.")
    return pd.DataFrame(rows)