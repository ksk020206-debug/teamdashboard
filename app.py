"""부산항 국가별 수출입·환적 물동량 대시보드 (Streamlit)

실행 방법 (프로젝트 폴더에서):
    streamlit run app.py

구성
  1) load_country_year(): kwon.py와 같은 방식으로 data/data2025.csv를 읽어
     연도·국가별 수입/수출/환적 표를 만듭니다. (입항=수입, 출항=수출)
  2) to_records(): 표를 HTML에 넣을 [연도, 국가, 수입, 수출, 환적] 리스트로 바꿉니다.
  3) HTML_TEMPLATE: 대시보드 화면(HTML/CSS/JS). __DATA__ 자리에 데이터가 들어갑니다.

참고 파일에서 가져온 기능
  - kwon.py: 입항=수입·출항=수출 피벗, 합계 동점 공동 순위(rank method="min"),
    기본 선택 국가(말레이시아), 국가 상세의 수입·수출·환적 값, 전체 표의 합계 비중
  - codes/sk.py: 수입·수출 KPI와 전년 대비 증감률, 수입·수출·환적별 증가율 Top 10
    (시작·끝 연도 모두 1만 TEU 이상인 국가만 비교)
  - data/processed/master_total.csv는 data2025.csv를 같은 방식으로 집계한 파일이라
    값이 같습니다. 이 앱은 data2025.csv 하나만 읽습니다.
  4) components.html(): 완성된 HTML을 Streamlit 화면에 띄웁니다.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="부산항 국가별 물동량", layout="wide")

# 데이터 경로: 이 파일(app.py)이 있는 폴더(teamdashboard) 기준
# PyCharm·터미널 어디서 실행해도 찾을 수 있도록 실행 위치가 아닌 이 파일의 위치를 기준으로 합니다.
# 1순위 data/raw/data2025.csv, 없으면 kwon.py가 쓰는 data/data2025.csv를 읽습니다.
BASE_DIR = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    BASE_DIR / "data" / "raw" / "data2025.csv",
    BASE_DIR / "data" / "data2025.csv",
]
DATA_PATH = next((p for p in DATA_CANDIDATES if p.exists()), DATA_CANDIDATES[0])
DASHBOARD_HEIGHT = 3000  # 화면이 잘리면 이 값을 늘리세요 (px)

DEFAULT_COUNTRY = "말레이시아"  # kwon.py의 기본 선택 국가 (데이터에 없으면 1위 국가)
TOP5_EXCLUDE = ["중국", "미국", "일본"]  # 상위 5개국 추이 그래프에서 제외할 국가
GROWTH_MIN_TEU = 10_000  # codes/sk.py 기준: 증가율 Top 10은 시작·끝 연도 모두 1만 TEU 이상인 국가만
REQUIRED_COLUMNS = ["연도", "국가명", "구분", "계"]  # data2025.csv에서 사용하는 열


# 1. 데이터 읽기 (kwon.py와 동일한 가공)
@st.cache_data
def load_country_year(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")  # path 기본값 = DATA_PATH

    # 실제 열 구조 확인 (data2025.csv: 연도, 국가명, 구분, 계, 적, 공)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"필요한 열이 없습니다: {missing} / 현재 열: {df.columns.tolist()}")
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
    country_year["합계"] = country_year["수입"] + country_year["수출"] + country_year["환적"]
    # 모든 값이 0인 행은 제외
    return country_year[country_year["합계"] > 0].reset_index(drop=True)


# 2. HTML에 넣을 형태로 변환: [연도, 국가, 수입, 수출, 환적]
def to_records(country_year: pd.DataFrame) -> list:
    return [
        [int(r["연도"]), str(r["국가명"]), round(float(r["수입"]), 2),
         round(float(r["수출"]), 2), round(float(r["환적"]), 2)]
        for _, r in country_year.iterrows()
    ]


# 3. 대시보드 HTML (데이터는 __DATA__, 설정값은 __CONFIG__ 자리에 들어감)
HTML_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>부산항 국가별 물동량</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">
<style>
:root{
  --bg:#f3f5f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#7c7b76;
  --grid:#e1e0d9; --axis:#c3c2b7; --ring:rgba(11,11,11,0.10);
  --accent:#1c5cab; --accent-wash:#e3edfa;
  --s1:#2a78d6; --s2:#eb6834;
  --pos:#2a78d6; --neg:#e34948;
  --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; --c4:#eda100; --c5:#e87ba4;
  --up:#006300; --down:#b42f2f;
  --shadow:0 1px 2px rgba(16,32,56,.06),0 4px 16px rgba(16,32,56,.05);
}
@media (prefers-color-scheme: dark){
  :root{
    color-scheme:dark;
    --bg:#0f1114; --surface:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --muted:#8f8e88;
    --grid:#2c2c2a; --axis:#383835; --ring:rgba(255,255,255,0.10);
    --accent:#86b6ef; --accent-wash:#1b2a3d;
    --s1:#3987e5; --s2:#d95926;
    --pos:#3987e5; --neg:#e66767;
    --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500; --c5:#d55181;
    --up:#0ca30c; --down:#e66767;
    --shadow:none;
  }
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"IBM Plex Sans KR",system-ui,-apple-system,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  font-size:14px; line-height:1.55;
}
.wrap{max-width:1180px; margin:0 auto; padding-inline:20px; padding-block:24px 40px; display:grid; gap:20px}
header.top{display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:12px 24px}
.eyebrow{font-size:12px; letter-spacing:.08em; color:var(--muted); font-weight:500}
h1{font-size:26px; line-height:1.25; margin:4px 0 0; font-weight:700; text-wrap:balance}
.sub{color:var(--ink-2); margin:6px 0 0; max-width:62ch}
.src{font-size:12px; color:var(--muted); text-align:right; max-width:38ch}

.filters{display:flex; flex-wrap:wrap; gap:10px 20px; align-items:center;
  background:var(--surface); border:1px solid var(--ring); border-radius:10px; padding:10px 14px}
.fgroup{display:flex; align-items:center; gap:10px; flex-wrap:wrap}
.flabel{font-size:12px; color:var(--muted); font-weight:500}
.seg{display:inline-flex; flex-wrap:wrap; background:var(--bg); border-radius:8px; padding:3px; gap:2px}
.seg button{
  font:inherit; font-size:13px; border:0; background:transparent; color:var(--ink-2);
  padding:5px 12px; border-radius:6px; cursor:pointer; font-variant-numeric:tabular-nums}
.seg button:hover{color:var(--ink)}
.seg.sm button{font-size:12px; padding:3px 9px}
.seg button[aria-pressed="true"]{background:var(--surface); color:var(--ink); font-weight:600; box-shadow:0 0 0 1px var(--ring)}
button:focus-visible,select:focus-visible{outline:2px solid var(--accent); outline-offset:2px}

.kpis{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px}
.kpi{background:var(--surface); border:1px solid var(--ring); border-radius:10px; padding:14px 16px; display:grid; gap:4px}
.kpi .l{font-size:12.5px; color:var(--ink-2)}
.kpi .v{font-size:28px; font-weight:600; line-height:1.15; letter-spacing:-.01em}
.kpi .v small{font-size:14px; font-weight:500; color:var(--ink-2); margin-left:2px}
.kpi .d{font-size:12.5px; color:var(--muted)}
.kpi .d b{font-weight:600}
.kpi .d .up{color:var(--up)} .kpi .d .down{color:var(--down)}
.kpi.hero{background:var(--accent-wash); border-color:transparent}

.grid2{display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:20px}
.card{background:var(--surface); border:1px solid var(--ring); border-radius:12px; padding:18px 18px 14px; box-shadow:var(--shadow); min-width:0}
.card h2{font-size:15.5px; margin:0; font-weight:600}
.card .hint{font-size:12.5px; color:var(--muted); margin:2px 0 10px}
.legend{display:flex; gap:14px; flex-wrap:wrap; font-size:12.5px; color:var(--ink-2); margin:0 0 6px}
.legend i{display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; vertical-align:-1px}
.chart{width:100%; position:relative}
.chart svg{display:block; width:100%; height:auto; overflow:visible}
.chart text{fill:var(--ink-2); font-size:11.5px; font-family:inherit}
.chart .tick{fill:var(--muted); font-variant-numeric:tabular-nums}
.chart .val{fill:var(--ink); font-weight:500; font-variant-numeric:tabular-nums}
.chart .gl{stroke:var(--grid); stroke-width:1}
.chart .base{stroke:var(--axis); stroke-width:1}
.chart .hit{fill:transparent; cursor:pointer}
.chart .dim{opacity:.38}
.legend .lg{cursor:pointer} .legend .lg b{font-weight:600; color:var(--ink)}

.detail-head,.card-head{display:flex; justify-content:space-between; align-items:flex-start; gap:10px; flex-wrap:wrap}
select{font:inherit; font-size:13px; color:var(--ink); background:var(--bg); border:1px solid var(--ring); border-radius:8px; padding:6px 10px}
.mini{width:100%; border-collapse:collapse; font-size:12.5px; margin-top:8px; font-variant-numeric:tabular-nums}
.mini th,.mini td{padding:5px 6px; text-align:right; border-bottom:1px solid var(--grid); white-space:nowrap}
.mini th:first-child,.mini td:first-child{text-align:left}
.mini th{color:var(--muted); font-weight:500}
.scroll{overflow-x:auto}

.tbl{width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; font-size:13px}
.tbl th,.tbl td{padding:7px 10px; text-align:right; border-bottom:1px solid var(--grid); white-space:nowrap}
.tbl th:nth-child(-n+2),.tbl td:nth-child(-n+2){text-align:left}
.tbl thead th{position:sticky; top:0; background:var(--surface); z-index:1}
.tbl th button{font:inherit; font-size:12px; color:var(--muted); background:none; border:0; padding:0; cursor:pointer; font-weight:500}
.tbl th button[aria-sort]{color:var(--ink); font-weight:600}
.tbl tbody tr:hover{background:var(--bg)}
.tbl tbody tr.sel{background:var(--accent-wash)}
.tbl .share{display:inline-flex; align-items:center; gap:8px; justify-content:flex-end}
.tbl .share span.bar{display:inline-block; height:6px; border-radius:3px; background:var(--s1); opacity:.75}
.tblwrap{max-height:520px; overflow:auto; border-top:1px solid var(--grid)}

.notes{font-size:12.5px; color:var(--ink-2); display:grid; gap:6px}
.notes h2{font-size:14px; color:var(--ink); margin:0 0 4px}
.notes p{margin:0; max-width:92ch}
.notes b{color:var(--ink); font-weight:600}

#tip{position:fixed; pointer-events:none; z-index:10; background:var(--surface); color:var(--ink);
  border:1px solid var(--ring); border-radius:8px; padding:8px 10px; font-size:12.5px; box-shadow:0 6px 24px rgba(0,0,0,.14);
  min-width:150px; font-variant-numeric:tabular-nums}
#tip .t{font-weight:600; margin-bottom:4px}
#tip .r{display:flex; justify-content:space-between; gap:14px; color:var(--ink-2)}
#tip .r b{color:var(--ink); font-weight:500}
#tip i{display:inline-block; width:8px; height:8px; border-radius:2px; margin-right:6px}
[hidden]{display:none!important}

@media (max-width:860px){
  .grid2{grid-template-columns:minmax(0,1fr)}
  .kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
  .src{text-align:left}
}
@media (max-width:420px){
  .wrap{padding-inline:16px}
  .kpi .v{font-size:23px}
  h1{font-size:22px}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div>
      <div class="eyebrow">BUSAN PORT · CONTAINER THROUGHPUT BY COUNTRY</div>
      <h1>부산항 국가별 수출입·환적 물동량</h1>
      <p class="sub" id="subText"></p>
    </div>
    
  </header>

  <div class="filters" role="group" aria-label="필터">
    <div class="fgroup"><span class="flabel" id="yl">기준 연도</span><div class="seg" id="yearSeg" role="group" aria-labelledby="yl"></div></div>
    <div class="fgroup"><span class="flabel" id="ml">지표</span><div class="seg" id="measSeg" role="group" aria-labelledby="ml"></div></div>
  </div>

  <section class="kpis" id="kpis" aria-label="핵심 지표"></section>

  <div class="grid2">
    <section class="card">
      <h2>연도별 물동량 구성</h2>
      <p class="hint">막대를 누르면 기준 연도가 바뀝니다.</p>
      <div class="legend"><span><i style="background:var(--s1)"></i>수출입</span><span><i style="background:var(--s2)"></i>환적</span></div>
      <div class="chart" id="cYear"></div>
    </section>
    <section class="card">
      <div class="card-head">
        <h2 id="growthTitle"></h2>
        <div class="seg sm" id="growthSeg" role="group" aria-label="증감률 대상">
          <button type="button" id="gvol">물동량 상위</button>
          <button type="button" id="grate">증가율 Top 10</button>
        </div>
      </div>
      <p class="hint" id="growthHint"></p>
      <div class="chart" id="cGrowth"></div>
    </section>
  </div>

  <div class="grid2">
    <section class="card">
      <h2 id="rankTitle"></h2>
      <p class="hint">막대를 누르면 오른쪽 국가 상세가 바뀝니다.</p>
      <div class="legend" id="rankLegend"></div>
      <div class="chart" id="cRank"></div>
    </section>
    <section class="card">
      <div class="detail-head">
        <div>
          <h2 id="detTitle"></h2>
          <p class="hint">수출입과 환적의 연도별 추이</p>
        </div>
        <label><span class="flabel" style="margin-right:6px">국가</span><select id="countrySel"></select></label>
      </div>
      <div class="legend"><span><i style="background:var(--s1)"></i>수출입</span><span><i style="background:var(--s2)"></i>환적</span></div>
      <div class="chart" id="cDetail"></div>
      <div class="scroll"><table class="mini" id="detTable"></table></div>
    </section>
  </div>

  <section class="card">
    <div class="card-head">
      <div>
        <h2 id="t5Title"></h2>
        <p class="hint" id="t5Hint"></p>
      </div>
      <div class="seg sm" id="t5Seg" role="group" aria-label="그래프 단위">
        <button type="button" id="t5abs">물동량(TEU)</button>
        <button type="button" id="t5idx"></button>
      </div>
    </div>
    <div class="legend" id="t5Legend"></div>
    <div class="chart" id="cTop5"></div>
  </section>

  <section class="card">
    <h2 id="tblTitle"></h2>
    <p class="hint">열 제목을 누르면 정렬되고, 행을 누르면 국가 상세가 바뀝니다.</p>
    <div class="tblwrap"><table class="tbl" id="tbl"></table></div>
  </section>

  <section class="card notes">
    <h2>참고 사항</h2>
    <p><b>수입</b> = 입항, <b>수출</b> = 출항, <b>수출입</b> = 수입 + 수출, <b>합계</b> = 수출입 + 환적입니다. 각 값은 적재(적)와 공컨테이너(공)를 합친 계(TEU)입니다.</p>
    <p><b>환적</b>은 부산항에서 내리고 다시 싣는 컨테이너로, 양하·적하가 각각 집계되어 2회 계상됩니다. 부산항 공식 총물동량과 같은 기준입니다.</p>
    <p><b>순위</b>는 합계가 같으면 같은 순위로 표시합니다(kwon.py 방식). <b>증가율 Top 10</b>은 codes/sk.py 기준대로 시작·끝 연도 모두 <span id="minNote"></span> TEU 이상인 국가만 비교합니다.</p>
    <p><b>국가 기준</b>: 환적의 상대국은 직전 출항지 또는 다음 기항지 국가일 수 있어, 화물의 최종 출발지·목적지와 다를 수 있습니다. 바하마·파나마처럼 경유 거점 국가가 상위권에 오르는 이유입니다.</p>
  </section>
</div>
<div id="tip" hidden></div>

<script>
const RAW = __DATA__;   // [연도, 국가, 수입, 수출, 환적]
const CFG = __CONFIG__; // {defaultCountry, growthMin}

const rows = RAW.map(r=>({y:r[0], n:r[1], im:r[2], ex:r[3], ts:r[4], ie:r[2]+r[3], tot:r[2]+r[3]+r[4]}));
const YEARS=[...new Set(rows.map(r=>r.y))].sort((a,b)=>a-b);
const FIRST=YEARS[0], LAST=YEARS[YEARS.length-1], SPAN=LAST-FIRST;
const MEAS={tot:{k:'tot',n:'합계'},im:{k:'im',n:'수입'},ex:{k:'ex',n:'수출'},ie:{k:'ie',n:'수출입'},ts:{k:'ts',n:'환적'}};

const byYear={}; YEARS.forEach(y=>byYear[y]=rows.filter(r=>r.y===y));
const idx={}; YEARS.forEach(y=>{idx[y]=new Map(byYear[y].map(r=>[r.n,r]));});
const ZERO=(y,n)=>({y,n,im:0,ex:0,ts:0,ie:0,tot:0});
const find=(y,n)=>idx[y].get(n)||null;
const totals={}; YEARS.forEach(y=>{const t={im:0,ex:0,ts:0,ie:0,tot:0}; byYear[y].forEach(r=>{for(const k in t)t[k]+=r[k]}); totals[y]=t;});
// 전체 누적: 모든 연도를 국가별로 합친 가상의 연도 'ALL'
(()=>{const m=new Map(); rows.forEach(r=>{const a=m.get(r.n)||{y:'ALL',n:r.n,im:0,ex:0,ts:0,ie:0,tot:0}; for(const k of ['im','ex','ts','ie','tot'])a[k]+=r[k]; m.set(r.n,a);});
  byYear.ALL=[...m.values()]; idx.ALL=m; const t={im:0,ex:0,ts:0,ie:0,tot:0}; byYear.ALL.forEach(r=>{for(const k in t)t[k]+=r[k]}); totals.ALL=t;})();
const yLabel=y=>y==='ALL'?`${FIRST}~${LAST}년 누적`:`${y}년`;
// 중국·미국·일본 제외 누적 합계 상위 5개국
const TOP5=[...byYear.ALL].filter(r=>!CFG.top5Exclude.includes(r.n)).sort((a,b)=>b.tot-a.tot).slice(0,5).map(r=>r.n);
// 합계가 같으면 같은 순위 (kwon.py의 rank(method="min")와 동일)
const rankIn=(y,n,k='tot')=>{const r=find(y,n); if(!r) return null; return 1+byYear[y].filter(x=>x[k]>r[k]).length;};
const countries=[...new Set(rows.map(r=>r.n))].sort((a,b)=>((find(LAST,b)||{tot:0}).tot)-((find(LAST,a)||{tot:0}).tot));

const startCountry=countries.includes(CFG.defaultCountry)?CFG.defaultCountry:countries[0];
let state={year:LAST, meas:'tot', country:startCountry, growth:'vol', t5:'abs', sortKey:'tot', sortDir:-1};
try{const s=JSON.parse(localStorage.getItem('bp-team-dash')||'null'); if(s&&(YEARS.includes(s.year)||s.year==='ALL')&&MEAS[s.meas]&&countries.includes(s.country)&&['vol','rate'].includes(s.growth)&&['abs','idx'].includes(s.t5)) state={...state,...s};}catch(e){}
function save(){try{localStorage.setItem('bp-team-dash',JSON.stringify({year:state.year,meas:state.meas,country:state.country,growth:state.growth,t5:state.t5}))}catch(e){}}

const nf=new Intl.NumberFormat('ko-KR',{maximumFractionDigits:0});
const man=v=>v>=10000? (Math.round(v/1000)/10).toLocaleString('ko-KR',{maximumFractionDigits:1})+'만' : nf.format(v);
const pct=(v,d=1)=>(v*100).toFixed(d)+'%';
const sgn=(v,d=1)=>(v>0?'+':v<0?'−':'')+Math.abs(v*100).toFixed(d)+'%';
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const NS='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){const e=document.createElementNS(NS,tag); for(const k in attrs)e.setAttribute(k,attrs[k]); if(parent)parent.appendChild(e); return e;}
function txt(parent,x,y,s,attrs={}){const t=el('text',{x,y,...attrs},parent); t.textContent=s; return t;}
function niceMax(v,n=5){if(v<=0)return n; const raw=v/n; const p=Math.pow(10,Math.floor(Math.log10(raw))); const m=[1,2,2.5,5,10].find(m=>m*p>=raw); return m*p*n;}
function barPath(x,y,w,h,dir){
  if(w<=0||h<=0) return '';
  const r=Math.min(4, dir==='up'?h:w, dir==='up'?w/2:h/2);
  if(dir==='up') return `M${x},${y+h}V${y+r}Q${x},${y} ${x+r},${y}H${x+w-r}Q${x+w},${y} ${x+w},${y+r}V${y+h}Z`;
  if(dir==='left') return `M${x+w},${y}H${x+r}Q${x},${y} ${x},${y+r}V${y+h-r}Q${x},${y+h} ${x+r},${y+h}H${x+w}Z`;
  return `M${x},${y}H${x+w-r}Q${x+w},${y} ${x+w},${y+r}V${y+h-r}Q${x+w},${y+h} ${x+w-r},${y+h}H${x}Z`;
}
const axisLabel=v=>v>=10000?(v/10000).toLocaleString('ko-KR')+'만':nf.format(v);

// 툴팁
const tip=document.getElementById('tip');
function showTip(ev,title,lines){
  tip.innerHTML=`<div class="t">${title}</div>`+lines.map(l=>`<div class="r"><span>${l.c?`<i style="background:${l.c}"></i>`:''}${l.k}</span><b>${l.v}</b></div>`).join('');
  tip.hidden=false; moveTip(ev);
}
function moveTip(ev){const pad=14; let x=ev.clientX+pad, y=ev.clientY+pad; const w=tip.offsetWidth,h=tip.offsetHeight;
  if(x+w>innerWidth-8)x=ev.clientX-w-pad; if(y+h>innerHeight-8)y=ev.clientY-h-pad; tip.style.left=x+'px'; tip.style.top=y+'px';}
function hideTip(){tip.hidden=true;}
function bindTip(node,fn){node.addEventListener('pointerenter',e=>fn(e)); node.addEventListener('pointermove',moveTip); node.addEventListener('pointerleave',hideTip);}

// 필터
function buildFilters(){
  document.getElementById('subText').textContent=`${FIRST}~${LAST}년, 상대국 기준 컨테이너 처리실적. 단위는 TEU, 연도와 지표에 따라 차트 변경.`;
  const ys=document.getElementById('yearSeg'); ys.innerHTML='';
  ['ALL',...YEARS].forEach(y=>{const b=document.createElement('button'); b.type='button'; b.textContent=y==='ALL'?'전체 누적':y; b.id='y'+y; b.onclick=()=>{state.year=y; renderAll();}; ys.appendChild(b);});
  const ms=document.getElementById('measSeg'); ms.innerHTML='';
  Object.values(MEAS).forEach(m=>{const b=document.createElement('button'); b.type='button'; b.textContent=m.n; b.id='m'+m.k; b.onclick=()=>{state.meas=m.k; renderAll();}; ms.appendChild(b);});
  const sel=document.getElementById('countrySel'); sel.innerHTML='';
  countries.forEach(n=>{const o=document.createElement('option'); o.value=n; o.textContent=n; sel.appendChild(o);});
  sel.onchange=()=>{state.country=sel.value; renderAll();};
  document.getElementById('gvol').onclick=()=>{state.growth='vol'; renderAll();};
  document.getElementById('grate').onclick=()=>{state.growth='rate'; renderAll();};
  document.getElementById('minNote').textContent=nf.format(CFG.growthMin);
  document.getElementById('t5idx').textContent=`성장 지수(${FIRST}=100)`;
  document.getElementById('t5abs').onclick=()=>{state.t5='abs'; renderTop5();};
  document.getElementById('t5idx').onclick=()=>{state.t5='idx'; renderTop5();};
}

function renderKPIs(){
  const y=state.year, t=totals[y], p=y==='ALL'?null:totals[y-1];
  const none= y==='ALL' ? `<span>${YEARS.length}개년 합계</span>` : `<span>${FIRST}년은 비교 기준이 없습니다</span>`;
  const d=k=>{ if(!p) return none; const g=t[k]/p[k]-1; return `전년 대비 <b class="${g>=0?'up':'down'}">${g>=0?'▲':'▼'} ${sgn(g)}</b>`;};
  const k=[
    {l:`${yLabel(y)} 총 물동량`,v:man(t.tot),u:'TEU',d:d('tot'),hero:true},
    {l:'수입',v:man(t.im),u:'TEU',d:d('im')},
    {l:'수출',v:man(t.ex),u:'TEU',d:d('ex')},
    {l:'환적',v:man(t.ts),u:'TEU',d:d('ts')},
  ];
  document.getElementById('kpis').innerHTML=k.map(x=>`<div class="kpi${x.hero?' hero':''}"><div class="l">${x.l}</div><div class="v">${x.v}<small>${x.u}</small></div><div class="d">${x.d}</div></div>`).join('');
}

function renderYearChart(){
  const host=document.getElementById('cYear'); host.innerHTML='';
  const W=Math.max(300,host.clientWidth), H=W<500?260:345, m={t:24,r:8,b:26,l:48};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'연도별 수출입·환적 물동량 누적 막대'},host);
  const max=niceMax(Math.max(...YEARS.map(y=>totals[y].tot)),5), iw=W-m.l-m.r, ih=H-m.t-m.b;
  const ys=v=>m.t+ih-(v/max)*ih;
  for(let i=0;i<=5;i++){const v=max/5*i, yy=ys(v); el('line',{x1:m.l,x2:W-m.r,y1:yy,y2:yy,class:i?'gl':'base'},svg); txt(svg,m.l-8,yy+4,v?axisLabel(v):'0',{class:'tick','text-anchor':'end'});}
  const band=iw/YEARS.length, bw=Math.min(40,band*.5);
  YEARS.forEach((y,i)=>{
    const t=totals[y], x=m.l+band*i+(band-bw)/2, g=el('g',{class:(state.year==='ALL'||y===state.year)?'':'dim'},svg);
    el('rect',{x,y:ys(t.ie),width:bw,height:(t.ie/max)*ih,fill:css('--s1')},g);
    el('path',{d:barPath(x,ys(t.tot),bw,Math.max(0,(t.ts/max)*ih-2),'up'),fill:css('--s2')},g);
    txt(svg,x+bw/2,ys(t.tot)-7,man(t.tot),{class:'val','text-anchor':'middle',opacity:(state.year==='ALL'||y===state.year)?1:.6});
    txt(svg,x+bw/2,H-8,y,{class:'tick','text-anchor':'middle'});
    const hit=el('rect',{x:m.l+band*i,y:m.t,width:band,height:ih,class:'hit'},svg);
    hit.addEventListener('click',()=>{state.year=y; renderAll();});
    bindTip(hit,e=>showTip(e,`${y}년`,[{k:'수출입',v:nf.format(t.ie),c:css('--s1')},{k:'환적',v:nf.format(t.ts),c:css('--s2')},{k:'합계',v:nf.format(t.tot)},{k:'환적 비중',v:pct(t.ts/t.tot)}]));
  });
}

function renderRank(){
  const host=document.getElementById('cRank'); host.innerHTML='';
  const k=state.meas, y=state.year, N=15;
  document.getElementById('rankTitle').textContent=`${yLabel(y)} ${MEAS[k].n} 상위 ${N}개국`;
  document.getElementById('rankLegend').innerHTML = k==='tot'? '<span><i style="background:var(--s1)"></i>수출입</span><span><i style="background:var(--s2)"></i>환적</span>' : '';
  const data=[...byYear[y]].sort((a,b)=>b[k]-a[k]).slice(0,N);
  const W=Math.max(300,host.clientWidth), row=26, m={t:4,r:58,b:4,l:92}, H=m.t+m.b+row*data.length;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':`${y}년 ${MEAS[k].n} 국가 순위`},host);
  const max=data[0][k]||1, iw=W-m.l-m.r, xs=v=>(v/max)*iw, bh=16, tot=totals[y][k];
  el('line',{x1:m.l,x2:m.l,y1:m.t,y2:H-m.b,class:'base'},svg);
  data.forEach((r,i)=>{
    const yy=m.t+row*i+(row-bh)/2, sel=r.n===state.country;
    txt(svg,m.l-10,yy+bh/2+4,r.n,{'text-anchor':'end',style:sel?'fill:var(--ink);font-weight:600':''});
    if(k==='tot'){
      const w1=xs(r.ie), w2=xs(r.ts);
      el('rect',{x:m.l,y:yy,width:Math.max(0,w1),height:bh,fill:css('--s1')},svg);
      el('path',{d:barPath(m.l+w1+2,yy,Math.max(0,w2-2),bh,'right'),fill:css('--s2')},svg);
    } else {
      el('path',{d:barPath(m.l,yy,xs(r[k]),bh,'right'),fill:css(k==='ts'?'--s2':'--s1')},svg);
    }
    txt(svg,m.l+xs(r[k])+6,yy+bh/2+4,man(r[k]),{class:'val'});
    const hit=el('rect',{x:0,y:m.t+row*i,width:W,height:row,class:'hit'},svg);
    hit.addEventListener('click',()=>{state.country=r.n; renderAll();});
    bindTip(hit,e=>showTip(e,`${rankIn(y,r.n,k)}위 ${r.n}`,[{k:'수입',v:nf.format(r.im)},{k:'수출',v:nf.format(r.ex)},{k:'수출입',v:nf.format(r.ie),c:css('--s1')},{k:'환적',v:nf.format(r.ts),c:css('--s2')},{k:`${MEAS[k].n} 비중`,v:pct(r[k]/tot)}]));
  });
}

function renderGrowth(){
  const host=document.getElementById('cGrowth'); host.innerHTML='';
  const k=state.meas, rate=state.growth==='rate', N=rate?10:15, MIN=CFG.growthMin;
  document.querySelectorAll('#growthSeg button').forEach(b=>b.setAttribute('aria-pressed',b.id===(rate?'grate':'gvol')));
  document.getElementById('growthTitle').textContent=`${MEAS[k].n} 증감률 (${FIRST}→${LAST})`;
  document.getElementById('growthHint').textContent= rate
    ? `${FIRST}·${LAST}년 모두 ${MEAS[k].n} ${nf.format(MIN)} TEU 이상인 국가 중 증가율 상위 ${N}개국입니다.`
    : `${LAST}년 ${MEAS[k].n} 상위 ${N}개국 기준입니다. 파랑은 증가, 빨강은 감소입니다.`;
  const withGrowth=r=>{const v0=find(FIRST,r.n)[k]; return {...r,v0,g:r[k]/v0-1};};
  let list;
  if(rate){ // codes/sk.py: 시작·끝 연도 모두 MIN 이상 → 증가율 내림차순 Top 10
    list=byYear[LAST].filter(r=>r[k]>=MIN&&find(FIRST,r.n)&&find(FIRST,r.n)[k]>=MIN)
      .map(withGrowth).sort((a,b)=>b.g-a.g).slice(0,N);
  } else {
    list=[...byYear[LAST]].sort((a,b)=>b[k]-a[k]).slice(0,N)
      .filter(r=>find(FIRST,r.n)&&find(FIRST,r.n)[k]>0).map(withGrowth).sort((a,b)=>b.g-a.g);
  }
  if(!list.length){ host.innerHTML='<p class="hint">조건에 맞는 국가가 없습니다.</p>'; return; }
  const W=Math.max(300,host.clientWidth), row=26, m={t:4,r:14,b:4,l:92}, H=m.t+m.b+row*list.length;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':`${MEAS[k].n} 증감률`},host);
  const lo=Math.min(0,...list.map(r=>r.g)), hi=Math.max(0,...list.map(r=>r.g));
  const labW=50, iw=W-m.l-m.r-labW*2, span=hi-lo||1;
  const xs=v=>m.l+labW+((v-lo)/span)*iw, x0=xs(0), bh=16;
  el('line',{x1:x0,x2:x0,y1:m.t,y2:H-m.b,class:'base'},svg);
  list.forEach((r,i)=>{
    const yy=m.t+row*i+(row-bh)/2, x1=xs(r.g), pos=r.g>=0;
    txt(svg,m.l-10,yy+bh/2+4,r.n,{'text-anchor':'end'});
    el('path',{d:barPath(pos?x0:x1,yy,Math.abs(x1-x0),bh,pos?'right':'left'),fill:css(pos?'--pos':'--neg')},svg);
    txt(svg,pos?x1+6:x1-6,yy+bh/2+4,sgn(r.g),{class:'val','text-anchor':pos?'start':'end'});
    const hit=el('rect',{x:0,y:m.t+row*i,width:W,height:row,class:'hit'},svg);
    hit.addEventListener('click',()=>{state.country=r.n; renderAll();});
    bindTip(hit,e=>showTip(e,r.n,[{k:String(FIRST),v:nf.format(r.v0)},{k:String(LAST),v:nf.format(r[k])},{k:'증감률',v:sgn(r.g)},{k:'연평균(CAGR)',v:sgn(Math.pow(r[k]/r.v0,1/SPAN)-1)}]));
  });
}

function renderDetail(){
  const host=document.getElementById('cDetail'); host.innerHTML='';
  const c=state.country, data=YEARS.map(y=>find(y,c)||ZERO(y,c)), L=YEARS.length-1;
  document.getElementById('countrySel').value=c;
  document.getElementById('detTitle').textContent=`${c} 상세`;
  const W=Math.max(300,host.clientWidth), H=210, m={t:20,r:56,b:26,l:48};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':`${c} 수출입·환적 추이`},host);
  const max=niceMax(Math.max(...data.map(r=>Math.max(r.ie,r.ts))),4), iw=W-m.l-m.r, ih=H-m.t-m.b;
  const xs=i=>m.l+(iw/L)*i, ys=v=>m.t+ih-(v/max)*ih;
  for(let i=0;i<=4;i++){const v=max/4*i, yy=ys(v); el('line',{x1:m.l,x2:W-m.r,y1:yy,y2:yy,class:i?'gl':'base'},svg); txt(svg,m.l-8,yy+4,axisLabel(v),{class:'tick','text-anchor':'end'});}
  YEARS.forEach((y,i)=>txt(svg,xs(i),H-8,y,{class:'tick','text-anchor':'middle'}));
  const cross=el('line',{x1:0,x2:0,y1:m.t,y2:m.t+ih,stroke:css('--axis'),'stroke-width':1,visibility:'hidden'},svg);
  const series=[{k:'ie',c:css('--s1')},{k:'ts',c:css('--s2')}], ends=[];
  series.forEach(s=>{
    el('path',{d:data.map((r,i)=>(i?'L':'M')+xs(i)+','+ys(r[s.k])).join(''),fill:'none',stroke:s.c,'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'},svg);
    data.forEach((r,i)=>el('circle',{cx:xs(i),cy:ys(r[s.k]),r:i===L?5:3.5,fill:s.c,stroke:css('--surface'),'stroke-width':2},svg));
    ends.push({y:ys(data[L][s.k]),t:man(data[L][s.k])});
  });
  if(Math.abs(ends[0].y-ends[1].y)<14){const mid=(ends[0].y+ends[1].y)/2, up=ends[0].y<ends[1].y?0:1; ends[up].y=mid-8; ends[1-up].y=mid+8;}
  ends.forEach(e=>txt(svg,xs(L)+10,e.y+4,e.t,{class:'val'}));
  const band=iw/L;
  YEARS.forEach((y,i)=>{
    const hit=el('rect',{x:xs(i)-band/2,y:m.t,width:band,height:ih,class:'hit'},svg);
    bindTip(hit,e=>{cross.setAttribute('x1',xs(i));cross.setAttribute('x2',xs(i));cross.setAttribute('visibility','visible');
      const r=data[i]; showTip(e,`${c} · ${y}년`,[{k:'수입',v:nf.format(r.im)},{k:'수출',v:nf.format(r.ex)},{k:'수출입',v:nf.format(r.ie),c:series[0].c},{k:'환적',v:nf.format(r.ts),c:series[1].c},{k:'합계',v:nf.format(r.tot)},{k:'부산항 내 비중',v:pct(r.tot/totals[y].tot)}]);});
    hit.addEventListener('pointerleave',()=>cross.setAttribute('visibility','hidden'));
  });
  const rankOf=(y)=>{const r=rankIn(y,c); return r?r+'위':'–';};
  document.getElementById('detTable').innerHTML='<thead><tr><th>연도</th><th>수입</th><th>수출</th><th>환적</th><th>합계</th><th>순위</th></tr></thead><tbody>'+
    data.map((r,i)=>`<tr><td>${YEARS[i]}</td><td>${nf.format(r.im)}</td><td>${nf.format(r.ex)}</td><td>${nf.format(r.ts)}</td><td><b>${nf.format(r.tot)}</b></td><td>${rankOf(YEARS[i])}</td></tr>`).join('')+'</tbody>';
}

function renderTable(){
  const y=state.year, tt=totals[y];
  document.getElementById('tblTitle').textContent=`${yLabel(y)} 국가별 전체 표 (${byYear[y].length}개국)`;
  const cols=[['rank','순위'],['n','국가'],['im','수입'],['ex','수출'],['ie','수출입'],['ts','환적'],['tot','합계'],['share','합계 비중']];
  const list=byYear[y].map(r=>({...r,rank:rankIn(y,r.n),share:r.tot/tt.tot}));
  const sk=state.sortKey, dir=state.sortDir;
  list.sort((a,b)=>{const A=a[sk],B=b[sk]; return (typeof A==='string'?A.localeCompare(B,'ko'):A-B)*dir;});
  const maxShare=Math.max(...list.map(r=>r.share));
  const th=cols.map(([k,n])=>`<th scope="col"><button type="button" data-k="${k}" ${k===sk?`aria-sort="${dir>0?'ascending':'descending'}"`:''}>${n}${k===sk?(dir>0?' ↑':' ↓'):''}</button></th>`).join('');
  const body=list.map(r=>`<tr class="${r.n===state.country?'sel':''}" data-n="${r.n}" style="cursor:pointer"><td>${r.rank}</td><td>${r.n}</td><td>${nf.format(r.im)}</td><td>${nf.format(r.ex)}</td><td>${nf.format(r.ie)}</td><td>${nf.format(r.ts)}</td><td><b>${nf.format(r.tot)}</b></td><td><span class="share"><span class="bar" style="width:${Math.max(2,r.share/maxShare*60)}px"></span>${pct(r.share)}</span></td></tr>`).join('');
  const foot=`<tr><td></td><td><b>부산항 전체</b></td><td><b>${nf.format(tt.im)}</b></td><td><b>${nf.format(tt.ex)}</b></td><td><b>${nf.format(tt.ie)}</b></td><td><b>${nf.format(tt.ts)}</b></td><td><b>${nf.format(tt.tot)}</b></td><td><b>100%</b></td></tr>`;
  const t=document.getElementById('tbl');
  t.innerHTML=`<thead><tr>${th}</tr></thead><tbody>${body}${foot}</tbody>`;
  t.querySelectorAll('th button').forEach(b=>b.onclick=()=>{const k=b.dataset.k; if(state.sortKey===k)state.sortDir*=-1; else {state.sortKey=k; state.sortDir=(k==='n'||k==='rank')?1:-1;} renderTable();});
  t.querySelectorAll('tbody tr[data-n]').forEach(tr=>tr.onclick=()=>{state.country=tr.dataset.n; renderAll();});
}

// 중국·미국·일본 제외 물동량 상위 5개국의 연도별 추이 (물동량 / 성장 지수)
function niceStep(raw){const p=Math.pow(10,Math.floor(Math.log10(raw))); return [1,2,2.5,5,10].find(m=>m*p>=raw)*p;}
function renderTop5(){
  const host=document.getElementById('cTop5'); host.innerHTML='';
  const idxMode=state.t5==='idx', L=YEARS.length-1;
  document.querySelectorAll('#t5Seg button').forEach(b=>b.setAttribute('aria-pressed',b.id===(idxMode?'t5idx':'t5abs')));
  document.getElementById('t5Title').textContent=`${CFG.top5Exclude.join('·')} 제외 물동량 상위 5개국 연도별 추이`;
  document.getElementById('t5Hint').textContent= idxMode
    ? `${FIRST}년 물동량을 100으로 놓고 비교한 성장 지수입니다. 100보다 높으면 ${FIRST}년보다 늘어난 것입니다.`
    : `${FIRST}~${LAST}년 누적 합계(수입+수출+환적) 기준 상위 5개국입니다. 이름을 누르면 국가 상세가 바뀝니다.`;
  const colors=[1,2,3,4,5].map(i=>css('--c'+i));
  const series=TOP5.map((n,i)=>{const raw=YEARS.map(y=>(find(y,n)||ZERO(y,n)).tot); const v0=raw[0]||1;
    return {n,c:colors[i],raw,v:idxMode?raw.map(x=>x/v0*100):raw,g:raw[L]/v0-1};});
  document.getElementById('t5Legend').innerHTML=series.map(s=>`<span class="lg" data-n="${s.n}"><i style="background:${s.c}"></i>${s.n} <b>${sgn(s.g)}</b></span>`).join('');
  document.querySelectorAll('#t5Legend .lg').forEach(e=>e.onclick=()=>{state.country=e.dataset.n; renderAll();});
  const W=Math.max(300,host.clientWidth), H=W<500?250:300, m={t:16,r:W<500?80:118,b:26,l:48};
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'상위 5개국 연도별 추이'},host);
  const all=series.flatMap(s=>s.v), iw=W-m.l-m.r, ih=H-m.t-m.b;
  let lo,hi,step;
  if(idxMode){ step=niceStep((Math.max(...all)-Math.min(...all,100))/4||10); lo=Math.floor(Math.min(...all,100)/step)*step; hi=Math.ceil(Math.max(...all,100)/step)*step; }
  else { hi=niceMax(Math.max(...all),4); lo=0; step=hi/4; }
  const xs=i=>m.l+(iw/L)*i, ys=v=>m.t+ih-((v-lo)/(hi-lo))*ih;
  for(let v=lo; v<=hi+1e-9; v+=step){const yy=ys(v); el('line',{x1:m.l,x2:W-m.r,y1:yy,y2:yy,class:(idxMode?Math.abs(v-100)<1e-9:v===0)?'base':'gl'},svg);
    txt(svg,m.l-8,yy+4,idxMode?nf.format(v):(v?axisLabel(v):'0'),{class:'tick','text-anchor':'end'});}
  YEARS.forEach((y,i)=>txt(svg,xs(i),H-8,y,{class:'tick','text-anchor':'middle'}));
  const cross=el('line',{x1:0,x2:0,y1:m.t,y2:m.t+ih,stroke:css('--axis'),'stroke-width':1,visibility:'hidden'},svg);
  series.forEach(s=>{
    el('path',{d:s.v.map((v,i)=>(i?'L':'M')+xs(i)+','+ys(v)).join(''),fill:'none',stroke:s.c,'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'},svg);
    s.v.forEach((v,i)=>el('circle',{cx:xs(i),cy:ys(v),r:i===L?5:3.5,fill:s.c,stroke:css('--surface'),'stroke-width':2},svg));
  });
  // 끝 라벨: 겹치지 않게 위아래 간격 확보
  const ends=series.map(s=>({s,y:ys(s.v[L])})).sort((a,b)=>a.y-b.y), gap=14;
  for(let i=1;i<ends.length;i++) if(ends[i].y-ends[i-1].y<gap) ends[i].y=ends[i-1].y+gap;
  const over=ends[ends.length-1].y-(m.t+ih); if(over>0) ends.forEach(e=>e.y-=over);
  ends.forEach(e=>{const ly=ys(e.s.v[L]);
    if(Math.abs(e.y-ly)>2) el('line',{x1:xs(L)+6,y1:ly,x2:xs(L)+12,y2:e.y,stroke:css('--axis'),'stroke-width':1},svg);
    txt(svg,xs(L)+14,e.y+4,`${e.s.n} ${idxMode?nf.format(e.s.v[L]):man(e.s.v[L])}`,{class:'val'});});
  const band=iw/L;
  YEARS.forEach((y,i)=>{
    const hit=el('rect',{x:xs(i)-band/2,y:m.t,width:band,height:ih,class:'hit'},svg);
    bindTip(hit,e=>{cross.setAttribute('x1',xs(i));cross.setAttribute('x2',xs(i));cross.setAttribute('visibility','visible');
      const lines=[...series].sort((a,b)=>b.raw[i]-a.raw[i]).map(s=>{const yoy=i?s.raw[i]/s.raw[i-1]-1:null;
        return {k:s.n,c:s.c,v:(idxMode?nf.format(s.v[i])+' · ':'')+man(s.raw[i])+(yoy===null?'':` (${sgn(yoy)})`)};});
      showTip(e,`${y}년${i?' · 괄호는 전년 대비':''}`,lines);});
    hit.addEventListener('pointerleave',()=>cross.setAttribute('visibility','hidden'));
  });
}

function renderAll(){
  document.querySelectorAll('#yearSeg button').forEach(b=>b.setAttribute('aria-pressed',b.id==='y'+state.year));
  document.querySelectorAll('#measSeg button').forEach(b=>b.setAttribute('aria-pressed',b.id==='m'+state.meas));
  hideTip(); save();
  renderKPIs(); renderYearChart(); renderGrowth(); renderRank(); renderDetail(); renderTop5(); renderTable();
}
buildFilters(); renderAll();
let rt; new ResizeObserver(()=>{clearTimeout(rt); rt=setTimeout(()=>{renderYearChart(); renderGrowth(); renderRank(); renderDetail(); renderTop5();},120);}).observe(document.querySelector('.wrap'));
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',renderAll);
</script>
</body>
</html>
"""


# 4. 화면에 띄우기
if not DATA_PATH.exists():
    st.error("데이터 파일을 찾을 수 없습니다. 아래 경로 중 한 곳에 data2025.csv를 두세요.\n\n"
             + "\n".join(f"- {p}" for p in DATA_CANDIDATES))
    st.stop()

try:
    country_year = load_country_year(DATA_PATH)
except ValueError as e:
    st.error(str(e))
    st.stop()

records = to_records(country_year)
config = {"defaultCountry": DEFAULT_COUNTRY, "growthMin": GROWTH_MIN_TEU, "top5Exclude": TOP5_EXCLUDE}
html = (
    HTML_TEMPLATE
    .replace("__DATA__", json.dumps(records, ensure_ascii=False))
    .replace("__CONFIG__", json.dumps(config, ensure_ascii=False))
)
components.html(html, height=DASHBOARD_HEIGHT, scrolling=True)
