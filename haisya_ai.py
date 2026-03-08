import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# --- ページ設定 ---
st.set_page_config(page_title="AI配車アシスタント PRO", layout="wide")
st.title("🚐 AI配車アシスタント PRO")

# --- サイドバー ---
with st.sidebar:
    st.header("⚙️ マスターデータ設定")
    api_key = st.text_input("Gemini API Key", type="password")
    f_d = st.file_uploader("1. 運転手スキル(車種)", type="csv")
    f_s = st.file_uploader("2. 運転手スキル(担当)", type="csv")
    f_v = st.file_uploader("3. 車両マスター", type="csv")
    f_c = st.file_uploader("4. 担当・住所マスター", type="csv")

def smart_read_csv(file):
    if file is None: return None
    for enc in ['utf-8-sig', 'utf-8', 'cp932']:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=enc, errors='replace')
            # 列名の前後の空白を削除しておく
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except:
            continue
    return None

# --- データの読み込みと自動補正 ---
df_drivers, df_vehicles, df_clients = None, None, None

if f_d and f_s and f_v and f_c:
    d = smart_read_csv(f_d)
    s = smart_read_csv(f_s)
    v = smart_read_csv(f_v)
    c = smart_read_csv(f_c)

    try:
        # 1. 担当データの項目名を補正（「所属」という列名を「名前」として扱う）
        if c is not None and "所属" in c.columns and "住所" in c.columns:
            c = c.rename(columns={"所属": "名前"})
        
        # 2. 運転手データの結合（「氏名」でくっつける）
        if d is not None and s is not None and "氏名" in d.columns and "氏名" in s.columns:
            df_drivers = pd.merge(d, s, on="氏名", how="inner")
            # 「運転可能車種（ミニバン）」を「ミニバン」に短縮
            df_drivers.columns = [c.replace("運転可能車種（", "").replace("）", "") for c in df_drivers.columns]
            
            df_vehicles = v
            df_clients = c
        else:
            if d is not None and "氏名" not in d.columns:
                st.sidebar.error("1のファイルに『氏名』列がありません")
            if s is not None and "氏名" not in s.columns:
                st.sidebar.error("2のファイルに『氏名』列がありません")
    except Exception as e:
        st.error(f"データ処理エラー: {e}")

# --- 画面表示 ---
if not api_key:
    st.warning("サイドバーで API Key を入力してください")
    st.stop()

if df_drivers is None:
    st.info("4つのファイルをアップロードしてください。現在ファイルを読み込み中です。")
    st.stop()

st.success("✅ 全データ連携成功！")

# --- 解析セクション ---
line_text = st.text_area("LINEの依頼文を貼り付けてください", height=200)
if st.button("AI配車シミュレーション実行") and line_text:
    v_info = df_vehicles.to_string(index=False)
    c_info = df_clients.to_string(index=False)
    
    # AIへの指示（プロンプト）
    prompt = f"""
    送迎の配車マンとして、以下のデータを参照しLINE文を解析してください。
    【車両リスト(車番と車種)】:\n{v_info}
    【担当・住所リスト(名前と住所)】:\n{c_info}
    【ルール】:
    1. 車番から車種を特定
    2. 名前から住所を特定
    3. 中目黒拠点の移動時間を考慮して拘束時間を算出
    【LINE文】:\n{line_text}
    """
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.spinner('ベテラン配車マンが計算中...'):
        response = model.generate_content(prompt)
        st.write(response.text)
