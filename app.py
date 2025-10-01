import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from gspread_pandas import Spread
from gspread.exceptions import SpreadsheetNotFound, APIError

# ===============================================================
# 초기 설정
# ===============================================================
st.set_page_config(layout="wide")
st.title("🚀 성찰 일지 분석 대시보드 (진단 강화)")
st.markdown("---")

# ===============================================================
# 사용자 입력 UI
# ===============================================================
# ‼️ 여기에 본인의 Google Sheet 문서 이름을 정확하게 입력하세요.
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

# 데이터 불러오기 및 진단 기능이 강화된 함수
@st.cache_data(ttl=600)
def load_data_with_diagnostics(spreadsheet_name, sheet_name):
    """
    데이터 로딩을 시도하고, 실패 시 구체적인 원인과 해결책을 안내하는 함수
    """
    try:
        # ‼️ DEBUGGING: JSON 키를 코드에 직접 삽입하여 Secrets 문제인지 확인합니다.
        # ‼️ 보안상 매우 위험하므로, 테스트 후 반드시 원래의 코드로 되돌려야 합니다.
        creds_dict = {
            "type": "service_account",
            "project_id": "gen-lang-client-0622212754",
            "private_key_id": "3c30ffbb07392a4e6139db1ae9493e9ce15db68c",
            # ✨ FIX: private_key를 삼중 따옴표를 사용한 여러 줄 문자열로 변경하여 형식 오류를 원천 차단합니다.
            "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDunHjOLVgFg+s+
jBNGs1fPidPzrlbOH1B8Qn3wN2PtJSAUDSxtKQKHrg2nLZyp4of3dWWHOLfVKSBg
ZFadfaTTnaAyylnQZX4JFIe9Tvj2FklGkPzLWhmK1juufEkr0WKosxW5A1KxgQEW
pHYbeM1CGAyFDBwvcrEH0AfOMuHWtyWIMKNURmia8hddHduw5wdl8lCBqsCTwThQ
mefjDY1k34asF/wY0eL3rj0kTasg+wOrZsLp5PjPd23uV6/Xi1N64mgocBe15UYT
gII8/OyECBw6HjPcm4TJiUFnXMx5qnH0B5MyO2fQEEK9xnOEbXo0mHXeqoX9lp2C
PAA0ZIiJAgMBAAECggEAFKRRqRhwHG4InE0W389lAc29GcATv1ojJtTDu1O3X80N
5N4s4TaiguVSRguimWnA9G3h/hwwfw7DP8N+YLp9V1c0BCDQO0CEcjml8oER9YwB
A8tIKzlcq0+UMyiKVfGTtN9lOi+o6DUuSGyq0P6W1yhocNwW1h34ZaIgAr0RH3dm
0wCh4vq7wjx0xDpSpOj6kMaBy+F7fGB15Y+JX+4GGd44HjW0pOBliykeDY2DcJyo
myv+fy2OUarW1XjRRCO+H7MTJXxem4eiQUfHWW/b6Yw/mzMJ6OyNGfVWMRv1fdkR
9ek5pkjTgk9GUppZTiSvJdpC7I95DsxkoOKiv1YqAQKBgQD4iBNeMYbcfyl+Zl0C
nGoaTJ2RK0iE5aXyCKt3bEVJPYVtwBU0cl3Um3ltWBXKTSbPp3ILTiGbEmcKcBzI
29t/BdkiEfDrX2ufy3cWEWo9/FcbGOeAUalD2xPu10TNmSvkJw2pK8qNBcaOb2mS
offLvocgwkBF3RwhmF02XsCfgQKBgQD1yBSPdDkXQGqQfT16fqOlkE7rWFAQkIK1
sn9i38rQ5z3U5pmw2AIGBtXpQcA4grpjTJqgqZm2OuaZQeAE8dfHemDEMzD8KcMO
kXScrablGkyB6Tdfq8wqSU+LZDhMdcU0sLldKspzBTk3mLk46ZgwQSD9BhdR7YZF
wu+I1jVtCQKBgBcmze8TXAXETsA4lud8XKHwiykPyCShI/FE/3wTeOzWr0xG/XKy
SK1aglg+QWFkCH6Fkakd8SF5+GFPik7ntC3EBLMYysGSVPtAv+otWyFFFXQvwLkC
YmswyE2SfhVM9Hq/bJVav/adGB8Cn+oJ7oRrTjkt/0DC1TEH+X7sGrOBAoGBAIPI
2F1i8AmrnHgE7yXzKUPo8Kf4HlYDZlKOdwdI/7KritfRHa9Y4xzgJWqAutSSI+aC
eJaU2bqAMo0SaU+9bPmkgKYy3J0Yt2HkVCZ+ZfKJ+2Pc7Lf7oek6jdAr2JQGwcrS
x1FRVGP/9QH+fbIqblPRWCLTVUW0mj5lm5I/aT4hAoGBAI0d/jZVl8+I9zIHURIx
oDcM0yMydVGNBfw3Oe1besMcAQM4sRbyzeKf1grR8dzDMc48st2WCOoT+L5Cnsat
o4t/5pM+DvHYlAXba6Uc7TmcL0U0lX8m4/dsrmMsGQ4IcVFE8EeHPaUk6Zp3xNej
i7XCNja/n6bWkpGeja6HhPzW
-----END PRIVATE KEY-----""",
            "client_email": "streamlit-g-sheets-reader@gen-lang-client-0622212754.iam.gserviceaccount.com",
            "client_id": "107259292181379513848",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-g-sheets-reader%40gen-lang-client-0622212754.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        gspread_client = gspread.service_account_from_dict(creds_dict)


        # 3. 특정 스프레드시트 및 시트 접근 시도
        spread = Spread(spreadsheet_name, sheet=sheet_name, client=gspread_client)
        df = spread.sheet_to_df(index=False)
        
        # 데이터 타입 변환 및 정리
        for col in df.columns:
            if '점수' in col or '총점' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    # 4. 발생한 오류 종류에 따라 맞춤형 안내 메시지 표시
    except SpreadsheetNotFound:
        st.error(f"😭 시트 문서 이름 오류: '{spreadsheet_name}' 문서를 찾을 수 없습니다.")
        st.subheader("🔍 해결 방법")
        st.markdown(f"""
        1. `app.py` 파일의 `SPREADSHEET_NAME` 변수 값이 실제 구글 시트 문서 제목과 **대소문자, 띄어쓰기까지 정확히 일치**하는지 확인해주세요.
        2. 서비스 계정이 접근 가능한 파일 중에 이름이 같은 문서가 여러 개 있는지 확인해주세요.
        """)
        return None
        
    except APIError as e:
        error_details = e.response.json()
        error_status = error_details.get("error", {}).get("status")
        error_message = error_details.get("error", {}).get("message", "")

        st.error(f"😭 Google API 오류 발생: {error_status}")
        st.code(error_message, language=None)
        st.subheader("🔍 해결 방법")

        if error_status == "PERMISSION_DENIED":
            st.markdown("""
            **원인:** 서비스 계정이 구글 시트 문서를 읽을 권한이 없습니다.
            1. **`{spreadsheet_name}`** 구글 시트 문서의 **'공유'** 버튼을 누르세요.
            2. 본인의 서비스 계정 이메일(`...@...gserviceaccount.com`)을 **'뷰어(Viewer)' 권한으로 추가**했는지 다시 확인해주세요.
            3. **Google Drive API**가 활성화되어 있는지 확인해주세요.
            """.format(spreadsheet_name=spreadsheet_name))
        elif "API has not been used" in error_message or "is not enabled" in error_message:
            st.markdown("""
            **원인:** 프로젝트에서 Google Sheets API 또는 Google Drive API 사용 설정이 안 되어 있습니다.
            1. [Google Cloud API 라이브러리](https://console.cloud.google.com/apis/library)로 이동하세요.
            2. **'Google Sheets API'**를 검색하여 **'사용(Enable)'** 버튼을 눌러 활성화해주세요.
            3. **'Google Drive API'**도 동일하게 검색하여 활성화해주세요.
            """)
        else:
            st.markdown("JSON 키가 손상되었거나 다른 API 관련 문제일 수 있습니다. Google Cloud에서 새 키를 발급받아 Secrets를 업데이트해보세요.")
        return None

    except Exception as e:
        st.error("😭 예측하지 못한 오류가 발생했습니다.")
        st.info("이제 문제는 Secrets가 아닌, 다른 곳에 있을 확률이 높습니다.")
        st.code(f"상세 오류: {e}", language=None)
        return None

# ===============================================================
# 메인 로직
# ===============================================================
if st.sidebar.button("📊 내 결과 분석하기"):
    if not user_name or not user_email:
        st.warning("이름과 이메일을 모두 입력해주세요.")
    else:
        # 진단 기능이 포함된 함수를 호출합니다.
        df = load_data_with_diagnostics(SPREADSHEET_NAME, sheet_name)

        # df가 None이면 오류가 발생하여 함수가 중단된 것이므로, 아래 코드를 실행하지 않습니다.
        if df is not None:
            if df.empty:
                st.warning("데이터가 비어있습니다. 구글 시트에 채점 결과가 있는지 확인해주세요.")
            else:
                user_data = df[(df['이름'].str.strip() == user_name.strip()) & (df['이메일'].str.strip() == user_email.strip())]

                if user_data.empty:
                    st.error("일치하는 정보가 없습니다. 이름과 이메일, 그리고 선택한 성찰 일지가 맞는지 다시 확인해주세요.")
                else:
                    # --- (기존의 시각화 및 표 생성 코드는 여기부터 동일합니다) ---
                    user_series = user_data.iloc[0]
                    st.success(f"### {user_name}님의 [{selected_sheet_key}] 분석 결과입니다.")
                    st.markdown("---")

                    st.subheader("📈 전체 집단과 나의 위치 비교")
                    st.info("Box Plot은 전체 응답자의 점수 분포를 보여줍니다. 상자 안의 선은 중앙값이며, 붉은 별⭐은 나의 점수 위치를 나타냅니다.")

                    score_columns = ['총점', '1-1 점수', '1-2 점수', '1-3 점수', '2-1 점수', '2-2 점수', '2-3 점수', '3-1 점수', '3-2 점수', '3-3 점수']
                    cols = st.columns(len(score_columns))

                    for i, col_name in enumerate(score_columns):
                        with cols[i]:
                            fig = go.Figure()
                            fig.add_trace(go.Box(y=df[col_name].dropna(), name='전체 분포', marker_color='#1f77b4'))
                            fig.add_trace(go.Scatter(y=[user_series[col_name]], mode='markers', name='나의 점수', marker=dict(color='red', size=12, symbol='star')))
                            fig.update_layout(title=dict(text=f'<b>{col_name}</b>', x=0.5), showlegend=False, yaxis_title="점수", margin=dict(l=10, r=10, t=40, b=10), height=350)
                            st.plotly_chart(fig, use_container_width=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("📑 문항별 세부 결과")
                    st.info("각 문항별 나의 점수, 내가 작성한 답변, 그리고 AI가 제시한 채점 근거입니다.")
                    summary_data = []
                    question_indices = ['1-1', '1-2', '1-3', '2-1', '2-2', '2-3', '3-1', '3-2', '3-3']
                    for idx in question_indices:
                        summary_data.append({"문항": f"**{idx}**", "나의 점수": user_series[f'{idx} 점수'], "내가 작성한 답변": user_series[idx], "채점 근거": user_series[f'{idx} 근거']})
                    summary_df = pd.DataFrame(summary_data)
                    st.markdown(summary_df.to_html(escape=False, index=False), unsafe_allow_html=True)

