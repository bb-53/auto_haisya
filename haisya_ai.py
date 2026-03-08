import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import io

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

# --- 頑丈なCSV読み込み関数（診断メッセージ付き） ---
def smart_read_csv(file):
    if file is None:
        return None
    
    encodings = ['utf-8-sig', 'utf-8', 'cp932']
    for enc in encodings:
        try:
            file.seek(0)
            # errors='replace'で絵文字等の問題を回避
            return pd.read_csv(file, encoding=enc, errors='replace')
        except Exception:
            continue
    return None

# --- データ加工関数（どこで失敗したか表示） ---
def process_driver_list(raw_df):
    try:
        # 左側の「車種スキル」表 (0-6列目)
        # 列名: 氏名, ミニバン, BMW, Gキャビン, マイクロバス, LM, 備考
        car_df = raw_df.iloc[:, 0:7].copy()
        car_df.columns = ["氏名", "ミニバン", "BMW", "Gキャビン", "マイクロバス", "LM", "備考"]
        car_df = car_df.dropna(subset=["氏名"])
        # 空白を埋める（〇や△以外を空文字に）
        car_df = car_df.fillna("")

        # 右側の「担当スキル」表 (8列目以降)
        # 1行目が担当名になっている
        client_skill_df = raw_drivers.iloc[:, 8:].copy()
        # 最初の行（氏名, 関, VERBAL...）をヘッダーにする
        new_header = client_skill_df.iloc[0]
        client_skill_df = client_skill_df[1:]
        client_skill_df.columns = new_header
        
        # 不要な「氏名」以外の空行を削除
        client_skill_df = client_skill_df.dropna(subset=["氏名"])
        client_skill_df = client_skill_df.fillna("")

        # 結合
        return pd.merge(car_df, client_skill_df, on="氏名", how="inner")
    except Exception as e:
        st.error(f"運転手リストの加工中にエラー: {e}")
        # どこで失敗したか確認用
        st.write("元データの列数:", raw_df.shape[1])
        st.write("元データの最初の5行:", raw_df.head())
        return None

# --- 実行 ---
df_drivers = None
df_vehicles = None
df_clients = None

if file_drivers and file_vehicles and file_clients:
    raw_drivers = smart_read_csv(file_drivers)
    if raw_drivers is not None:
        df_drivers = process_driver_list(raw_drivers)
    
    df_vehicles = smart_read_csv(file_vehicles)
    df_clients = smart_read_csv(file_clients)

if api_key:
    genai.configure(api_key=api_key)

# --- 画面表示制御 ---
if not api_key:
    st.warning("サイドバーでGemini API Keyを入力してください。")
    st.stop()

if df_drivers is None or df_vehicles is None or df_clients is None:
    st.warning("3つのCSVファイルをすべて正しく読み込めるまでお待ちください。")
    if file_drivers:
        st.info("運転手リストの形式をチェックしています...")
    st.stop()

# --- 解析セクション ---
st.success("全てのマスターデータを読み込みました！")
st.header("1. LINE依頼の解析・シミュレーション")
line_text = st.text_area("LINEの文章を貼り付けてください", height=200)

if st.button("詳細シミュレーション実行"):
    # (解析ロジック)
    vehicle_info = df_vehicles.to_string()
    client_info = df_clients.to_string()

    prompt = f"""
    あなたは送迎業界のベテラン配車マンです。以下のデータを参考に運行予測をしてください。
    【車両】: {vehicle_info}
    【担当・住所】: {client_info}
    【ルール】
    - 出庫：準備30分＋最初の地点への移動
    - 帰庫：終了＋住所への送り＋事務所（中目黒想定）戻り＋清掃20分
    - vehicle：ミニバン, BMW, Gキャビン, マイクロバス, LM から判定
    - client：担当カテゴリ（所属, 会長, TJBB等）を特定
    【LINE文】: {line_text}
    【出力形式(JSONのみ)】: {{...}}
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    with st.spinner('ベテラン配車マンが計算中...'):
        try:
            response = model.generate_content(prompt)
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            res = json.loads(json_str)

            c1, c2, c3 = st.columns(3)
            c1.metric("予想拘束時間", res.get('total_duration', '-'))
            c2.metric("車種判定", res.get('detected_vehicle_type', '-'))
            c3.metric("2名体制要否", res.get('is_two_drivers_needed', '-'))
            
            st.info(f"**📍 送り先:** {res.get('target_address', '-')}\n\n**📝 根拠:** {res.get('reasoning', '-')}")

            # 2. マッチング表示
            st.divider()
            st.header("2. 候補運転手の選定")
            v_type = res.get('detected_vehicle_type')
            cat = res.get('detected_category')
            
            if v_type in df_drivers.columns and cat in df_drivers.columns:
                match = df_drivers[(df_drivers[v_type].isin(['〇', '△'])) & (df_drivers[cat].isin(['〇', '△']))].copy()
                if not match.empty:
                    st.table(match[["氏名", v_type, cat, "備考"]])
                else:
                    st.error(f"「{v_type}」と「{cat}」の両方に対応できる人が見つかりません。")
            else:
                st.warning(f"リストに項目『{v_type}』または『{cat}』が見当たりません。")
        except Exception as e:
            st.error(f"解析エラー: {e}")
