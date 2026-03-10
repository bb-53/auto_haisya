import streamlit as st
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="プロ配車デスクAI", layout="wide")
st.title("🚐 自動配車・担当割り振りAI")

# サイドバーで3つのデータを読み込み
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    st.write("### 1. マスターデータの準備")
    up_drivers = st.file_uploader("運転手リスト(CSV)", type="csv")
    up_mapping = st.file_uploader("担当可能リスト(CSV)", type="csv")
    up_vehicles = st.file_uploader("車両リスト(CSV)", type="csv")

if not api_key:
    st.warning("APIキーを入力してください")
    st.stop()

# 依頼文の入力
st.write("### 2. 本日の稼働依頼を貼り付け")
line_text = st.text_area("依頼内容（ランペ 1980...など）", height=200)

if st.button("担当を割り振り、配車案を作る"):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # 各データをテキスト化してAIに読み込ませる準備
        def get_csv_text(up_file, label):
            if up_file:
                df = pd.read_csv(up_file)
                return f"【{label}】\n{df.to_string(index=False)}\n"
            return ""

        context = ""
        context += get_csv_text(up_drivers, "運転手リスト")
        context += get_csv_text(up_mapping, "担当可能リスト（現場と運転手の相性）")
        context += get_csv_text(up_vehicles, "車両リスト")

        # AIへの指示（プロンプト）
        prompt = f"""
        あなたは送迎会社の経験豊富な配車デスクです。
        以下の「マスターデータ」に基づき、本日の「依頼内容」に対して最適な運転手と車両を割り当ててください。

        {context}

        【依頼内容】
        {line_text}

        【割り振りのルール】
        1. 「担当可能リスト」を最優先してください。特定の現場に指定の運転手がいれば、その人を優先して割り当てます。
        2. 「車両リスト」を参照し、ナンバーから正確な車種を特定してください。
        3. 同じ運転手・車両で1日複数回の稼働（中抜き）がある場合、無理のないスケジュールか確認してください。
        4. もし「担当できる人がいない」または「車両が足りない」場合は、警告を出してください。
        """
        
        with st.spinner('最適な組み合わせを計算中...'):
            response = model.generate_content(prompt)
            st.success("配車・担当割り振りが完了しました！")
            st.markdown(response.text)
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
