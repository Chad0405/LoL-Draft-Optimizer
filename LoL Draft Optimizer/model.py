import pandas as pd
import numpy as np
import joblib
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import LabelEncoder
from features import build_training_dataset

FEATURE_COLS = [
    "wr_global", "nb_matchs", "wr_role", "nb_role",
    "wr_synergie_moy", "nb_synergies",
    "wr_counter_moy", "nb_counters",
    "team_ap_ratio"
]

def train():
    os.makedirs("models", exist_ok=True)

    # 1. Construire le dataset
    df = build_training_dataset()
    df.to_csv("data/training_data.csv", index=False)  # sauvegarde pour debug
    print(f"Dataset : {len(df)} lignes, {df['win'].mean():.2%} winrate moyen")

    X = df[FEATURE_COLS].fillna(0)
    y = df["win"]

    # 2. Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train : {len(X_train)} | Test : {len(X_test)}")

    # 3. Entraînement XGBoost
    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )

    print("Entraînement en cours...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50
    )

    # 4. Évaluation
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("\n--- Résultats ---")
    print(classification_report(y_test, y_pred))
    print(f"AUC-ROC : {roc_auc_score(y_test, y_proba):.4f}")

    # 5. Feature importance
    print("\n--- Importance des features ---")
    for feat, imp in sorted(zip(FEATURE_COLS, model.feature_importances_),
                             key=lambda x: x[1], reverse=True):
        print(f"  {feat:<25} {imp:.4f}")

    # 6. Sauvegarde
    joblib.dump(model, "models/xgboost_draft.pkl")
    joblib.dump(FEATURE_COLS, "models/feature_cols.pkl")
    print("\nModèle sauvegardé dans models/xgboost_draft.pkl")

if __name__ == "__main__":
    train()