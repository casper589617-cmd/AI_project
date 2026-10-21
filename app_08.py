import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="철도 설비 데이터 분석", page_icon="🚄", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.stApp {background:#f5f7fb; color:#17263c;}
.block-container {padding-top:1.5rem; max-width:1500px;}
[data-testid="stSidebar"] {background:#101e32;}
[data-testid="stSidebar"] * {color:#eef3fa;}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {color:#17263c !important;}
[data-testid="stSidebar"] [data-baseweb="select"] * {color:#17263c;}
[data-testid="stMetric"] {background:white; border:1px solid #e1e8f0; border-radius:14px; padding:18px; box-shadow:0 3px 12px rgba(25,43,65,.04);}
[data-testid="stMetricLabel"] {color:#63738b;}
[data-testid="stMetricValue"] {color:#142c4c;}
.stTabs [data-baseweb="tab-list"] {gap:10px; border-bottom:1px solid #dce4ee;}
.stTabs [data-baseweb="tab"] {padding:12px 18px; border-radius:10px 10px 0 0; font-weight:600;}
.stTabs [aria-selected="true"] {background:#e7effc; color:#1b58a6;}
.hero {background:linear-gradient(115deg,#112743,#1b4b78); color:white; border-radius:18px; padding:25px 30px; margin-bottom:18px;}
.hero h1 {color:white; margin:0 0 7px 0; font-size:1.85rem;}
.hero p {color:#cbd9eb; margin:0; font-size:.94rem;}
.section-note {color:#62758b; font-size:.92rem; margin-bottom:12px;}
</style>""", unsafe_allow_html=True)

DATA_PATH = "analysis_result.csv"

@st.cache_data(show_spinner="분석 데이터를 불러오는 중입니다...")
def load_data(path):
    data = pd.read_csv(path)
    required = {"측정시각", "설비ID", "AI결과", "온도_C", "다음온도_C", "AI예측온도_C", "목표시각"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError("필수 열 누락: " + ", ".join(sorted(missing)))
    data["측정시각"] = pd.to_datetime(data["측정시각"], errors="coerce")
    data["목표시각"] = pd.to_datetime(data["목표시각"], errors="coerce")
    for c in ["온도_C", "다음온도_C", "AI예측온도_C"]:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    return data.dropna(subset=["측정시각", "설비ID"]).sort_values("측정시각")

try:
    df = load_data(DATA_PATH)
except Exception as e:
    st.error(f"데이터를 불러올 수 없습니다: {e}")
    st.stop()
if df.empty:
    st.warning("분석 가능한 데이터가 없습니다.")
    st.stop()

with st.sidebar:
    st.markdown("## 🚄 RAIL ANALYTICS")
    st.caption("설비 상태 · AI 점검 · 온도 예측")
    st.divider()
    st.subheader("⚙️ 분석 조건")
    equipment = st.selectbox("설비 선택", sorted(df["설비ID"].unique().tolist(), key=str))
    equipment_df = df.loc[df["설비ID"] == equipment].copy()
    min_date = equipment_df["측정시각"].min().date()
    max_date = equipment_df["측정시각"].max().date()
    start = st.date_input("시작일", value=min_date, key=f"start_{equipment}", min_value=min_date, max_value=max_date)
    end = st.date_input("종료일", value=max_date, key=f"end_{equipment}", min_value=min_date, max_value=max_date)
    if start > end:
        st.error("시작일은 종료일보다 늦을 수 없습니다.")
        st.stop()
    st.caption("선택한 조건이 모든 탭에 공통 적용됩니다.")

view = equipment_df.loc[equipment_df["측정시각"].dt.date.between(start, end)].copy()
candidates = view.loc[view["AI결과"] == "확인후보"].copy()
pred = view.dropna(subset=["목표시각", "다음온도_C", "AI예측온도_C"]).copy()
mae = (pred["다음온도_C"] - pred["AI예측온도_C"]).abs().mean() if not pred.empty else float("nan")
mae_text = f"{mae:.2f} ℃" if pd.notna(mae) else "자료 없음"
candidate_rate = len(candidates) / len(view) * 100 if len(view) else 0.0

with st.sidebar:
    st.divider()
    st.subheader("📝 업무 검토")
    note = st.text_area("확인할 사항 및 조치 제안", value="센서 상태와 운전 조건을 확인한 후 담당자 검토가 필요합니다.", height=130)
    report = (f"설비: {equipment}\n조회 기간: {start} ~ {end}\n조회 건수: {len(view)}건\n"
              f"AI 확인후보: {len(candidates)}건 ({candidate_rate:.1f}%)\n"
              f"온도 예측 MAE: {mae_text} ({len(pred)}건 비교)\n업무 메모: {note}\n"
              "교육용 가상 자료이며, 확인후보는 고장 확정이 아닙니다.")
    st.subheader("📥 결과 다운로드")
    st.download_button("전체 조회 CSV", view.to_csv(index=False).encode("utf-8-sig"), "dashboard_result.csv", mime="text/csv", use_container_width=True)
    st.download_button("점검 후보 CSV", candidates.to_csv(index=False).encode("utf-8-sig"), "inspection_candidates.csv", mime="text/csv", use_container_width=True)
    st.download_button("업무 보고서 TXT", report.encode("utf-8-sig"), "dashboard_report.txt", mime="text/plain", use_container_width=True)

st.markdown('<div class="hero"><h1>철도 설비 데이터 분석 대시보드</h1><p>RAIL EQUIPMENT INTELLIGENCE · 설비 데이터 모니터링 및 AI 분석 지원</p></div>', unsafe_allow_html=True)
st.info(f"**현재 분석 조건**  |  설비: {equipment}  |  기간: {start} ~ {end}  |  AI 확인후보는 고장 확정이 아닙니다.", icon="ℹ️")

m1, m2, m3, m4 = st.columns(4)
m1.metric("측정 데이터", f"{len(view):,}건")
m2.metric("AI 확인후보", f"{len(candidates):,}건")
m3.metric("확인후보 비율", f"{candidate_rate:.1f}%")
m4.metric("예측 평균 오차(MAE)", mae_text)
st.write("")

tab1, tab2, tab3 = st.tabs(["📋 데이터 조회", "🔍 AI 점검 후보", "📈 1시간 온도 예측"])

with tab1:
    st.subheader("측정 데이터 조회")
    st.markdown('<div class="section-note">조회 조건에 해당하는 원본 측정값을 확인하고, 표에서 정렬·검색할 수 있습니다.</div>', unsafe_allow_html=True)
    if view.empty:
        st.warning("조회 결과가 없습니다. 왼쪽에서 기간을 변경하세요.")
    else:
        st.dataframe(view, use_container_width=True, hide_index=True, height=520)
        with st.expander("데이터 품질 확인"):
            st.write("컬럼별 결측값 수")
            st.dataframe(view.isna().sum().rename("결측 건수"), use_container_width=True)

with tab2:
    st.subheader("AI 점검 후보 분석")
    st.markdown('<div class="section-note">확인후보가 발생한 시점을 온도 추이와 함께 확인합니다. 실제 고장 여부는 별도 점검이 필요합니다.</div>', unsafe_allow_html=True)
    if view.empty:
        st.warning("표시할 데이터가 없습니다.")
    else:
        a, b = st.columns([2.2, 1])
        with a:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=view["측정시각"], y=view["온도_C"], mode="lines", name="측정 온도", line=dict(color="#2374bd", width=2)))
            fig.add_trace(go.Scatter(x=candidates["측정시각"], y=candidates["온도_C"], mode="markers", name="AI 확인후보", marker=dict(color="#e25353", size=9, symbol="circle")))
            fig.update_layout(title="온도 추이 및 확인후보 발생 시점", template="plotly_white", height=400, margin=dict(l=20,r=20,t=60,b=20), xaxis_title="측정시각", yaxis_title="온도 (℃)", hovermode="x unified", legend=dict(orientation="h", y=1.12))
            st.plotly_chart(fig, use_container_width=True)
        with b:
            counts = view["AI결과"].fillna("미분류").value_counts().reset_index()
            counts.columns = ["분류", "건수"]
            fig_counts = go.Figure(go.Bar(x=counts["건수"], y=counts["분류"].astype(str), orientation="h", marker_color="#3678b5"))
            fig_counts.update_layout(title="AI 분류별 건수", template="plotly_white", height=400, margin=dict(l=20,r=20,t=60,b=20), xaxis_title="건수", yaxis_title="")
            st.plotly_chart(fig_counts, use_container_width=True)
        with st.expander(f"확인후보 상세 목록 ({len(candidates):,}건)", expanded=True):
            if candidates.empty:
                st.success("선택한 기간에 AI 확인후보가 없습니다.")
            else:
                st.dataframe(candidates, use_container_width=True, hide_index=True, height=300)

with tab3:
    st.subheader("다음 1시간 온도 예측 정확도")
    st.markdown('<div class="section-note">실제 다음 온도와 AI 예측 온도를 비교합니다. MAE는 오차의 절댓값 평균으로, 낮을수록 예측이 실제값에 가깝습니다.</div>', unsafe_allow_html=True)
    st.caption(f"비교 가능한 데이터: {len(pred):,}건")
    if pred.empty:
        st.info("선택한 조건에서 실제·예측 온도를 함께 비교할 자료가 없습니다.")
    else:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=pred["목표시각"], y=pred["다음온도_C"], mode="lines", name="실제 온도", line=dict(color="#2374bd", width=2)))
        fig2.add_trace(go.Scatter(x=pred["목표시각"], y=pred["AI예측온도_C"], mode="lines", name="AI 예측 온도", line=dict(color="#e6a23c", width=2, dash="dash")))
        fig2.update_layout(title="실제 온도 vs AI 예측 온도", template="plotly_white", height=450, margin=dict(l=20,r=20,t=60,b=20), xaxis_title="목표시각", yaxis_title="온도 (℃)", hovermode="x unified", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, use_container_width=True)
        with st.expander("예측 오차 상세 데이터"):
            detail = pred[["목표시각", "다음온도_C", "AI예측온도_C"]].copy()
            detail["절대오차_C"] = (detail["다음온도_C"] - detail["AI예측온도_C"]).abs()
            st.dataframe(detail, use_container_width=True, hide_index=True)

with st.expander("📄 업무 보고서 미리보기"):
    st.text(report)
