import os
import pandas as pd
import streamlit as st

DATA_PATH = "data/olist/"

@st.cache_data
def load_all():
    """
    Charge et nettoie toutes les tables Olist.
    Le décorateur @st.cache_data évite de relire les CSV à chaque interaction.
    """
    files = {
        "orders":         "olist_orders_dataset.csv",
        "order_items":    "olist_order_items_dataset.csv",
        "products":       "olist_products_dataset.csv",
        "customers":      "olist_customers_dataset.csv",
        "sellers":        "olist_sellers_dataset.csv",
        "payments":       "olist_order_payments_dataset.csv",
        "reviews":        "olist_order_reviews_dataset.csv",
        "category_names": "product_category_name_translation.csv",
    }

    dfs = {}
    for key, filename in files.items():
        path = os.path.join(DATA_PATH, filename)
        dfs[key] = pd.read_csv(path)

    # --- Nettoyage orders ---
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        dfs["orders"][col] = pd.to_datetime(dfs["orders"][col], errors="coerce")

    dfs["orders"] = dfs["orders"].dropna(subset=["order_purchase_timestamp"])
    dfs["orders"]["year"]        = dfs["orders"]["order_purchase_timestamp"].dt.year
    dfs["orders"]["month"]       = dfs["orders"]["order_purchase_timestamp"].dt.month
    dfs["orders"]["month_name"]  = dfs["orders"]["order_purchase_timestamp"].dt.strftime("%b")
    dfs["orders"]["day_of_week"] = dfs["orders"]["order_purchase_timestamp"].dt.day_name()
    dfs["orders"]["hour"]        = dfs["orders"]["order_purchase_timestamp"].dt.hour
    dfs["orders"]["delivery_days"] = (
        dfs["orders"]["order_delivered_customer_date"] -
        dfs["orders"]["order_purchase_timestamp"]
    ).dt.days
    dfs["orders"]["delay_days"] = (
        dfs["orders"]["order_delivered_customer_date"] -
        dfs["orders"]["order_estimated_delivery_date"]
    ).dt.days

    # --- Nettoyage products ---
    dfs["products"] = dfs["products"].merge(
        dfs["category_names"], on="product_category_name", how="left"
    ).rename(columns={"product_category_name_english": "category_en"})
    dfs["products"]["category_en"] = dfs["products"]["category_en"].fillna("unknown")

    # --- Dataset principal ---
    master = (
        dfs["orders"]
        .merge(dfs["order_items"],  on="order_id",    how="left")
        .merge(dfs["products"],     on="product_id",  how="left")
        .merge(dfs["customers"],    on="customer_id", how="left")
    )

    payments_agg = (
        dfs["payments"]
        .groupby("order_id")
        .agg(
            payment_value=("payment_value", "sum"),
            payment_type=("payment_type", lambda x: x.mode()[0])
        )
        .reset_index()
    )
    master = master.merge(payments_agg, on="order_id", how="left")

    reviews_agg = (
        dfs["reviews"]
        .groupby("order_id")
        .agg(review_score=("review_score", "mean"))
        .reset_index()
    )
    master = master.merge(reviews_agg, on="order_id", how="left")

    delivered = master[master["order_status"] == "delivered"].copy()

    return delivered
