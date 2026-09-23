import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st
import plotly.express as px

TARGET_PATH='./data/master_total.csv'
df = pd.read_csv(TARGET_PATH)
df.head()

st.set_page_config(page_title="수입/수출/환적 증감률 top 10 대시보드", layout="wide")

yearly = (
    df.groupby(['국가명', '연도'], as_index=False)['수입']
      .sum()
)
pivot = yearly.pivot(
    index='국가명',
    columns='연도',
    values='수입'
)
pivot = pivot[
    (pivot[2020] >= 10000) &
    (pivot[2025] >= 10000)
]
pivot['수입증감률'] = (
    (pivot[2025] - pivot[2020])
    / pivot[2020]
    * 100
)
top10 = (
    pivot[['수입증감률']]
    .dropna()
    .sort_values('수입증감률', ascending=False)
    .head(10)
    .reset_index()
)
fig = px.bar(
    top10,
    x='수입증감률',
    y='국가명',
    orientation='h',
    title='국가별 수입 증감률 Top 10',
    labels={
        '수입증감률': '수입 증감률 (%)',
        '국가명': '국가'
    }
)
fig.update_yaxes(autorange='reversed')

yearly1 = (
    df.groupby(['국가명', '연도'], as_index=False)['수출']
      .sum()
)

pivot1 = yearly1.pivot(
    index='국가명',
    columns='연도',
    values='수출'
)
pivot1 = pivot1[
    (pivot1[2020] >= 10000) &
    (pivot1[2025] >= 10000)
]
pivot1['수출증감률'] = (
    (pivot1[2025] - pivot1[2020])
    / pivot1[2020]
    * 100
)
top10_ex = (
    pivot1[['수출증감률']]
    .dropna()
    .sort_values('수출증감률', ascending=False)
    .head(10)
    .reset_index()
)
fig1 = px.bar(
    top10_ex,
    x='수출증감률',
    y='국가명',
    orientation='h',
    title='국가별 수출 증감률 Top 10',
    labels={
        '수출증감률': '수출 증감률 (%)',
        '국가명': '국가'
    }
)
fig1.update_yaxes(autorange='reversed')

yearly2 = (
    df.groupby(['국가명', '연도'], as_index=False)['환적']
      .sum()
)

pivot2 = yearly2.pivot(
    index='국가명',
    columns='연도',
    values='환적'
)
pivot2 = pivot2[
    (pivot2[2020] >= 10000) &
    (pivot2[2025] >= 10000)
]
pivot2['환적증감률'] = (
    (pivot2[2025] - pivot2[2020])
    / pivot2[2020]
    * 100
)
top10_tr = (
    pivot2[['환적증감률']]
    .dropna()
    .sort_values('환적증감률', ascending=False)
    .head(10)
    .reset_index()
)
fig2 = px.bar(
    top10_tr,
    x='환적증감률',
    y='국가명',
    orientation='h',
    title='국가별 환적 증감률 Top 10',
    labels={
        '수출증감률': '환적 증감률 (%)',
        '국가명': '국가'
    }
)
fig2.update_yaxes(autorange='reversed')

col1, col2, col3 = st.columns(3)

with col1:
    st.plotly_chart(
        fig,
        use_container_width=True,
        height=700,
    )

with col2:
    st.plotly_chart(
        fig1,
        use_container_width=True,
        height=700,
    )

with col3:
    st.plotly_chart(
        fig2,
        use_container_width=True,
        height=700,
    )

