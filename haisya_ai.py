import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="LINE内容整理くん")
st.title("🚐 LINE依頼内容の整理（最新モデル版）")

# サイドバーでAPIキー入力
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")

if not api_key:
    st.warning("APIキーを入力してください")
    st.stop()

# LINE文の入力
line_text = st.text_area("LINEの依頼文をここに貼り付けてください", height=200, placeholder="例：3/10 佐藤 10:00〜19:00 現場：渋谷公会堂...")

if st.button("内容を整理する") and line_text:
    try:
        genai.configure(api_key=api_key)
        
        # あなたのリストにあった最新の「2.0-flash」を指定します
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        あなたは送迎業界のプロ配車マンです。
        以下のLINEの依頼文を解析し、情報を抽出して見やすいテーブル（表）形式で整理してください。

        【抽出項目】
        ・日付
        ・ドライバー名
        ・車両（ナンバーや車種）
        ・稼働時間
        ・現場（行き先・住所）

        【LINE文】
        {line_text}
        """
        
        with st.spinner('最新AIが解析中...'):
            response = model.generate_content(prompt)
            st.success("解析完了！")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
