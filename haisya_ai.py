import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

st.set_page_config(page_title="育成型・配車デスクAI", layout="wide")
st.title("🚐 育成型・配車デスクAI")

# --- 1. 記憶（ルール）の管理機能 ---
KNOWLEDGE_FILE = "log_knowledge.txt"

def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "まだ学習したルールはありません。"

def save_knowledge(new_content):
    with open(KNOWLEDGE_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n- {new_content}")

# --- 2. 初期設定とサイドバー ---
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    st.write("### 📚 現在の学習済みルール")
    knowledge = load_knowledge()
    st.info(knowledge)
    if st.button("記憶をリセット"):
        if os.path.exists(KNOWLEDGE_FILE):
            os.remove(KNOWLEDGE_FILE)
            st.rerun()

if not api_key:
    st.warning("APIキーを入力してください")
    st.stop()

# --- 3. メイン画面：対話と配車 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# チャット履歴の表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# あなたの指示（プロンプト）入力
if prompt := st.chat_input("例：『この配車案をベースに、石井さんはMT車NGだから別の車に変えて』"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # 過去のルールと会話履歴をコンテキストに含める
        full_context = f"""
        あなたはユーザーの配車判断基準を学習中の配車デスクです。
        以下の【これまでに学んだルール】を絶対守ってください。

        【これまでに学んだルール】
        {knowledge}

        【ユーザーからの最新の指示】
        {prompt}
        """
        
        with st.chat_message("assistant"):
            response = model.generate_content(full_context)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # AIに「今教わった新しいルール」を抽出させる（これが学習プロセス）
            learn_prompt = f"今の会話から、今後も守るべき『配車ルール』だけを一言で抽出して。例：『〇〇さんは大型車NG』。なければ『なし』と答えて。 会話：{prompt} -> {response.text}"
            new_rule = model.generate_content(learn_prompt).text
            if "なし" not in new_rule:
                save_knowledge(new_rule.strip())
                st.caption(f"✨ 新しいルールを学習しました: {new_rule}")

    except Exception as e:
        st.error(f"エラー: {e}")
