import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# --- 設定と記憶の準備 ---
KNOWLEDGE_FILE = "haisya_rules.txt"

def load_rules():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "まだ学習した特別なルールはありません。"

def save_rule(new_rule):
    with open(KNOWLEDGE_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n- {new_rule}")

st.set_page_config(page_title="育成型・配車デスクAI", layout="wide")
st.title("🚐 育成型：自動配車・担当割り振りAI")

# --- サイドバー：データと記憶の確認 ---
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    st.write("### 1. マスターデータの準備")
    up_drivers = st.file_uploader("運転手リスト(CSV)", type="csv")
    up_mapping = st.file_uploader("担当可能リスト(CSV)", type="csv")
    up_vehicles = st.file_uploader("車両リスト(CSV)", type="csv")
    st.divider()
    st.write("### 📚 学習済みのあなたのこだわり")
    rules = load_rules()
    st.info(rules)
    if st.button("学習したルールをリセット"):
        if os.path.exists(KNOWLEDGE_FILE):
            os.remove(KNOWLEDGE_FILE)
            st.rerun()
    # ★★★ ここから下を新しく追加してください ★★★
    st.divider()
    st.write("### 💾 学習内容のバックアップ")
    rules = load_rules() # 現在保存されているルールを読み込む
    
    # メモ帳に保存するための表示
    st.text_area("以下の内容をコピーしてメモ帳等に保存しておけば、消えてもすぐ復元できます", rules, height=150)
    
    # 消えてしまった時に、手動で一気に書き込むための入力欄
    manual_restore = st.text_area("復元したいルールをここに貼り付けてください")
    if st.button("ルールを復元・追加する"):
        if manual_restore:
            save_rule(manual_restore)
            st.success("ルールを復元しました！")
            st.rerun()

if not api_key:
    st.warning("APIキーを入力してください")
    st.stop()

# --- メイン画面：チャット形式への変更 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 過去の会話を表示
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# あなたの入力（依頼内容 または 修正指示）
if user_input := st.chat_input("依頼内容を貼り付けるか、AIの案に修正を指示してください"):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # 各種CSVの読み込み
        def get_csv_text(up_file, label):
            if up_file:
                df = pd.read_csv(up_file)
                return f"【{label}】\n{df.to_string(index=False)}\n"
            return ""

        context_data = get_csv_text(up_drivers, "運転手リスト") + \
                       get_csv_text(up_mapping, "担当可能リスト") + \
                       get_csv_text(up_vehicles, "車両リスト")

        # AIへの指示（これまでのルール＋CSV＋今の入力）
        system_prompt = f"""
        あなたはユーザー（配車責任者）の好みを学習し、分身となって配車を組むAIです。
        
        【これまでの学習内容（優先）】
        {rules}
        
        【基本データ】
        {context_data}
        
        【あなたの任務】
        1. ユーザーからの入力が依頼であれば、上記データと学習内容に基づき配車を組んでください。
        2. ユーザーからの入力が「修正指示」であれば、素直に従い、謝罪して案を出し直してください。
        3. 常に「車種」や「ドライバーの相性」を考慮してください。
        """
        
        with st.chat_message("assistant"):
            # 会話履歴を含めて応答を生成
            response = model.generate_content(system_prompt + "\n\n会話履歴:\n" + str(st.session_state.chat_history))
            st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            
            # --- 学習プロセス：今回の会話から「将来のルール」を抽出して保存 ---
            learn_prompt = f"以下の会話から、ユーザーが今後も守ってほしいと思っている『配車ルール』だけを1つ、簡潔な箇条書きで抽出してください。新しいルールがなければ『なし』とだけ答えてください。会話：{user_input} -> {response.text}"
            learning_response = model.generate_content(learn_prompt)
            if "なし" not in learning_response.text:
                save_rule(learning_response.text.strip())
                st.toast("新しいルールを学習しました！サイドバーを確認してください。")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
