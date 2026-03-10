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
        
        # 'gemini-2.0-flash' をやめて、こちらに変更
        model = genai.GenerativeModel('gemini-flash-latest')

        prompt = f"""
        以下のLINE文（複数件の依頼が含まれています）から、稼働予約の一覧を作成してください。
        
        【ルール】
        ・日付ごとにグループ分けしてください。
        ・同じ日の依頼は、１．２．３．と連番を振ってください。
        ・「名前」「車両ナンバー」「稼働時間」を抽出してください。
        
        【LINE文】
        {line_text}
        """
       
        with st.spinner('最新AIが解析中...'):
            response = model.generate_content(prompt)
            st.success("解析完了！")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
