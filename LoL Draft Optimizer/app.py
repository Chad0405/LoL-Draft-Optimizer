import streamlit as st
import numpy as np
import time
import plotly.express as px
import joblib
import pandas as pd
from db import get_all_champions, get_candidates, get_conn
from features import get_global_winrates, get_winrate_by_role, build_feature_vector

st.set_page_config(page_title="LoL Neural-Synergy", page_icon="⚔️", layout="wide")
st.title("LoL Draft Optimizer — Neural-Synergy")

# Chargement une seule fois au démarrage
@st.cache_resource
def load_model():
    model     = joblib.load("models/xgboost_draft.pkl")
    feat_cols = joblib.load("models/feature_cols.pkl")
    return model, feat_cols

@st.cache_data(ttl=3600)
def load_static_data():
    return (
        get_all_champions(),
        get_global_winrates(),
        get_winrate_by_role(),
    )

@st.cache_data(ttl=3600)
def load_lookups():
    with get_conn() as conn:
        syn_df = pd.read_sql("""
            SELECT champ1, champ2, AVG(win::int) as wr
            FROM champion_pairs WHERE same_team = TRUE
            GROUP BY champ1, champ2 HAVING COUNT(*) >= 3
        """, conn)
        ctr_df = pd.read_sql("""
            SELECT champ1, champ2, AVG(win::int) as wr
            FROM champion_pairs WHERE same_team = FALSE
            GROUP BY champ1, champ2 HAVING COUNT(*) >= 3
        """, conn)
    syn_lookup = {(r.champ1, r.champ2): float(r.wr) for _, r in syn_df.iterrows()}
    ctr_lookup = {(r.champ1, r.champ2): float(r.wr) for _, r in ctr_df.iterrows()}
    return syn_lookup, ctr_lookup

syn_lookup, ctr_lookup = load_lookups()

model, feat_cols            = load_model()
ALL_CHAMPS, global_wr, role_wr = load_static_data()
ROLES = ["AUTO", "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

if not ALL_CHAMPS:
    st.error("Base de données vide — lance d'abord scraper.py !")
    st.stop()

# Sidebar
st.sidebar.header("Ton Équipe (Alliés)")
ally_data = []
for i in range(4):
    c1, c2 = st.sidebar.columns([2, 1.9])
    with c1:
        name = st.selectbox(f"Allié {i+1}", ["None"] + ALL_CHAMPS, key=f"al_{i}")
    with c2:
        role = st.selectbox("Poste", ROLES, key=f"alr_{i}")
    if name != "None":
        ally_data.append({"champ": name, "role": role})

st.sidebar.markdown("---")
st.sidebar.header("Équipe Ennemie")
enemy_data = []
for i in range(5):
    c1, c2 = st.sidebar.columns([2, 1.9])
    with c1:
        name = st.selectbox(f"Ennemi {i+1}", ["None"] + ALL_CHAMPS, key=f"en_{i}")
    with c2:
        role = st.selectbox("Poste", ROLES, key=f"enr_{i}")
    if name != "None":
        enemy_data.append({"champ": name, "role": role})

# Recommandation
st.header("Ta Recommandation")
my_role = st.selectbox("Quel rôle vas-tu jouer ?", ROLES[1:])

if st.button("Calculer le meilleur pick"):
    if not ally_data and not enemy_data:
        st.warning("Ajoute au moins un champion dans la draft !")
    else:
        with st.spinner("Analyse en cours..."):
            candidates = get_candidates(my_role)

            # Construit toutes les features d'un coup (pas de boucle SQL)
            rows = []
            for candidate in candidates:
                gwr = global_wr.get(candidate, {})
                rwr = role_wr.get((candidate, my_role), {})

                syn_rates = [syn_lookup[(candidate, a["champ"])]
                             for a in ally_data
                             if (candidate, a["champ"]) in syn_lookup]

                ctr_rates = [ctr_lookup[(candidate, e["champ"])]
                             for e in enemy_data
                             if (candidate, e["champ"]) in ctr_lookup]

                ap_champs = {"Lux","Syndra","Orianna","Viktor","Cassiopeia",
                             "TwistedFate","Ahri","Zoe","Veigar","Annie","Brand"}
                ally_names = [a["champ"] for a in ally_data]
                ap_count   = sum(1 for c in ally_names if c in ap_champs)

                rows.append({
                    "wr_global":       gwr.get("wr", 0.5),
                    "nb_matchs":       gwr.get("nb", 0),
                    "wr_role":         rwr.get("wr", gwr.get("wr", 0.5)),
                    "nb_role":         rwr.get("nb", 0),
                    "wr_synergie_moy": float(np.mean(syn_rates)) if syn_rates else gwr.get("wr", 0.5),
                    "nb_synergies":    len(syn_rates),
                    "wr_counter_moy":  float(np.mean(ctr_rates)) if ctr_rates else gwr.get("wr", 0.5),
                    "nb_counters":     len(ctr_rates),
                    "team_ap_ratio":   ap_count / max(len(ally_names), 1),
                })

            # Prédiction sur tous les champions en une seule fois
            X      = pd.DataFrame(rows, index=candidates)[feat_cols].fillna(0)
            probas = model.predict_proba(X)[:, 1]
            results = pd.Series(probas * 100, index=candidates).sort_values(ascending=False)

        if not results.empty:
            st.balloons()
            cols = st.columns(5)
            for i, (champ, score) in enumerate(results.head(5).items()):
                with cols[i]:
                    st.metric(label=f"TOP {i+1}", value=champ, delta=f"{score:.1f}% WR")

            df_plot = results.head(15).reset_index()
            df_plot.columns = ["Champion", "Winrate"]
            val_min = df_plot["Winrate"].min() - 2
            val_max = df_plot["Winrate"].max() + 2

            fig = px.bar(df_plot, x="Winrate", y="Champion", orientation="h",
                         color="Winrate", color_continuous_scale="RdYlGn",
                         range_color=[50, 100], text="Winrate")
            fig.update_layout(yaxis={"categoryorder": "total ascending"},
                              xaxis=dict(range=[val_min, val_max]),
                              height=500, coloraxis_showscale=False)
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Pas assez de données pour cette configuration.")
