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


#######  데이터프레임

import pandas as pd
import streamlit as st




df = pd.read_csv("data/data2025.csv", encoding="utf-8-sig")
df["물동량"] = df["적"] + df["공"]

year = st.selectbox("연도", sorted(df["연도"].unique(), reverse=True))
table = (
    df[df["연도"] == year]
    .pivot_table(
        index="국가명",
        columns="구분",
        values="물동량",
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