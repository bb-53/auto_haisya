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

# --- 頑丈な読み込み関数 ---
def smart_read_csv(file):
    if file is None: return None
    encodings = ['utf-8-sig', 'utf-8', 'cp932']
    for enc in encodings:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=enc, errors='replace')
        except:
            continue
    return None

# --- 状態チェック用 ---
files = {"車種スキル": f_d, "担当スキル": f_s, "車両マスター": f_v, "担当マスター": f_c}
loaded_data = {}

# 個別に読み込み試行
for name, f in files.items():
    if f:
        df = smart_read_csv(f)
        if df is not None:
            loaded_data[name] = df
            st.sidebar.success(f"OK: {name}")
        else:
            st.sidebar.error(f"NG: {name} (読み込み失敗)")

# --- データ結合処理 ---
df_drivers, df_vehicles, df_clients = None, None, None

if len(loaded_data) == 4:
    try:
        d = loaded_data["車種スキル"]
        s = loaded_data["担当スキル"]
        # ここで「氏名」という列名が両方のファイルにあるかチェック
        if "氏名" in d.columns and "氏名" in s.columns:
            df_drivers = pd.merge(d, s, on="氏名", how="inner")
            df_vehicles = loaded_data["車両マスター"]
            df_clients = loaded_data["担当マスター"]
        else:
            st.error("エラー：運転手リストの2つのファイル両方に『氏名』という列名が必要です。")
            st.write("車種スキルの列名:", list(d.columns))
            st.write("担当スキルの列名:", list(s.columns))
    except Exception as e:
        st.error(f"データ結合中に予期せぬエラー: {e}")

# --- 画面表示制御 ---
if not api_key:
    st.warning("サイドバーで Gemini API Key を入力してください。")
    st.stop()

if df_drivers is None:
    st.info("4つのファイルをアップロードしてください。現在、以下のファイルを認識しています：")
    st.write(list(loaded_data.keys()))
    st.stop()

st.success("✅ 全データの連携に成功しました！解析を開始できます。")

# --- 解析セクション ---
line_text = st.text_area("LINEの依頼文を貼り付けてください", height=200)
if st.button("AI配車シミュレーション実行"):
    # ... (解析ロジック)
    st.write("解析を実行します...")
