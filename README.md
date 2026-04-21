# LoL Draft Optimizer — Neural-Synergy

LoL Draft Optimizer est un outil d'aide à la décision (Prescriptive Analytics) 
pour la phase de sélection des champions (Draft) dans League of Legends. 
En s'appuyant sur les données réelles de l'API Riot Games et un modèle 
de Machine Learning entraîné sur plus de 600 000 paires de champions, 
l'outil recommande le meilleur pick en fonction des synergies alliées 
et des counter-picks ennemis.

## Objectifs du projet

L'objectif principal est de transformer des données de match brutes en 
indicateurs d'aide à la décision. L'outil évalue la pertinence d'un champion 
en fonction de ses statistiques historiques de performance, de ses synergies 
avec les alliés déjà pickés, et de ses confrontations directes face à la 
composition adverse.

## Fonctionnalités

- **Moteur de recommandation ML** : Modèle XGBoost entraîné sur les données 
  réelles (AUC-ROC : 0.626) produisant une probabilité de victoire par champion. 
  Les données de synergies et de counters sont mises en cache RAM au démarrage 
  pour des recommandations instantanées (<0.5s).
- **Extraction et ingénierie des données** : Automatisation de la récupération 
  via l'API Riot Games (Match-V5, région EUW) et traitement des objets JSON.
- **Pipeline de stockage** : Structuration des données dans une base PostgreSQL 
  avec indexation optimisée pour les requêtes de synergies (temps de réponse < 50ms).
- **Feature Engineering** : Construction de 9 variables prédictives par champion :
  - Winrate global et winrate par rôle
  - Winrate de synergie moyen avec les alliés pickés
  - Winrate de counter moyen face aux ennemis pickés
  - Popularité (nombre de matchs) et équilibre AP/AD de la composition
- **Interface interactive** : Dashboard Streamlit affichant le top 5 des 
  recommandations avec visualisation des scores via Plotly.
- **Auto-update** : Script de scraping paramétrable par tier/division 
  pour maintenir les statistiques à jour après chaque patch.

## Stack Technique

| Couche | Technologies |
|---|---|
| Langage | Python 3.13 |
| Machine Learning | XGBoost, Scikit-learn |
| Manipulation de données | Pandas, NumPy |
| Base de données | PostgreSQL, Psycopg2 |
| Visualisation | Streamlit, Plotly |
| API | Riot Games API (Match-V5) |
| Sérialisation modèle | Joblib |

## Architecture du projet

```
LoL Draft Optimizer/
│
├── scraper.py        # Collecte des données via l'API Riot
├── features.py       # Construction des features ML
├── model.py          # Entraînement et évaluation XGBoost
├── scoring.py        # Moteur de recommandation (ML + fallback)
├── app.py            # Interface Streamlit
├── db.py             # Couche d'accès PostgreSQL
├── settings.py       # Configuration (API key, DB URL)
├── migrate.py        # Migration CSV → PostgreSQL
│
├── data/
│   └── pairs.csv         # Dataset brut (disponible sur Kaggle)
│
└── models/
    └── xgboost_draft.pkl  # Modèle entraîné
```

## Structure des données

Chaque ligne du dataset représente une interaction entre deux champions 
dans un même match :

| Colonne | Type | Description |
|---|---|---|
| match_id | TEXT | Identifiant unique du match |
| champ1 | TEXT | Champion évalué |
| role1 | TEXT | Rôle joué (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY) |
| champ2 | TEXT | Champion de référence (allié ou ennemi) |
| role2 | TEXT | Rôle du champion de référence |
| same_team | BOOLEAN | True = allié, False = ennemi |
| win | BOOLEAN | Résultat du match pour champ1 |

**Le dataset est disponible sur 
[Kaggle](https://www.kaggle.com/datasets/chadyy/pairs-csv/data) 
(600 000+ paires, joueurs Platinum EUW).**

## Résultats du modèle

Entraîné sur ~44 000 exemples issus de 6 700 matchs Platinum EUW :

> **Note** : La performance du modèle est actuellement limitée par le volume 
> de données (6 700 matchs). L'objectif est d'atteindre 50 000+ matchs 
> pour améliorer significativement l'AUC-ROC.

**Le dataset que j'ai réalisé pour l'instant est disponible sur [Kaggle](https://www.kaggle.com/datasets/chadyy/pairs-csv/data).**
