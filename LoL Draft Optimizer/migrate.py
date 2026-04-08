# migrate.py — à lancer une seule fois pour migrer les données du CSV vers la base de données
import pandas as pd
from db import init_db, insert_pairs

init_db()
df = pd.read_csv("data/pairs.csv")
df = df.dropna()

batch_size = 1000
for i in range(0, len(df), batch_size):
    batch = df.iloc[i:i+batch_size].to_dict("records")
    insert_pairs(batch)
    print(f"{min(i+batch_size, len(df))}/{len(df)} lignes migrées...", end="\r")

print("\nMigration terminée !")