import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# --- 환경 변수 ---
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_DATABASE')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# --- 데이터베이스 연결 ---
def get_db_connection():
    """데이터베이스 연결 객체를 생성하고 반환합니다."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except mysql.connector.Error as err:
        st.error(f"데이터베이스 연결 오류: {err}")
        return None

def execute_query(query, params=None, fetch=None):
    """쿼리를 실행하고, 실행 후에는 반드시 연결을 종료합니다."""
    conn = get_db_connection()
    if conn is None:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        if fetch == 'one':
            result = cursor.fetchone()
        elif fetch == 'all':
            result = cursor.fetchall()
        else:
            conn.commit()
            result = None
        return result
    except mysql.connector.Error as err:
        st.error(f"쿼리 실행 중 오류 발생: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

# --- 이메일 발송 기능 ---
def send_email(recipient_email, student_name, email_content_html):
    """지정된 이메일 주소로 대화 내용을 HTML 형식으로 발송합니다."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        st.error("이메일 설정이 누락되었습니다. .env 파일을 확인하세요.")
        return

    subject = f"[AI 물리 학습] {student_name} 학생의 전체 대화 기록입니다."
    
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(email_content_html, 'html', 'utf-8'))

    try:
        with st.spinner(f"{recipient_email} (으)로 이메일을 발송하는 중입니다..."):
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
            server.quit()
        st.success("이메일 발송에 성공했습니다!")
    except smtplib.SMTPAuthenticationError:
        st.error("이메일 발송 인증에 실패했습니다. 이메일 주소 또는 앱 비밀번호를 확인하세요.")
    except Exception as e:
        st.error(f"이메일 발송 중 오류가 발생했습니다: {e}")

# --- 메인 애플리케이션 ---
def main():
    st.set_page_config(page_title="학습 데이터 조회 시스템", layout="wide")
    st.header("👨‍🏫 학습 데이터 조회 및 발송 (관리자용)")

    # 1. DB에서 학생 목록 가져오기
    students = execute_query(
        "SELECT id, name, email, date FROM paced_learning ORDER BY date DESC",
        fetch='all'
    )

    if not students:
        st.warning("조회할 학습 데이터가 없습니다.")
        return

    # 2. 콤보박스(selectbox) 생성을 위한 옵션 준비
    student_options = {f"{s['name']} ({s['email']}) - {s['date'].strftime('%Y-%m-%d %H:%M')}": s['id'] for s in students}
    selected_student_label = st.selectbox(
        "조회할 학생을 선택하세요.",
        options=student_options.keys()
    )

    if not selected_student_label:
        return

    selected_id = student_options[selected_student_label]
    
    # 3. 선택된 학생의 전체 대화 내용 조회
    student_data = execute_query(
        """
        SELECT name, email, domain_1_content, domain_2_content, domain_3_content, 
               domain_4_content, domain_5_content, domain_6_content 
        FROM paced_learning WHERE id = %s
        """,
        params=(selected_id,),
        fetch='one'
    )
        
    if not student_data:
        st.error("선택된 학생의 데이터를 찾을 수 없습니다.")
        return

    # 4. Email/Markdown용 대화 내용 준비
    email_body_html = f"<h1>{student_data['name']} ({student_data['email']}) 학생의 학습 대화 기록</h1>"
    markdown_content = f"# {student_data['name']} ({student_data['email']}) 학생의 학습 대화 기록\n\n"
    is_conversation_exist = False

    for i in range(1, 7):
        content_col = f'domain_{i}_content'
        conversation_json = student_data.get(content_col)
        
        if conversation_json:
            is_conversation_exist = True
            email_body_html += f"<hr><h2>📚 Domain {i}</h2>"
            markdown_content += f"---\n\n## 📚 Domain {i}\n\n"
            
            try:
                conversation = json.loads(conversation_json)
                for message in conversation:
                    if message.get('role') and message['role'] != 'system':
                        role_emoji = "🧑‍🎓" if message['role'] == 'user' else "🤖"
                        timestamp = message.get('timestamp', '')
                        
                        # 이메일 본문용 HTML 생성
                        bg_color = '#f1f8e9' if message['role'] == 'user' else '#e1f5fe'
                        content_html = message['content'].replace('\n', '<br>')
                        email_body_html += f"""
                            <div style="margin: 10px; padding: 10px; border-radius: 8px; background-color: {bg_color};">
                                <p><b>{role_emoji} {message['role'].capitalize()}</b> ({timestamp})</p>
                                <div>{content_html}</div>
                            </div>
                        """
                        
                        # 마크다운 본문 생성
                        markdown_content += f"**{role_emoji} {message['role'].capitalize()}** ({timestamp})\n\n"
                        markdown_content += f"```\n{message['content']}\n```\n\n"

            except (json.JSONDecodeError, TypeError):
                error_message = f"Domain {i}의 대화 기록을 불러오는 데 실패했습니다. (형식 오류)"
                email_body_html += f"<p><b>오류:</b> {error_message}</p>"
                markdown_content += f"**오류:** {error_message}\n\n"

    # 5. 이메일 발송 및 페이지 저장 버튼 (콤보박스 바로 아래에 위치)
    if is_conversation_exist:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 전체 대화 내용 이메일로 발송", use_container_width=True):
                send_email(
                    recipient_email=student_data['email'],
                    student_name=student_data['name'],
                    email_content_html=email_body_html
                )
        with col2:
            safe_student_name = re.sub(r'[\\/*?:"<>|]', "", student_data['name'])
            st.download_button(
               label="📄 페이지 저장 (Markdown)",
               data=markdown_content.encode('utf-8'),
               file_name=f"{safe_student_name}_학습기록.md",
               mime="text/markdown",
               use_container_width=True
            )
    
    st.subheader(f"'{student_data['name']}' 학생의 전체 대화 내용")

    # 6. 화면에 대화 내용 출력
    if not is_conversation_exist:
        st.info("아직 저장된 대화 내용이 없습니다.")
        return
        
    for i in range(1, 7):
        content_col = f'domain_{i}_content'
        conversation_json = student_data.get(content_col)
        
        if conversation_json:
            st.markdown(f"--- \n ### 📚 Domain {i}")
            try:
                conversation = json.loads(conversation_json)
                for message in conversation:
                    if message.get('role') and message['role'] != 'system':
                        role_emoji = "🧑‍🎓" if message['role'] == 'user' else "🤖"
                        timestamp = message.get('timestamp', '')
                        with st.chat_message(name=message['role'], avatar=role_emoji):
                            if timestamp:
                                st.write(f"_{timestamp}_")
                            st.markdown(message['content'])
            except (json.JSONDecodeError, TypeError):
                 st.error(f"Domain {i}의 대화 기록을 화면에 표시하는 데 실패했습니다.")


if __name__ == "__main__":
    main()

