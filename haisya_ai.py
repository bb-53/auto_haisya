import streamlit as st
import google.generativeai as genai

st.title("API診断テスト")
api_key = st.text_input("新しいAPIキーを入力", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # あなたのキーで今すぐ使えるモデルを全部書き出す
        models = [m.name for m in genai.list_models()]
        st.write("### ✅ 接続成功！")
        st.write("あなたが今使えるモデル一覧:")
        st.success(models)
        
        if "models/gemini-1.5-flash" in models:
            st.info("おめでとうございます！Gemini 1.5 Flashが使えます。")
        else:
            st.warning("リストに1.5-flashがありません。アカウント設定が必要です。")
            
    except Exception as e:
        st.error(f"❌ 接続エラー: {e}")
