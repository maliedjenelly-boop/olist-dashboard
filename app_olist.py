import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_loader import load_all
import os

# ============================================================
# CONFIG GÉNÉRALE
# ============================================================
st.set_page_config(
    page_title   = "Olist E-Commerce Dashboard",
    page_icon    = "🛒",
    layout       = "wide",
    initial_sidebar_state = "expanded",
)

TEAL   = "#1D9E75"
TEAL_L = "#9FE1CB"
PURPLE = "#7F77DD"
AMBER  = "#EF9F27"
CORAL  = "#D85A30"

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================
DATA_PATH = "data/olist/"
local_data_exists = (
    os.path.exists(DATA_PATH) and
    len([f for f in os.listdir(DATA_PATH) if f.endswith(".csv")]) >= 8
)

if local_data_exists:
    with st.spinner("Chargement des données Olist…"):
        df = load_all()
else:
    st.title("Olist E-Commerce Dashboard")
    st.info(
        "Les fichiers CSV ne sont pas inclus dans le repo (trop volumineux). "
        "Merci de les uploader ci-dessous pour lancer le dashboard."
    )
    st.markdown(
        "Télécharge le dataset sur [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) "
        "puis upload les 8 fichiers CSV nécessaires."
    )

    files_needed = [
        "olist_orders_dataset.csv",
        "olist_order_items_dataset.csv",
        "olist_products_dataset.csv",
        "olist_customers_dataset.csv",
        "olist_sellers_dataset.csv",
        "olist_order_payments_dataset.csv",
        "olist_order_reviews_dataset.csv",
        "product_category_name_translation.csv",
    ]

    uploaded = st.file_uploader(
        "Upload les fichiers CSV Olist",
        type="csv",
        accept_multiple_files=True,
        help=f"Fichiers attendus : {', '.join(files_needed)}"
    )

    uploaded_names = [f.name for f in uploaded] if uploaded else []
    missing = [f for f in files_needed if f not in uploaded_names]

    if missing:
        if uploaded:
            st.warning(f"Fichiers manquants : {', '.join(missing)}")
        st.stop()

    with st.spinner("Traitement des données…"):
        df = load_all(uploaded_files=uploaded)

    st.success("Données chargées !")
    if st.button("▶ Lancer le dashboard", type="primary"):
        st.rerun()
    st.stop()

# ============================================================
# SIDEBAR — Filtres globaux
# ============================================================
with st.sidebar:
    st.title("Olist Dashboard")
    st.caption("Brazilian E-Commerce · 2016–2018")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Vue générale", "Géographie", "Segments RFM", "Saisonnalité", "Produits"],
        index=0,
    )

    st.divider()
    st.subheader("Filtres")

    years = sorted(df["year"].dropna().unique().astype(int))
    selected_years = st.multiselect("Année", years, default=years)

    states = sorted(df["customer_state"].dropna().unique())
    selected_states = st.multiselect("État (customer)", states, default=states)

    st.divider()
    st.caption("Projet portfolio · Master 2 Data & IA")

# Application des filtres
filtered = df[
    df["year"].isin(selected_years) &
    df["customer_state"].isin(selected_states)
].copy()

# ============================================================
# MÉTRIQUES COMMUNES
# ============================================================
total_ca     = filtered["payment_value"].sum()
nb_commandes = filtered["order_id"].nunique()
panier_moyen = filtered["payment_value"].mean()
note_moyenne = filtered["review_score"].mean()
delai_moyen  = filtered["delivery_days"].mean()

def kpi_row():
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("CA total",          f"{total_ca:,.0f} BRL")
    c2.metric("Commandes livrées", f"{nb_commandes:,}")
    c3.metric("Panier moyen",      f"{panier_moyen:.0f} BRL")
    c4.metric("Note moyenne",      f"{note_moyenne:.2f} / 5")
    c5.metric("Délai moyen",       f"{delai_moyen:.1f} j")


# ============================================================
# PAGE 1 — VUE GÉNÉRALE
# ============================================================
if page == "Vue générale":
    st.title("Vue générale")
    st.caption("KPIs globaux et évolution du chiffre d'affaires")
    kpi_row()
    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        monthly = (
            filtered
            .groupby(["year", "month"])
            .agg(ca=("payment_value", "sum"), nb=("order_id", "nunique"))
            .reset_index()
        )
        monthly["period"] = pd.to_datetime(
            monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
        )
        monthly = monthly.sort_values("period")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=monthly["period"], y=monthly["nb"],
                   name="Nb commandes", marker_color=TEAL_L, opacity=0.7),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=monthly["period"], y=monthly["ca"],
                       name="CA (BRL)", line=dict(color=TEAL, width=2.5),
                       mode="lines+markers"),
            secondary_y=True
        )
        fig.update_layout(
            title="Évolution mensuelle — commandes & CA",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=380,
        )
        fig.update_yaxes(title_text="Nb commandes", secondary_y=False)
        fig.update_yaxes(title_text="CA (BRL)", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        scores = filtered.dropna(subset=["review_score"]).copy()
        scores["review_score"] = scores["review_score"].round().astype(int)
        counts = scores["review_score"].value_counts().sort_index().reset_index()
        counts.columns = ["score", "count"]
        counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)

        fig2 = px.bar(
            counts, x="score", y="count",
            text=counts["pct"].astype(str) + "%",
            title="Distribution des notes clients",
            color="score",
            color_continuous_scale=["#E24B4A","#EF9F27","#EF9F27","#1D9E75","#1D9E75"],
            labels={"score": "Note", "count": "Avis"},
            height=380,
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    sub = filtered.dropna(subset=["delivery_days", "review_score"]).copy()
    sub = sub[(sub["delivery_days"] > 0) & (sub["delivery_days"] < 120)]
    sub["review_score"] = sub["review_score"].round().astype(int)
    avg_del = sub.groupby("review_score")["delivery_days"].mean().round(1).reset_index()

    fig3 = px.bar(
        avg_del, x="review_score", y="delivery_days",
        title="Délai moyen de livraison par note client",
        color="delivery_days",
        color_continuous_scale=["#1D9E75","#EF9F27","#E24B4A"],
        text="delivery_days",
        labels={"review_score": "Note", "delivery_days": "Délai moyen (j)"},
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)


# ============================================================
# PAGE 2 — GÉOGRAPHIE
# ============================================================
elif page == "Géographie":
    st.title("Géographie des ventes")
    st.caption("Chiffre d'affaires et délais par État brésilien")
    kpi_row()
    st.divider()

    metric = st.selectbox(
        "Métrique à afficher",
        ["CA total (BRL)", "Nombre de commandes", "Délai moyen (jours)", "Note moyenne"]
    )

    by_state = (
        filtered
        .groupby("customer_state")
        .agg(
            ca_total     = ("payment_value", "sum"),
            nb_commandes = ("order_id",      "nunique"),
            delai_moyen  = ("delivery_days", "mean"),
            note_moyenne = ("review_score",  "mean"),
        )
        .round(2)
        .reset_index()
        .rename(columns={"customer_state": "state"})
    )

    col_map = {
        "CA total (BRL)":      "ca_total",
        "Nombre de commandes": "nb_commandes",
        "Délai moyen (jours)": "delai_moyen",
        "Note moyenne":        "note_moyenne",
    }
    color_col   = col_map[metric]
    color_scale = ["#1D9E75","#EF9F27","#E24B4A"] if "Délai" in metric else (
        "RdYlGn" if "Note" in metric else "Teal"
    )

    import requests
    try:
        geo_url    = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        brazil_geo = requests.get(geo_url, timeout=8).json()

        fig_map = px.choropleth(
            by_state,
            geojson          = brazil_geo,
            locations        = "state",
            featureidkey     = "properties.sigla",
            color            = color_col,
            color_continuous_scale = color_scale,
            title            = f"{metric} par État",
            labels           = {color_col: metric, "state": "État"},
            hover_name       = "state",
            hover_data       = {
                "ca_total":    ":,.0f",
                "nb_commandes": True,
                "delai_moyen": ":.1f",
                "note_moyenne":":.2f",
            },
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(margin=dict(l=0,r=0,t=40,b=0), height=520)
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception:
        st.warning("Carte indisponible. Voici le tableau :")
        st.dataframe(by_state.sort_values("ca_total", ascending=False),
                     use_container_width=True)

    top10 = by_state.sort_values("ca_total", ascending=False).head(10)
    fig_bar = px.bar(
        top10, x="state", y="ca_total",
        title="Top 10 États par CA",
        color="ca_total", color_continuous_scale="Teal",
        labels={"state":"État","ca_total":"CA (BRL)"},
        text="nb_commandes",
    )
    fig_bar.update_traces(texttemplate="%{text:,} cmdes", textposition="outside")
    fig_bar.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)


# ============================================================
# PAGE 3 — SEGMENTS RFM
# ============================================================
elif page == "Segments RFM":
    st.title("Segmentation RFM")
    st.caption("Récence · Fréquence · Montant")

    reference_date = filtered["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = (
        filtered
        .groupby("customer_unique_id")
        .agg(
            recency  = ("order_purchase_timestamp", lambda x: (reference_date - x.max()).days),
            frequency= ("order_id",      "nunique"),
            monetary = ("payment_value", "sum"),
        )
        .reset_index()
    )
    rfm["R"] = pd.qcut(rfm["recency"],                        q=5, labels=[5,4,3,2,1]).astype(int)
    rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), q=5, labels=[1,2,3,4,5]).astype(int)
    rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"),  q=5, labels=[1,2,3,4,5]).astype(int)
    rfm["RFM_total"] = rfm["R"] + rfm["F"] + rfm["M"]

    def segment(row):
        r, f, m, s = row["R"], row["F"], row["M"], row["RFM_total"]
        if r >= 4 and f >= 4 and m >= 4: return "Champions"
        elif r >= 3 and f >= 3 and m >= 3: return "Clients fidèles"
        elif r >= 4 and f <= 2: return "Nouveaux clients"
        elif r >= 3 and f >= 2 and m >= 2: return "Clients potentiels"
        elif r == 2 and s >= 7: return "À risque"
        elif r <= 2 and f >= 3: return "Clients perdus"
        elif r <= 2 and s <= 6: return "Clients inactifs"
        else: return "Autres"

    rfm["segment"] = rfm.apply(segment, axis=1)
    color_map = {
        "Champions":"#1D9E75","Clients fidèles":"#5DCAA5",
        "Nouveaux clients":"#7F77DD","Clients potentiels":"#AFA9EC",
        "À risque":"#EF9F27","Clients perdus":"#E24B4A",
        "Clients inactifs":"#B4B2A9","Autres":"#D3D1C7",
    }

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clients analysés", f"{len(rfm):,}")
    c2.metric("Champions",        f"{len(rfm[rfm['segment']=='Champions']):,}")
    c3.metric("Clients à risque", f"{len(rfm[rfm['segment']=='À risque']):,}")
    c4.metric("CA à risque",      f"{rfm[rfm['segment']=='À risque']['monetary'].sum():,.0f} BRL")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        seg_counts = rfm["segment"].value_counts().reset_index()
        seg_counts.columns = ["segment","count"]
        fig_seg = px.bar(
            seg_counts.sort_values("count"),
            x="count", y="segment", orientation="h",
            title="Répartition par segment",
            color="segment", color_discrete_map=color_map,
            labels={"count":"Nb clients","segment":""},
        )
        fig_seg.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_seg, use_container_width=True)

    with col2:
        seg_ca = rfm.groupby("segment")["monetary"].mean().round(0).reset_index()
        fig_ca = px.bar(
            seg_ca.sort_values("monetary"),
            x="monetary", y="segment", orientation="h",
            title="CA moyen par segment (BRL)",
            color="segment", color_discrete_map=color_map,
            labels={"monetary":"CA moyen (BRL)","segment":""},
        )
        fig_ca.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_ca, use_container_width=True)

    rfm_plot = rfm[rfm["monetary"] < rfm["monetary"].quantile(0.97)].copy()
    fig_sc = px.scatter(
        rfm_plot, x="recency", y="monetary",
        color="segment", size="frequency",
        color_discrete_map=color_map, opacity=0.5,
        title="Récence vs Montant (taille = fréquence)",
        labels={"recency":"Récence (jours)","monetary":"Montant (BRL)"},
    )
    fig_sc.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_sc, use_container_width=True)


# ============================================================
# PAGE 4 — SAISONNALITÉ
# ============================================================
elif page == "Saisonnalité":
    st.title("Saisonnalité")
    st.caption("Volume de commandes par mois, jour et heure")
    kpi_row()
    st.divider()

    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_fr    = {
        "Monday":"Lundi","Tuesday":"Mardi","Wednesday":"Mercredi",
        "Thursday":"Jeudi","Friday":"Vendredi","Saturday":"Samedi","Sunday":"Dimanche"
    }

    monthly = (
        filtered.groupby(["year","month"])
        .agg(nb=("order_id","nunique")).reset_index()
    )
    monthly["period"] = pd.to_datetime(
        monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
    )
    monthly = monthly.sort_values("period")

    fig_m = px.line(
        monthly, x="period", y="nb", markers=True,
        title="Volume mensuel de commandes",
        labels={"period":"Mois","nb":"Nb commandes"},
        color_discrete_sequence=[TEAL],
    )
    fig_m.update_layout(hovermode="x unified")
    st.plotly_chart(fig_m, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        by_day = (
            filtered.groupby("day_of_week")
            .agg(nb=("order_id","nunique"))
            .reindex(day_order).reset_index()
        )
        by_day["jour"] = by_day["day_of_week"].map(day_fr)
        fig_d = px.bar(
            by_day, x="jour", y="nb",
            title="Par jour de la semaine",
            color="nb", color_continuous_scale="Teal",
            labels={"jour":"Jour","nb":"Nb commandes"},
        )
        fig_d.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_d, use_container_width=True)

    with col2:
        by_hour = (
            filtered.groupby("hour")
            .agg(nb=("order_id","nunique"))
            .reset_index().sort_values("hour")
        )
        fig_h = px.bar(
            by_hour, x="hour", y="nb",
            title="Par heure de la journée",
            color="nb", color_continuous_scale="Teal",
            labels={"hour":"Heure","nb":"Nb commandes"},
        )
        fig_h.update_layout(
            coloraxis_showscale=False,
            xaxis=dict(tickmode="linear", tick0=0, dtick=1),
        )
        st.plotly_chart(fig_h, use_container_width=True)

    hm = (
        filtered.groupby(["day_of_week","hour"])
        .agg(nb=("order_id","nunique")).reset_index()
    )
    pivot = (
        hm.pivot(index="day_of_week", columns="hour", values="nb")
        .reindex(day_order).fillna(0)
    )
    pivot.index = [day_fr[d] for d in pivot.index]

    fig_hm = px.imshow(
        pivot,
        color_continuous_scale="Teal",
        title="Heatmap — Jour × Heure",
        labels=dict(x="Heure", y="Jour", color="Nb commandes"),
        aspect="auto",
    )
    fig_hm.update_layout(
        xaxis=dict(tickmode="linear", tick0=0, dtick=1),
        height=300,
    )
    st.plotly_chart(fig_hm, use_container_width=True)


# ============================================================
# PAGE 5 — PRODUITS
# ============================================================
elif page == "Produits":
    st.title("Analyse produits")
    st.caption("Catégories, paniers et satisfaction")
    kpi_row()
    st.divider()

    n_top = st.slider("Nombre de catégories", 5, 20, 10)

    top_cats = (
        filtered.groupby("category_en")
        .agg(
            ca_total     = ("payment_value", "sum"),
            nb_commandes = ("order_id",      "nunique"),
            panier_moy   = ("payment_value", "mean"),
            note_moy     = ("review_score",  "mean"),
        )
        .round(1)
        .sort_values("ca_total", ascending=False)
        .head(n_top)
        .reset_index()
    )

    col1, col2 = st.columns(2)
    with col1:
        fig_cat = px.bar(
            top_cats.sort_values("ca_total"),
            x="ca_total", y="category_en", orientation="h",
            title=f"Top {n_top} catégories par CA",
            color="ca_total", color_continuous_scale="Teal",
            labels={"ca_total":"CA (BRL)","category_en":"Catégorie"},
        )
        fig_cat.update_layout(coloraxis_showscale=False, height=420)
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        fig_note = px.bar(
            top_cats.sort_values("note_moy"),
            x="note_moy", y="category_en", orientation="h",
            title="Note moyenne par catégorie",
            color="note_moy",
            color_continuous_scale=["#E24B4A","#EF9F27","#1D9E75"],
            range_color=[1, 5],
            labels={"note_moy":"Note /5","category_en":"Catégorie"},
        )
        fig_note.update_layout(height=420)
        st.plotly_chart(fig_note, use_container_width=True)

    all_cats = (
        filtered.groupby("category_en")
        .agg(
            ca_total     = ("payment_value", "sum"),
            nb_commandes = ("order_id",      "nunique"),
            note_moy     = ("review_score",  "mean"),
        )
        .round(2).reset_index()
    )
    fig_sc = px.scatter(
        all_cats, x="note_moy", y="ca_total",
        size="nb_commandes", color="ca_total",
        color_continuous_scale="Teal",
        hover_name="category_en",
        title="CA vs Note moyenne (taille = nb commandes)",
        labels={"note_moy":"Note /5","ca_total":"CA (BRL)"},
    )
    fig_sc.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_sc, use_container_width=True)
