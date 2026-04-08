# LoL Draft Optimizer

LoL Draft Optimizer est un outil d'analyse de données conçu pour optimiser la phase de sélection des champions (Draft) dans League of Legends. En s'appuyant sur les données réelles de l'API Riot Games, cet outil calcule les synergies entre alliés et les probabilités de victoire face aux compositions adverses.

## Objectifs du projet
L'objectif principal est de transformer des données de match brutes en indicateurs d'aide à la décision. L'outil évalue la pertinence d'une composition d'équipe en fonction des statistiques historiques de performance, des associations de champions et des confrontations directes (matchups).

## Fonctionnalités techniques
* **Extraction et Ingénierie des données** : Automatisation de la récupération des données via l'API Riot (Région EUW) et traitement des objets JSON complexes.
* **Pipeline de stockage** : Structuration et stockage des données traitées dans une base de données relationnelle PostgreSQL pour optimiser les requêtes (aussi disponible plus simplement en .csv).
* **Algorithme de Scoring** : Développement d'un moteur de calcul évaluant la force d'une draft selon trois axes :
    * Le winrate individuel des champions.
    * La synergie interne à l'équipe (duos et combinaisons).
    * Le facteur de contre (counter-picking) face à l'équipe adverse.
* **Analyse de données** : Utilisation de bibliothèques de calcul statistique pour identifier des corrélations entre la composition d'équipe et l'issue des matchs.

## Stack Technique
* **Langage** : Python
* **Manipulation de données** : Pandas, NumPy
* **Base de données** : PostgreSQL (SQLAlchemy / Psycopg2), ou fichier csv
* **Visualisation** : Plotly, streamlit
* **API** : Riot Games API (Interface avec les services tiers et gestion des limites de requêtes)

## Structure des données
Le dataset structuré permet une analyse granulaire des interactions :
* **Identifiant de match** : Clé unique pour le suivi des parties classées.
* **Champion 1 , Champion 2** : Indique le nom du champion puis synergies / matchups. 
* **Attributs des champions** : Rôles (Top, Jungle, Middle, Bottom, Utility) et caractéristiques.
* **Indicateurs relationnels** : Variables booléennes distinguant les relations alliées des relations adverses.
* **Cible (Label)** : Résultat final de la partie utilisé pour l'évaluation des modèles.

**Le dataset que j'ai réalisé pour l'instant est disponible sur [Kaggle](https://www.kaggle.com/datasets/chadyy/pairs-csv/data).**
