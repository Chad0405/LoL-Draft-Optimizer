import streamlit as st
import pandas as pd
import os
from scoring import compute_scores
import plotly.express as px


st.set_page_config(page_title="LoL Neural-Synergy V2", page_icon="⚔️", layout="wide")

@st.cache_data
def load_data():
    path = "data/pairs.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        champs = sorted(df["champ1"].unique().tolist())
        # Liste des rôles officiels Riot
        roles = ["AUTO", "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
        return df, champs, roles
    return None, [], []

df, ALL_CHAMPS, ROLES = load_data()

st.title("LoL Draft Optimizer — Neural-Synergy")

if df is None:
    st.error("Fichier data/pairs.csv introuvable !")
else:
    # --- SIDEBAR : MA DRAFT ---
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

    # --- MAIN PAGE ---
    st.header("Ta Recommandation")
    my_role = st.selectbox("Quel rôle vas-tu jouer ?", ROLES[1:]) # On enlève AUTO pour toi

    if st.button("Calculer le meilleur pick"):
        if not ally_data and not enemy_data:
            st.warning("Ajoute au moins un champion dans la draft !")
        else:
            with st.spinner("Analyse des probabilités de victoire..."):
                results = compute_scores(df, ally_data, enemy_data, target_role=my_role)

            if not results.empty:
                st.balloons()
                cols = st.columns(5)
                for i, (champ, score) in enumerate(results.head(5).items()):
                    with cols[i]:
                        st.metric(label=f"TOP {i+1}", value=champ, delta=f"{score:.1f}% WR")
                
                st.markdown("### Classement détaillé")
                if not results.empty:
                    # 1. Préparation des données
                    df_plot = results.head(15).reset_index()
                    df_plot.columns = ['Champion', 'Winrate']

                    # 2. Calcul des bornes pour l'auto-scale
                    # On prend le min et le max de tes résultats pour que le graph soit joli
                    val_min = df_plot['Winrate'].min() - 2
                    val_max = df_plot['Winrate'].max() + 2
    
                    # 3. Création du graphique
                    fig = px.bar(
                        df_plot, 
                        x='Winrate', 
                        y='Champion', 
                        orientation='h',
                        color='Winrate',
                        # On utilise une échelle divergente et on fixe le milieu
                        color_continuous_scale='RdYlGn', 
                        range_color=[50, 100], # Force le rouge à 40, le jaune à 50, le vert à 60
                        text='Winrate'
                    )

                    # 4. Réglages fins
                    fig.update_layout(
                        yaxis={'categoryorder':'total ascending'},
                        xaxis=dict(range=[val_min, val_max]), # Auto-scale intelligent
                        height=500,
                        coloraxis_showscale=False # Cache la barre de légende sur le côté
                    )
    
                    fig.update_traces(
                        texttemplate='%{text:.1f}%', 
                        textposition='outside',
                        marker_line_color='rgb(8,48,107)', # Ajoute un petit contour pour la netteté
                        marker_line_width=1.5
                    )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Désolé, pas assez de données pour cette configuration (seuil min: 3 matchs).")