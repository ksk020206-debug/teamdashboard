import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

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


st.set_page_config(page_title="국가별 물동량", layout="wide")

# 1. 데이터 읽기: 입항=수입, 출항=수출, 적+공=물동량
df = pd.read_csv("data/data2025.csv", encoding="utf-8-sig")

# 2. 연도·국가별 수입/수출/환적 표 만들기
country_year = (
    df.pivot_table(
        index=["연도", "국가명"],
        columns="구분",
        values="계",
        aggfunc="sum",
        fill_value=0,
    )
    .reindex(columns=["입항", "출항", "환적"], fill_value=0)
    .rename(columns={"입항": "수입", "출항": "수출"})
    .reset_index()
)

country_year["수출입"] = country_year["수입"] + country_year["수출"]
country_year["합계"] = country_year["수출입"] + country_year["환적"]

# 같은 연도 내에서 합계 순위 계산
country_year["순위"] = (
    country_year.groupby("연도")["합계"]
    .rank(method="min", ascending=False)
    .astype(int)
)

# 3. 국가 선택
selected_country = st.selectbox(
    "국가",
    sorted(country_year["국가명"].unique()),
    index=sorted(country_year["국가명"].unique()).index("말레이시아"),
)

selected = (
    country_year[country_year["국가명"] == selected_country]
    .sort_values("연도")
    .copy()
)

st.subheader(f"{selected_country} 상세")
st.caption("입항=수입 · 출항=수출 · 적+공 합산")

# 4. 수입·수출·환적 연도별 그래프
chart_data = selected.melt(
    id_vars="연도",
    value_vars=["수입", "수출", "환적"],
    var_name="구분",
    value_name="계",
)
chart_data["계(만)"] = chart_data["계"] / 10_000

fig = px.line(
    chart_data,
    x="연도",
    y="계(만)",
    color="구분",
    markers=True,
    color_discrete_map={
        "수입": "#2874D0",
        "수출": "#22A06B",
        "환적": "#ED6331",
    },
)
fig.update_layout(
    xaxis=dict(dtick=1),
    yaxis_title="계(만)",
    xaxis_title="연도",
    legend_title_text="",
)
st.plotly_chart(fig, width="stretch")

# 5. 상세 표
table = selected[
    ["연도", "수입", "수출", "환적", "합계", "순위"]
].copy()

table[["수입", "수출", "환적", "합계"]] = (
    table[["수입", "수출", "환적", "합계"]].round().astype(int)
)
table["순위"] = table["순위"].astype(str) + "위"

st.dataframe(table, hide_index=True, width="stretch")

year = st.selectbox("연도", sorted(df["연도"].unique(), reverse=True))
table = (
    df[df["연도"] == year]
    .pivot_table(
        index="국가명",
        columns="구분",
        values="계",
        aggfunc="sum",
        fill_value=0,
    )
    .reindex(columns=["입항", "출항", "환적"], fill_value=0)
    .rename(columns={"입항": "수입", "출항": "수출"})
    .reset_index()
)

table["수출입"] = table["수입"] + table["수출"]
table["합계"] = table["수출입"] + table["환적"]
table["합계 비중"] = table["합계"] / table["합계"].sum() * 100

# 합계가 큰 나라부터 처음 표시하고, 그 순위를 고정
table = table.sort_values("합계", ascending=False).reset_index(drop=True)
table.insert(0, "순위", range(1, len(table) + 1))
table = table.rename(columns={"국가명": "국가"})

st.subheader(f"{year}년 국가별 전체 표")
st.caption("열 제목을 누르면 해당 열 기준으로 정렬됩니다.")

숫자열 = ["수입", "수출", "수출입", "환적", "합계"]
table[숫자열] = table[숫자열].round(0).astype(int)

st.dataframe(
    table[["순위", "국가", "수입", "수출", "수출입", "환적", "합계", "합계 비중"]],
    hide_index=True,
    width="stretch",
    height=650,
    column_config={
        "합계 비중": st.column_config.ProgressColumn(
            "합계 비중",
            min_value=0,
            max_value=100,
            format="%.1f%%",
        ),
    },
)

st.write("현재 열:", df.columns.tolist())

total_df = pd.read_csv("./data/processed/master_total.csv")

yearly = (
    total_df.groupby(['국가명', '연도'], as_index=False)['수입']
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
    total_df.groupby(['국가명', '연도'], as_index=False)['수출']
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
    total_df.groupby(['국가명', '연도'], as_index=False)['환적']
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
