import streamlit as st
import plotly.express as px
from db import get_all_champions
from scoring import compute_scores  # signature changée, plus de df en paramètre

st.set_page_config(page_title="LoL Neural-Synergy", page_icon="⚔️", layout="wide")
st.title("LoL Draft Optimizer — Neural-Synergy")

@st.cache_data(ttl=3600)
def load_champions():
    return get_all_champions()

ALL_CHAMPS = load_champions()
ROLES = ["AUTO", "TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

if not ALL_CHAMPS:
    st.error("Base de données vide — lance d'abord scraper.py !")
    st.stop()

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

st.header("Ta Recommandation")
my_role = st.selectbox("Quel rôle vas-tu jouer ?", ROLES[1:])

if st.button("Calculer le meilleur pick"):
    if not ally_data and not enemy_data:
        st.warning("Ajoute au moins un champion dans la draft !")
    else:
        with st.spinner("Analyse en cours..."):
            results = compute_scores(ally_data, enemy_data, target_role=my_role)

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
            st.error("Pas assez de données pour cette configuration (seuil min: 3 matchs).")
