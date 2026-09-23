import pandas as pd
import plotly.express as px
import streamlit as st

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