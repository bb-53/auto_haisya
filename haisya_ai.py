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

# --- 頑丈なCSV読み込み関数 ---
def smart_read_csv(file):
    if file is None:
        return None
    
    # 試行するエンコーディングのリスト（優先順位順）
    encodings = ['utf-8-sig', 'utf-8', 'cp932']
    
    for enc in encodings:
        try:
            file.seek(0)
            # 【重要】errors='replace' を指定することで、
            # 読み取れない絵文字などを「？」に置き換えて、エラーを出さずに読み込みます。
            return pd.read_csv(file, encoding=enc, errors='replace')
        except Exception:
            continue
            
    # 全ての形式で失敗した場合のみエラーを表示
    st.error(f"{file.name} の読み込みに失敗しました。ファイルが壊れているか、CSV以外の可能性があります。")
    return None

# --- データの読み込みと加工 ---
def load_all_data():
    if not (file_drivers and file_vehicles and file_clients):
        return None, None, None

    # 1. 運転手リスト（特殊な横並び形式）の処理
    raw_drivers = smart_read_csv(file_drivers)
    if raw_drivers is None: return None, None, None
    
    try:
        # 左側の「車種スキル」表を抽出
        car_df = raw_drivers.iloc[:, 0:7].copy()
        car_df.columns = ["氏名", "ミニバン", "BMW", "Gキャビン", "マイクロバス", "LM", "備考"]
        car_df = car_df.dropna(subset=["氏名"])

        # 右側の「担当スキル」表を抽出
        # 「氏名.1」がある列（通常は8列目）を探して、そこから右を抽出
        client_start_idx = 8
        client_skill_df = raw_drivers.iloc[:, client_start_idx:].copy()
        
        # 1行目（実際の担当名）をヘッダーに設定
        client_skill_df.columns = client_skill_df.iloc[0]
        client_skill_df = client_skill_df.drop(client_skill_df.index[0]).dropna(subset=["氏名"])
        
        # 左右を「氏名」で結合
        df_drivers = pd.merge(car_df, client_skill_df, on="氏名", how="inner")
        
        # 2. 車両データ
        df_vehicles = smart_read_csv(file_vehicles)
        
        # 3. 担当データ
        df_clients = smart_read_csv(file_clients)
        
        return df_drivers, df_vehicles, df_clients
    except Exception as e:
        st.error(f"データ加工中にエラーが発生しました: {e}")
        return None, None, None

# 実行
df_drivers, df_vehicles, df_clients = load_all_data()

if api_key:
    genai.configure(api_key=api_key)

# --- メイン画面ガード ---
if not api_key:
    st.warning("サイドバーでGemini API Keyを入力してください。")
    st.stop()

if df_drivers is None:
    st.warning("サイドバーで3つのCSVファイルをアップロードしてください。")
    st.stop()

# --- 解析セクション ---
st.header("1. LINE依頼の解析・シミュレーション")
line_text = st.text_area("LINEの文章を貼り付けてください", height=200)

if st.button("詳細シミュレーション実行"):
    # (解析ロジック開始)
    vehicle_info = df_vehicles.to_string()
    client_info = df_clients.to_string()

    prompt = f"""
    あなたは送迎業界のベテラン配車マンです。以下のマスターデータを踏まえ、LINE文から運行を予測してください。
    【車両リスト】: {vehicle_info}
    【担当・住所リスト】: {client_info}
    【ルール】
    - 出庫：準備30分＋移動
    - 帰庫：終了＋住所への送り＋事務所（中目黒）戻り＋清掃20分
    - vehicle：ミニバン/BMW/Gキャビン/マイクロバス/LM から選択
    - client：担当カテゴリ（所属/会長/TJBB等）を特定
    【LINE文】: {line_text}
    【回答形式(JSON)】: 以前の形式通り
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    with st.spinner('シミュレーション中...'):
        try:
            response = model.generate_content(prompt)
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            res = json.loads(json_str)

            # 結果表示
            c1, c2, c3 = st.columns(3)
            c1.metric("予想拘束時間", res['total_duration'])
            c2.metric("車種判定", res['detected_vehicle_type'])
            c3.metric("2名体制要否", res['is_two_drivers_needed'])
            st.info(f"**📍 送り先:** {res['target_address']}\n\n**📝 根拠:** {res['reasoning']}")

            # マッチング
            st.divider()
            st.header("2. 最適な運転手の選定")
            v_type = res['detected_vehicle_type']
            cat = res['detected_category']
            
            if v_type in df_drivers.columns and cat in df_drivers.columns:
                match = df_drivers[(df_drivers[v_type].isin(['〇', '△'])) & (df_drivers[cat].isin(['〇', '△']))].copy()
                if not match.empty:
                    st.table(match[["氏名", v_type, cat, "備考"]])
                else:
                    st.error("適任者が見つかりませんでした。")
        except Exception as e:
            st.error(f"解析エラー: {e}")
