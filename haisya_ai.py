import streamlit as st
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="プロ配車デスクAI", layout="wide")
st.title("🚐 プロ配車デスクAI（車両データ連携版）")

# サイドバー設定
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    st.write("### 1. マスターデータの読み込み")
    # 以前作成したCSVファイルを読み込む想定
    uploaded_vehicles = st.file_uploader("車両マスター(CSV)をアップロード", type="csv")
    uploaded_clients = st.file_uploader("住所録(CSV)をアップロード", type="csv")

if not api_key:
    st.warning("APIキーを入力してください")
    st.stop()

# LINE文（依頼一覧）の入力
st.write("### 2. 稼働依頼の入力")
line_text = st.text_area("依頼一覧を貼り付けてください", height=250, placeholder="ランペ 1980 / ドーベル 624 12:00〜14:00 ...")

if st.button("配車案を生成する") and line_text:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # CSVデータのテキスト化（AIに読ませるため）
        v_info = ""
        if uploaded_vehicles:
            df_v = pd.read_csv(uploaded_vehicles)
            v_info = "【車両マスターデータ】\n" + df_v.to_string(index=False)
        
        c_info = ""
        if uploaded_clients:
            df_c = pd.read_csv(uploaded_clients)
            c_info = "【現場・住所データ】\n" + df_c.to_string(index=False)
        
        # AIへの指示（プロンプト）
        prompt = f"""
        あなたは10年の経験を持つベテラン配車管理担当です。
        提供された「車両データ」と「現場データ」を参考に、最適な「配車素案」を作成してください。

        {v_info}
        {c_info}

        【今回の依頼内容】
        {line_text}

        【出力の指示】
        1. 車両ナンバーごとにスケジュールを整理してください。
        2. ナンバーから「車種（アルファード、プリウス等）」を特定し、記載してください。
        3. 同じ車両で複数案件（中抜き）がある場合は、移動時間や休憩が適切か判断してください。
        4. 現場の住所データがある場合は、移動の注意点も添えてください。
        5. 車両の重複や時間が被っている等の「配車ミス」があれば、最優先で警告してください。
        """
        
        with st.spinner('最適な配車ルートを計算中...'):
            response = model.generate_content(prompt)
            st.success("配車素案が完成しました！")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"エラー: {e}")
