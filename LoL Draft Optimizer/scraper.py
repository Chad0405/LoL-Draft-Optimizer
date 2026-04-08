import os
import time
import pandas as pd
import requests
import settings as config

# Configuration des dossiers et URLs
os.makedirs("data", exist_ok=True)
BASE = f"https://{config.REGION}.api.riotgames.com"
ROUTING = f"https://{config.REGION_ROUTING}.api.riotgames.com"
HEADERS = {"X-Riot-Token": config.RIOT_API_KEY}

def get_platinum_players(tier="PLATINUM", division="I", page=1):
    url = f"{BASE}/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{division}?page={page}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_match_ids(puuid: str, count: int = 20):
    """Récupère les IDs des matchs (Max 100 par appel)."""
    url = f"{ROUTING}/lol/match/v5/matches/by-puuid/{puuid}/ids"
    params = {"queue": 420, "count": min(count, 100)}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()

def get_match_data(match_id: str) -> dict:
    url = f"{ROUTING}/lol/match/v5/matches/{match_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def extract_champion_pairs(match: dict) -> list[dict]:
    rows = []
    if "info" not in match or "participants" not in match["info"]:
        return []
    
    participants = match["info"]["participants"]
    match_id = match["metadata"]["matchId"]
    
    for p1 in participants:
        for p2 in participants:
            if p1["puuid"] == p2["puuid"]: 
                continue
            rows.append({
                "match_id":  match_id,
                "champ1":    p1["championName"],
                "role1":     p1["teamPosition"],
                "champ2":    p2["championName"],
                "role2":     p2["teamPosition"],
                "same_team": p1["teamId"] == p2["teamId"],
                "win":       p1["win"],
            })
    return rows

if __name__ == "__main__":
    print("💎 Connexion à l'API Riot et récupération des Platines...")
    
    try:
        players = get_platinum_players(tier="PLATINUM", division="II", page=1)
        
        # On traite 5 joueurs pour commencer
        for p_idx, player in enumerate(players[:50]):
            try:
                puuid = player.get('puuid')
                if not puuid: continue

                print(f"\nJoueur {p_idx+1}/50 (PUUID: {puuid[:10]}...)")
                
                # Récupération des IDs de matchs
                m_ids = get_match_ids(puuid, count=40)
                time.sleep(1.2) 
                
                current_player_pairs = []
                for i, mid in enumerate(m_ids):
                    try:
                        match_data = get_match_data(mid)
                        pairs = extract_champion_pairs(match_data)
                        current_player_pairs.extend(pairs)
                        print(f"Match {i+1}/{len(m_ids)} ({mid})", end="\r")
                        time.sleep(1.2)
                    except Exception as e:
                        continue

                # Sauvegarde immédiate (Mode Append)
                if current_player_pairs:
                    df = pd.DataFrame(current_player_pairs)
                    csv_path = "data/pairs.csv"
                    file_exists = os.path.isfile(csv_path)
                    df.to_csv(csv_path, mode='a', index=False, header=not file_exists)
                    print(f"\n{len(current_player_pairs)} paires ajoutées.")

            except Exception as e:
                print(f"\nErreur sur ce joueur : {e}")
                continue

        # --- NETTOYAGE FINAL ---
        if os.path.exists("data/pairs.csv"):
            print("\n🧹 Nettoyage des doublons...")
            final_df = pd.read_csv("data/pairs.csv")
            final_df = final_df.drop_duplicates(subset=['match_id', 'champ1', 'champ2'])
            final_df.to_csv("data/pairs.csv", index=False)
            print(f"Terminé ! Total : {len(final_df)} paires uniques.")

    except Exception as e:
        print(f"Erreur critique : {e}")