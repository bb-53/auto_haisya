import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# --- ページ設定 ---
st.set_page_config(page_title="AI配車アシスタント PRO", layout="wide")
st.title("🚐 AI配車アシスタント PRO")

# --- サイドバー：複数ファイル読み込み ---
with st.sidebar:
    st.header("⚙️ マスターデータ設定")
    api_key = st.text_input("Gemini API Key", type="password")
    
    # 3つのファイルをアップロード
    file_drivers = st.file_uploader("1. 運転手リスト(CSV)", type="csv")
    file_vehicles = st.file_uploader("2. 車両データ(CSV)", type="csv")
    file_clients = st.file_uploader("3. 担当データ(CSV)", type="csv")
    
    st.divider()
    st.info("車番・タレント名・住所を紐付けて解析します")

# --- データ処理関数の修正版 ---
def load_data():
    if not (file_drivers and file_vehicles and file_clients):
        return None, None, None
    
    try:
        # encoding="cp932" を追加することで日本語エラーを回避します
        # 1. 運転手リスト
        raw_drivers = pd.read_csv(file_drivers, encoding="cp932")
        
        # ... (中略) ...

        # 2. 車両データ
        df_vehicles = pd.read_csv(file_vehicles, encoding="cp932")
        
        # 3. 担当データ
        df_clients = pd.read_csv(file_clients, encoding="cp932")
        
        return df_drivers, df_vehicles, df_clients
    except Exception as e:
        # もし cp932 でもダメな場合は utf-8 も試すようにするとより安全です
        try:
            raw_drivers = pd.read_csv(file_drivers, encoding="utf-8")
            df_vehicles = pd.read_csv(file_vehicles, encoding="utf-8")
            df_clients = pd.read_csv(file_clients, encoding="utf-8")
            return load_data_processing(raw_drivers, df_vehicles, df_clients) # 処理部分は共通化
        except:
            st.error(f"データ読み込みエラー: {e}")
            return None, None, None

# --- メイン画面 ---
if not api_key or df_drivers is None:
    st.warning("サイドバーでAPIキーと3つのCSVファイルをすべて設定してください。")
    st.stop()

st.header("1. LINE依頼の解析・シミュレーション")
line_text = st.text_area("LINEの文章を貼り付けてください", height=200)

if st.button("詳細シミュレーション実行"):
    # 参照用データをテキスト化してプロンプトに組み込む
    vehicle_info = df_vehicles.to_string()
    client_info = df_clients.to_string()

    prompt = f"""
    あなたは送迎業界のベテラン配車管理職です。以下の【マスターデータ】を参考に【LINE文】を解析してください。

    【マスターデータ】
    ■車両リスト(車番と車種の対応):
    {vehicle_info}
    ■担当・住所リスト(タレント名、カテゴリ、自宅住所):
    {client_info}

    【解析・判断ルール】
    1. 車番特定：LINEにある車番から「ミニバン/BMW/Gキャビン/マイクロバス/LM」を特定。
    2. 担当特定：乗車名から「所属/会長/TJBB/RAMPAGE」等のカテゴリを特定。
    3. 住所参照：タレントの自宅住所を確認し、現場終了後の移動時間を推測（中目黒拠点）。
    4. 時間予測：準備30分、帰庫後の清掃20分を含めた「拘束時間」を算出。
    5. 労務判定：13時間超は2名体制(Yes)、6時間以内は組み合わせ可能(Yes)。

    【LINE文】
    {line_text}

    【出力形式(JSONのみ)】
    {{
        "date": "日付",
        "start_time": "出庫(HH:MM)",
        "end_time": "帰庫(HH:MM)",
        "total_duration": "x時間x分",
        "is_two_drivers_needed": "Yes/No",
        "can_combine": "Yes/No",
        "detected_vehicle_type": "特定された車種",
        "detected_category": "特定された担当カテゴリ",
        "target_address": "送り先の住所",
        "reasoning": "シミュレーションの根拠"
    }}
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.spinner('各マスターデータと照合して計算中...'):
        try:
            response = model.generate_content(prompt)
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            res = json.loads(json_str)

            # 結果表示
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("予想拘束時間", res['total_duration'])
                st.caption(f"出庫 {res['start_time']} / 帰庫 {res['end_time']}")
            with c2:
                st.metric("車種判定", res['detected_vehicle_type'])
                st.caption(f"カテゴリ: {res['detected_category']}")
            with c3:
                st.metric("2名体制要否", res['is_two_drivers_needed'])
            
            st.info(f"**📍 送り先住所:** {res['target_address']}\n\n**📝 根拠:** {res['reasoning']}")

            # マッチング
            st.divider()
            st.header("2. 最適な運転手の選定")
            
            v_type = res['detected_vehicle_type']
            cat = res['detected_category']
            
            if v_type in df_drivers.columns and cat in df_drivers.columns:
                match = df_drivers[
                    (df_drivers[v_type].isin(['〇', '△'])) & 
                    (df_drivers[cat].isin(['〇', '△']))
                ].copy()
                
                match['優先度'] = match[cat].apply(lambda x: 1 if x == '〇' else 2)
                match = match.sort_values('優先度')

                if not match.empty:
                    st.success(f"以下の運転手が {cat} さんの {v_type} 案件に適任です。")
                    st.table(match[["氏名", v_type, cat, "備考"]])
                else:
                    st.error("条件に合う運転手が見つかりません。")
            else:
                st.warning(f"リスト内に車種『{v_type}』またはカテゴリ『{cat}』が見当たりません。")

        except Exception as e:
            st.error(f"シミュレーションエラー: {e}")
