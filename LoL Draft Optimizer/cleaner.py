import pandas as pd
import os

def clean_data():
    file_path = "data/pairs.csv"
    
    if not os.path.exists(file_path):
        print("Fichier pairs.csv introuvable.")
        return

    # 1. Charger les données
    df = pd.read_csv(file_path)
    initial_count = len(df)
    print(f"📊 Lignes avant nettoyage : {initial_count}")

    # 2. Supprimer les doublons exacts
    # On se base sur l'ID du match et les noms des champions pour identifier une ligne unique
    df = df.drop_duplicates(subset=['match_id', 'champ1', 'champ2'])
    
    final_count = len(df)
    print(f"✨ Lignes après nettoyage : {final_count}")
    print(f"🗑️ Doublons supprimés : {initial_count - final_count}")

    # 3. (Optionnel) Supprimer les lignes avec des données manquantes
    df = df.dropna()

    # 4. Sauvegarder le fichier propre
    df.to_csv(file_path, index=False)
    print("✅ Données nettoyées et sauvegardées !")

if __name__ == "__main__":
    clean_data()