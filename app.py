import pandas as pd
import streamlit as st
import plotly.express as px

# ==========================================
# ★ 페이지 설정
# ==========================================

st.set_page_config(
    page_title="철도 데이터 분석 대시보드",
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터 읽기
df = pd.read_csv(
    "/content/drive/MyDrive/데이터분석(26.10.19~21)/analysis_result.csv"
)

df["측정시각"] = pd.to_datetime(df["측정시각"])

# 제목과 설명
st.title("🚄 철도 데이터 분석 대시보드")
st.write(
    "교육용 가상 자료입니다. AI 확인후보는 고장 확정이 아닙니다."
)

# ==========================================
# ★ 사이드바 - 분석 조건 설정
# ==========================================

st.sidebar.header("⚙️ 분석 조건 설정")

equipment = st.sidebar.selectbox(
    "설비 선택",
    df["설비ID"].unique()
)

view = df[df["설비ID"] == equipment].copy()

start = st.sidebar.date_input(
    "시작일",
    view["측정시각"].min().date()
)

end = st.sidebar.date_input(
    "종료일",
    view["측정시각"].max().date()
)

if start > end:
    st.sidebar.error("시작일이 종료일보다 늦습니다.")
    st.stop()

view = view[
    (view["측정시각"].dt.date >= start) &
    (view["측정시각"].dt.date <= end)
]

st.sidebar.divider()

# ==========================================
# ★ 공통 분석 데이터 계산
# ==========================================

if len(view) == 0:
    st.warning("조회 결과가 없습니다. 날짜를 다시 선택하세요.")
    st.stop()

# AI 점검 후보
candidates = view[
    view["AI결과"] == "확인후보"
]

# 온도 예측 분석
pred = view.dropna(
    subset=["다음온도_C", "AI예측온도_C"]
)

if len(pred) > 0:
    mae = (
        pred["다음온도_C"] -
        pred["AI예측온도_C"]
    ).abs().mean()
    mae_text = f"{mae:.2f} ℃"
else:
    mae_text = "자료 없음"

# ==========================================
# ★ 메인 화면 - 분석 탭 생성
# ==========================================

tab1, tab2, tab3 = st.tabs([
    "📋 데이터 조회 결과",
    "🔍 AI 점검 후보",
    "📈 다음 1시간 온도 예측"
])

# ==========================================
# ★ TAB 1 - 데이터 조회 결과
# ==========================================

with tab1:

    st.subheader("📋 데이터 조회 결과")

    st.metric(
        "조회 행 수",
        len(view)
    )

    st.dataframe(
        view,
        use_container_width=True
    )

# ==========================================
# ★ TAB 2 - AI 점검 후보
# ==========================================

with tab2:

    st.subheader("🔍 AI 점검 후보")

    st.metric(
        "AI 확인후보 건수",
        len(candidates)
    )

    st.write("AI 분석 결과 분포")

    st.dataframe(
        view["AI결과"].value_counts(),
        use_container_width=True
    )

    fig = px.line(
        view,
        x="측정시각",
        y="온도_C",
        title="온도 추이와 AI 확인후보"
    )

    fig.add_scatter(
        x=candidates["측정시각"],
        y=candidates["온도_C"],
        mode="markers",
        name="확인후보",
        marker=dict(
            color="red",
            size=10
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.write("AI 확인후보 상세 데이터")

    st.dataframe(
        candidates,
        use_container_width=True
    )

# ==========================================
# ★ TAB 3 - 다음 1시간 온도 예측
# ==========================================

with tab3:

    st.subheader("📈 다음 1시간 온도 예측")

    st.metric(
        "평균 절대 오차(MAE)",
        mae_text
    )

    st.write(
        "비교한 자료:",
        len(pred),
        "건"
    )

    if len(pred) > 0:

        fig2 = px.line(
            pred,
            x="목표시각",
            y=[
                "다음온도_C",
                "AI예측온도_C"
            ],
            title="실제 온도와 AI 예측 온도"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    else:
        st.info("온도 예측 비교 자료가 없습니다.")

# ==========================================
# ★ 사이드바 - 업무 검토 및 저장
# ==========================================

st.sidebar.header("📝 업무 검토 및 저장")

note = st.sidebar.text_area(
    "확인할 사항 및 조치 제안",
    "센서 상태와 운전 조건을 확인한 후 담당자 검토가 필요합니다.",
    height=150
)

report = f"""설비: {equipment}
조회 기간: {start} ~ {end}
조회 건수: {len(view)}건
AI 확인후보: {len(candidates)}건
온도 예측 MAE: {mae_text} ({len(pred)}건 비교)
업무 메모: {note}
교육용 가상 자료이며, 확인후보는 고장 확정이 아닙니다."""

st.sidebar.subheader("📥 파일 다운로드")

st.sidebar.download_button(
    "조회 결과 CSV",
    view.to_csv(index=False).encode("utf-8-sig"),
    "dashboard_result.csv",
    mime="text/csv",
    use_container_width=True
)

st.sidebar.download_button(
    "점검 후보 CSV",
    candidates.to_csv(index=False).encode("utf-8-sig"),
    "inspection_candidates.csv",
    mime="text/csv",
    use_container_width=True
)

st.sidebar.download_button(
    "보고서 TXT",
    report.encode("utf-8-sig"),
    "dashboard_report.txt",
    mime="text/plain",
    use_container_width=True
)

# ==========================================
# ★ 업무 보고서 미리보기
# ==========================================

with st.expander("📄 업무 보고서 미리보기"):
    st.text(report)
