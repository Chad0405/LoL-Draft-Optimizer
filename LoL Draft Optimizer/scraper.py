import os
import time
import requests
import settings as config
from db import init_db, insert_pairs

BASE    = f"https://{config.REGION}.api.riotgames.com"
ROUTING = f"https://{config.REGION_ROUTING}.api.riotgames.com"
HEADERS = {"X-Riot-Token": config.RIOT_API_KEY}

def get_platinum_players(tier="PLATINUM", division="I", page=1):
    url = f"{BASE}/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{division}?page={page}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_match_ids(puuid: str, count: int = 20):
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
    if "info" not in match or "participants" not in match["info"]:
        return []
    rows = []
    participants = match["info"]["participants"]
    match_id     = match["metadata"]["matchId"]
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
    init_db()  # crée la table si besoin
    print("Récupération des joueurs Platinum...")

    players = get_platinum_players(tier="PLATINUM", division="III", page=1)

    for p_idx, player in enumerate(players[:5]):
        try:
            puuid = player.get("puuid")
            if not puuid:
                continue

            print(f"\nJoueur {p_idx+1}/50 (PUUID: {puuid[:10]}...)")
            m_ids = get_match_ids(puuid, count=40)
            time.sleep(1.2)

            for i, mid in enumerate(m_ids):
                try:
                    match_data = get_match_data(mid)
                    pairs      = extract_champion_pairs(match_data)
                    insert_pairs(pairs)  # direct en DB, plus de CSV
                    print(f"  Match {i+1}/{len(m_ids)} — {len(pairs)} paires insérées", end="\r")
                    time.sleep(1.2)
                except Exception as e:
                    continue

        except Exception as e:
            print(f"Erreur joueur : {e}")
            continue

    print("\nScraping terminé.")
