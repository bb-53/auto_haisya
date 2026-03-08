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
    file_drivers = st.file_uploader("1. 運転手リスト(CSV)", type="csv")
    file_vehicles = st.file_uploader("2. 車両データ(CSV)", type="csv")
    file_clients = st.file_uploader("3. 担当データ(CSV)", type="csv")

# --- CSV読み込み関数 ---
def smart_read_csv(file):
    if file is None: return None
    encodings = ['utf-8-sig', 'utf-8', 'cp932']
    for enc in encodings:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=enc, errors='replace', header=None) # 一旦ヘッダーなしで読み込む
        except:
            continue
    return None

# --- 運転手リスト専用の加工ロジック ---
def process_driver_list(raw_df):
    try:
        # スニペットに基づき、1行目（タイトル行）を飛ばして2行目をヘッダーにする
        # 左側の表：0-6列目
        car_df = raw_df.iloc[1:, 0:7].copy()
        car_df.columns = ["氏名", "ミニバン", "BMW", "Gキャビン", "マイクロバス", "LM", "備考"]
        car_df = car_df.dropna(subset=["氏名"]).fillna("")

        # 右側の表：8列目以降（8列目が氏名.1）
        client_skill_df = raw_df.iloc[1:, 8:].copy()
        client_header = raw_df.iloc[1, 8:].values # 2行目を項目名にする
        client_skill_df.columns = client_header
        client_skill_df = client_skill_df.drop(client_skill_df.index[0]) # 項目名行を削除
        client_skill_df = client_skill_df.dropna(subset=["氏名"]).fillna("")

        # 左右を「氏名」で結合
        df = pd.merge(car_df, client_skill_df, on="氏名", how="inner")
        # 列名から「運転可能車種（）」という文字を消してシンプルにする
        df.columns = [c.replace("運転可能車種（", "").replace("）", "") for c in df.columns]
        return df
    except Exception as e:
        st.error(f"加工エラー: {e}")
        return None

# --- データの読み込み実行 ---
df_drivers, df_vehicles, df_clients = None, None, None

if file_drivers and file_vehicles and file_clients:
    raw_drivers = smart_read_csv(file_drivers)
    if raw_drivers is not None:
        df_drivers = process_driver_list(raw_drivers)
    
    # 車両と担当は1行目がヘッダーの標準形式と想定
    df_vehicles = smart_read_csv(file_vehicles)
    if df_vehicles is not None:
        df_vehicles.columns = df_vehicles.iloc[0]
        df_vehicles = df_vehicles[1:]
        
    df_clients = smart_read_csv(file_clients)
    if df_clients is not None:
        df_clients.columns = df_clients.iloc[0]
        df_clients = df_clients[1:]

if api_key:
    genai.configure(api_key=api_key)

# --- 画面制御 ---
if not api_key:
    st.warning("APIキーを入力してください")
    st.stop()

if df_drivers is None or df_vehicles is None or df_clients is None:
    st.warning("3つのファイルをアップロードしてください。")
    st.stop()

st.success("全てのデータを読み込みました！")

# --- 解析・シミュレーション ---
line_text = st.text_area("LINEを貼り付けてください", height=200)
if st.button("実行"):
    # (解析ロジック)
    model = genai.GenerativeModel('gemini-1.5-flash')
    # 以下、前回同様のマッチング処理...
    st.write("シミュレーション結果を表示します...")
    # (省略：前回の解析コード)
