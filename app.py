import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from gspread_pandas import Spread, Client

# ===============================================================
# 초기 설정
# ===============================================================
st.set_page_config(layout="wide")
st.title("🚀 성찰 일지 분석 대시보드")
st.markdown("---")

# Google Sheets 인증 (Streamlit Secrets 사용)
# GCP에서 서비스 계정을 만들고 JSON 키를 생성해야 합니다.
# 생성된 JSON 내용을 Streamlit Cloud의 Secrets에 'gcp_service_account'라는 이름으로 저장하세요.
try:
    creds = st.secrets["gcp_service_account"]
    client = Client(creds)
except Exception as e:
    st.error("Google Sheets 인증 정보를 불러오는 데 실패했습니다. Streamlit Secrets 설정을 확인해주세요.")
    st.info("자세한 설정 방법은 함께 제공된 README.md 파일을 참고하세요.")
    st.stop()


# ===============================================================
# 사용자 입력 UI
# ===============================================================
# 구글 시트 문서 이름을 입력하세요.
SPREADSHEET_NAME = "student_perspective" 

# Apps Script에 정의된 시트 이름과 동일하게 작성합니다.
SHEET_OPTIONS = {
    "1번 부력": "1번 부력",
    "2번 앙금": "2번 앙금",
    "3번 열평형": "3번 열평형",
    "4번 원자": "4번 원자",
    "5번 오목거울": "5번 오목거울",
    "6번 밀도": "6번 밀도"
}

st.sidebar.header("조회 정보 입력")
selected_sheet_key = st.sidebar.selectbox(
    "분석할 성찰 일지를 선택하세요:",
    options=list(SHEET_OPTIONS.keys())
)
sheet_name = SHEET_OPTIONS[selected_sheet_key]

user_name = st.sidebar.text_input("이름을 입력하세요:")
user_email = st.sidebar.text_input("이메일을 입력하세요:")

# 데이터 불러오기 및 캐싱
@st.cache_data(ttl=600) # 10분마다 데이터 새로고침
def load_data(spreadsheet_name, sheet_name):
    try:
        spread = Spread(spreadsheet_name, sheet=sheet_name, client=client)
        df = spread.sheet_to_df(index=False)
        # 데이터 타입 변환 및 정리
        for col in df.columns:
            if '점수' in col or '총점' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        st.error(f"'{sheet_name}' 시트를 불러오는 중 오류가 발생했습니다: {e}")
        return None

if st.sidebar.button("📊 내 결과 분석하기"):
    if not user_name or not user_email:
        st.warning("이름과 이메일을 모두 입력해주세요.")
    else:
        df = load_data(SPREADSHEET_NAME, sheet_name)

        if df is not None and not df.empty:
            # 사용자 데이터 필터링
            user_data = df[(df['이름'].str.strip() == user_name.strip()) & (df['이메일'].str.strip() == user_email.strip())]

            if user_data.empty:
                st.error("일치하는 정보가 없습니다. 이름과 이메일을 다시 확인해주세요.")
            else:
                user_series = user_data.iloc[0]
                st.success(f"### {user_name}님의 [{selected_sheet_key}] 분석 결과입니다.")
                st.markdown("---")

                # ===============================================================
                # 1. Box Plot 시각화
                # ===============================================================
                st.subheader("📈 전체 집단과 나의 위치 비교")
                st.info("Box Plot은 전체 응답자의 점수 분포를 보여줍니다. 상자 안의 선은 중앙값이며, 붉은 별⭐은 나의 점수 위치를 나타냅니다.")

                score_columns = [
                    '총점', '1-1 점수', '1-2 점수', '1-3 점수', '2-1 점수',
                    '2-2 점수', '2-3 점수', '3-1 점수', '3-2 점수', '3-3 점수'
                ]
                
                # 10개의 컬럼을 만들어 plot을 나란히 표시
                cols = st.columns(len(score_columns))

                for i, col_name in enumerate(score_columns):
                    with cols[i]:
                        fig = go.Figure()

                        # 전체 데이터 Box Plot
                        fig.add_trace(go.Box(
                            y=df[col_name].dropna(),
                            name='전체 분포',
                            marker_color='#1f77b4'
                        ))

                        # 사용자 점수 Scatter Plot
                        fig.add_trace(go.Scatter(
                            y=[user_series[col_name]],
                            mode='markers',
                            name='나의 점수',
                            marker=dict(color='red', size=12, symbol='star')
                        ))

                        fig.update_layout(
                            title=dict(text=f'<b>{col_name}</b>', x=0.5),
                            showlegend=False,
                            yaxis_title="점수",
                            margin=dict(l=10, r=10, t=40, b=10),
                            height=350
                        )
                        st.plotly_chart(fig, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ===============================================================
                # 2. 세부 결과표
                # ===============================================================
                st.subheader("📑 문항별 세부 결과")
                st.info("각 문항별 나의 점수, 내가 작성한 답변, 그리고 AI가 제시한 채점 근거입니다.")

                summary_data = []
                question_indices = ['1-1', '1-2', '1-3', '2-1', '2-2', '2-3', '3-1', '3-2', '3-3']

                for idx in question_indices:
                    summary_data.append({
                        "문항": f"**{idx}**",
                        "나의 점수": user_series[f'{idx} 점수'],
                        "내가 작성한 답변": user_series[idx],
                        "채점 근거": user_series[f'{idx} 근거']
                    })

                summary_df = pd.DataFrame(summary_data)
                
                # DataFrame을 HTML로 변환하여 스타일 적용
                st.markdown(summary_df.to_html(escape=False, index=False), unsafe_allow_html=True)
