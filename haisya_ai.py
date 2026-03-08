import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# --- ページ設定 ---
st.set_page_config(page_title="AI配車アシスタント PRO", layout="wide")
st.title("🚐 AI配車アシスタント PRO")

# --- サイドバー：設定エリア ---
with st.sidebar:
    st.header("⚙️ マスターデータ設定")
    api_key = st.text_input("Gemini API Key", type="password")
    file_drivers = st.file_uploader("1. 運転手リスト(CSV)", type="csv")
    file_vehicles = st.file_uploader("2. 車両データ(CSV)", type="csv")
    file_clients = st.file_uploader("3. 担当データ(CSV)", type="csv")

# --- データ処理関数（エラーに強い版） ---
def load_all_data():
    if not (file_drivers and file_vehicles and file_clients):
        return None, None, None
    
    def smart_read_csv(file):
        # 1. まずは UTF-8 (絵文字対応) で試す
        try:
            # 元の場所に戻してから読み直す
            file.seek(0)
            return pd.read_csv(file, encoding="utf-8")
        except:
            # 2. 失敗したら Shift-JIS (Excel形式) で試す
            try:
                file.seek(0)
                return pd.read_csv(file, encoding="cp932")
            except Exception as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")
                return None

    try:
        # 1. 運転手リスト
        raw_drivers = smart_read_csv(file_drivers)
        if raw_drivers is None: return None, None, None
        
        # 運転手リストの加工（横並び形式対応）
        car_df = raw_drivers.iloc[:, 0:7].copy()
        car_df.columns = ["氏名", "ミニバン", "BMW", "Gキャビン", "マイクロバス", "LM", "備考"]
        client_skill_df = raw_drivers.iloc[:, 8:].copy()
        client_skill_df.columns = client_skill_df.iloc[0]
        client_skill_df = client_skill_df.drop(client_skill_df.index[0]).dropna(subset=["氏名"])
        df_drivers = pd.merge(car_df.dropna(subset=["氏名"]), client_skill_df, on="氏名", how="inner")

        # 2. 車両データ
        df_vehicles = smart_read_csv(file_vehicles)
        
        # 3. 担当データ
        df_clients = smart_read_csv(file_clients)
        
        if df_vehicles is None or df_clients is None:
            return None, None, None
            
        return df_drivers, df_vehicles, df_clients
        
    except Exception as e:
        st.error(f"データ処理中にエラーが発生しました: {e}")
        return None, None, None
        
# データの読み込み実行
df_drivers, df_vehicles, df_clients = load_all_data()

# API設定
if api_key:
    genai.configure(api_key=api_key)

# --- メイン画面のガード（ここでエラーを止める） ---
if not api_key:
    st.warning("サイドバーでGemini API Keyを入力してください。")
    st.stop()

if df_drivers is None:
    st.warning("サイドバーで3つのCSVファイルをすべてアップロードしてください。")
    st.stop()

# --- 以降、正常にデータが読み込まれた場合の処理 ---
st.header("1. LINE依頼の解析・シミュレーション")
line_text = st.text_area("LINEの文章を貼り付けてください", height=200)

if st.button("詳細シミュレーション実行"):
    # (中略：解析ロジックは前回と同じ)
    # ...
    st.write("解析を開始します...")
    # ...
