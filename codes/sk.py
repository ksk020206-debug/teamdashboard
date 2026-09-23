import pandas as pd
import numpy as np
import streamlit as st

df = pd.read_csv("./data/processed/master_total.csv")

year_list = [2020, 2021, 2022, 2023, 2024, 2025]

selected_year = st.segmented_control(
    "기준 연도",
    options=year_list,
    default=2021
)

year_df = df[df["연도"] == selected_year]

total = year_df["전체물동량"].sum()
export = year_df["수출"].sum()
import_ = year_df["수입"].sum()
transshipment = year_df["환적"].sum()

previous_year = selected_year - 1

previous_df = df[df["연도"] == previous_year]

previous_total = previous_df["전체물동량"].sum()
previous_export = previous_df["수출"].sum()
previous_import = previous_df["수입"].sum()
previous_transshipment = previous_df["환적"].sum()

def calculate_delta(current, previous):

    if previous == 0:
        return None

    return ((current - previous) / previous) * 100


total_delta = calculate_delta(total, previous_total)
export_delta = calculate_delta(export, previous_export)
import_delta = calculate_delta(import_, previous_import)
transshipment_delta = calculate_delta(
    transshipment,
    previous_transshipment
)

def format_teu(value):
    return f"{value / 10000:,.1f}만 TEU"

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label=f"{selected_year}년 총 물동량",
        value=format_teu(total),
        delta=(
            f"{total_delta:.1f}%"
            if total_delta is not None
            else "비교 기준 없음"
        )
    )

with col2:
    st.metric(
        label="수출",
        value=format_teu(export),
        delta=(
            f"{export_delta:.1f}%"
            if export_delta is not None
            else "비교 기준 없음"
        )
    )

col3, col4 = st.columns(2)

with col3:
    st.metric(
        label="수입",
        value=format_teu(import_),
        delta=(
            f"{import_delta:.1f}%"
            if import_delta is not None
            else "비교 기준 없음"
        )
    )

with col4:
    st.metric(
        label="환적",
        value=format_teu(transshipment),
        delta=(
            f"{transshipment_delta:.1f}%"
            if transshipment_delta is not None
            else "비교 기준 없음"
        )
    )