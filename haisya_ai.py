import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="LINE内容整理くん")
st.title("🚐 LINE依頼内容の整理テスト")

# サイドバーでAPIキーだけ入力
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")

if not api_key:
    st.warning("APIキーを入力してください")
    st.stop()

# LINE文の入力
line_text = st.text_area("LINEの依頼文をここに貼り付けてください", height=200, placeholder="例：3/10 佐藤 10:00〜19:00 現場：渋谷公会堂 車両：1234")

if st.button("内容を整理する"):
    try:
        genai.configure(api_key=api_key)
        # 最もエラーが出にくいシンプルな指定
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # AIへの指示（プロンプト）
        prompt = f"""
        以下のLINEの依頼文から情報を抽出し、指定の項目で一覧（テーブル形式）に整理してください。
        不明な項目は「不明」と記載してください。

        【抽出項目】
        ・日付
        ・名前
        ・車両（ナンバーや車種）
        ・稼働時間
        ・現場住所

        【LINE文】
        {line_text}
        """
        
        with st.spinner('解析中...'):
            response = model.generate_content(prompt)
            st.success("整理完了！")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.info("※404エラーが出る場合は、APIキーが『新しいプロジェクト』で作成されているか確認してください。")
