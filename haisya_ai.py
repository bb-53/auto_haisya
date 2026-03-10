import streamlit as st
import google.generativeai as genai

# ページの設定
st.set_page_config(page_title="LINE解析テスト")
st.title("🚐 LINE内容の整理テスト")

# サイドバーでAPIキーを入力
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")

if not api_key:
    st.warning("左側のサイドバーにAPIキーを入力してください。")
    st.stop()

# LINE文の入力
line_text = st.text_area("LINEの依頼文を貼り付けてください", height=200)

if st.button("内容を整理する") and line_text:
    try:
        # APIの設定（ここが21行目付近です。半角スペースに修正済み）
        genai.configure(api_key=api_key)
        
        # 404エラー対策：最もシンプルなモデル名
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        以下のLINE文から情報を抽出し、表形式で整理してください。
        項目：日付、名前、車両、時間、現場
        
        【LINE文】
        {line_text}
        """
        
        with st.spinner('ベテラン配車マンが解析中...'):
            response = model.generate_content(prompt)
            st.success("整理が完了しました！")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"エラーが発生しました。")
        st.info(f"詳細: {e}")
