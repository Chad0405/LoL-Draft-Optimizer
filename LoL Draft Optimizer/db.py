import psycopg2
import psycopg2.extras
import settings as config

def get_conn():
    return psycopg2.connect(config.DB_URL)

def init_db():
    """Crée la table si elle n'existe pas + index pour les performances."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
    CREATE TABLE IF NOT EXISTS champion_pairs (
        id        SERIAL PRIMARY KEY,
        match_id  TEXT NOT NULL,
        champ1    TEXT NOT NULL,
        role1     TEXT,
        champ2    TEXT NOT NULL,
        role2     TEXT,
        same_team BOOLEAN NOT NULL,
        win       BOOLEAN NOT NULL,
        CONSTRAINT idx_unique_pair UNIQUE (match_id, champ1, champ2)
    );
    CREATE INDEX IF NOT EXISTS idx_champ1
        ON champion_pairs(champ1);
    CREATE INDEX IF NOT EXISTS idx_champ1_champ2
        ON champion_pairs(champ1, champ2, same_team);
""")
        conn.commit()
    print("Base de données initialisée.")

def insert_pairs(pairs: list[dict]):
    """Insert en bulk, ignore les doublons (ON CONFLICT DO NOTHING)."""
    if not pairs:
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO champion_pairs
                    (match_id, champ1, role1, champ2, role2, same_team, win)
                VALUES %s
                ON CONFLICT ON CONSTRAINT idx_unique_pair DO NOTHING
                """,
                [(p["match_id"], p["champ1"], p["role1"],
                  p["champ2"], p["role2"], p["same_team"], p["win"])
                 for p in pairs],
            )
        conn.commit()

def get_all_champions() -> list[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT champ1 FROM champion_pairs ORDER BY champ1")
            return [row[0] for row in cur.fetchall()]

def query_pairs(champ1: str, champ2: str, same_team: bool, role2: str = None):
    """Retourne win rate et count pour une paire donnée."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            if role2 and role2 != "AUTO":
                cur.execute("""
                    SELECT COUNT(*), AVG(win::int)
                    FROM champion_pairs
                    WHERE champ1 = %s AND champ2 = %s
                      AND same_team = %s AND role2 = %s
                """, (champ1, champ2, same_team, role2))
            else:
                cur.execute("""
                    SELECT COUNT(*), AVG(win::int)
                    FROM champion_pairs
                    WHERE champ1 = %s AND champ2 = %s
                      AND same_team = %s
                """, (champ1, champ2, same_team))
            row = cur.fetchone()
            count = row[0] or 0
            avg   = row[1] or 0.0
            return count, avg

def get_candidates(target_role: str = None) -> list[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            if target_role and target_role != "AUTO":
                cur.execute("""
                    SELECT DISTINCT champ1 FROM champion_pairs
                    WHERE role1 = %s ORDER BY champ1
                """, (target_role,))
            else:
                cur.execute("SELECT DISTINCT champ1 FROM champion_pairs ORDER BY champ1")
            return [row[0] for row in cur.fetchall()]