import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# --- ページ設定 ---
st.set_page_config(page_title="AI配車アシスタント", layout="wide")
st.title("🚐 AI配車アシスタント")

# --- サイドバー：設定エリア ---
with st.sidebar:
    st.header("⚙️ 設定")
    # APIキー入力（Secretsに保存する前段階として）
    api_key = st.text_input("Gemini API Keyを入力してください", type="password")
    # 先ほど作成したCSVのアップロード
    uploaded_file = st.file_uploader("運転手リスト(CSV)をアップロード", type="csv")
    
    st.divider()
    st.info("""
    【10年選手の判断基準を移植済み】
    - 出庫/帰庫時間の自動予測
    - 13時間超えの2名体制アラート
    - 短時間案件の組み合わせ判定
    """)

# --- データ読み込みとAPI設定 ---
if api_key:
    genai.configure(api_key=api_key)

df_drivers = None
if uploaded_file is not None:
    # CSVの読み込み（日本語文字化け対策でencodingを指定）
    try:
        df_drivers = pd.read_csv(uploaded_file)
        st.sidebar.success("運転手リストを読み込みました")
    except Exception as e:
        st.sidebar.error(f"読み込みエラー: {e}")

# --- メイン画面 ---
if not api_key or df_drivers is None:
    st.warning("左側のサイドバーで「APIキーの入力」と「運転手リストのアップロード」を完了させてください。")
    st.stop()

st.header("1. LINE依頼文の解析と運行予測")
line_text = st.text_area("LINEの文章をここに貼り付けてください", height=200, 
                         placeholder="例：明日の石井杏奈さん案件になります。...\n3月9日（月）14:05 LDH発...")

if st.button("AI配車シミュレーション実行"):
    # --- Geminiプロンプト設定 ---
    prompt = f"""
    あなたは送迎業界で10年の経験を持つベテラン配車管理責任者です。
    以下の【LINE文】から情報を読み取り、運行スケジュールをシミュレーションし、指定のJSON形式で回答してください。

    【計算・判断ルール】
    1. 出庫予測：最初の地点の出発時間から逆算し、移動＋準備30分を考慮。
    2. 帰庫予測：最後の地点の終了予定から、自宅送迎と事務所（中目黒想定）への戻り＋清掃20分を考慮。
    3. 2名体制判定：合計拘束時間が13時間を超える場合は "Yes"、そうでなければ "No"。
    4. 組み合わせ判定：合計拘束時間が6時間以内なら "Yes"、そうでなければ "No"。
    5. 車種分類：ミニバン, BMW, Gキャビン, マイクロバス, LM の中から選択。

    【LINE文】
    {line_text}

    【回答形式(JSONのみを出力)】
    {{
        "date": "日付",
        "start_time": "出庫予想(HH:MM)",
        "end_time": "帰庫予想(HH:MM)",
        "total_duration": "合計拘束時間(x時間x分)",
        "duration_decimal": 拘束時間の数値(例: 8.5),
        "is_two_drivers_needed": "Yes/No",
        "can_combine": "Yes/No",
        "vehicle": "車種",
        "client": "担当名",
        "reasoning": "時間予測の根拠"
    }}
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with st.spinner('ベテラン配車マンが思考中...'):
        try:
            response = model.generate_content(prompt)
            # JSON部分のみを抽出（```json ... ``` を除去）
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            res = json.loads(json_str)

            # --- 結果表示（解析結果） ---
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("予想拘束時間", res['total_duration'])
                st.write(f"**出庫:** {res['start_time']} / **帰庫:** {res['end_time']}")
            with col2:
                st.metric("2名体制必要性", res['is_two_drivers_needed'])
            with col3:
                st.metric("他案件との結合", res['can_combine'])

            st.write(f"**AIの判断根拠:** {res['reasoning']}")

            # --- マッチングロジック ---
            st.divider()
            st.header("2. 候補運転手の選定")
            
            # 条件に合う運転手を抽出
            v_col = f"運転可能車種（{res['vehicle']}）"
            c_col = res['client']
            
            # 運転手リストに該当する列があるか確認してフィルタリング
            if v_col in df_drivers.columns and c_col in df_drivers.columns:
                # 「〇」または「△」の人を抽出
                match_df = df_drivers[
                    (df_drivers[v_col].isin(['〇', '△'])) & 
                    (df_drivers[c_col].isin(['〇', '△']))
                ].copy()
                
                # 優先順位（〇を優先）
                match_df['優先度'] = match_df[c_col].apply(lambda x: 1 if x == '〇' else 2)
                match_df = match_df.sort_values('優先度')

                if not match_df.empty:
                    st.success(f"以下の運転手が {res['client']} さんの {res['vehicle']} 案件に対応可能です：")
                    # 表示用に整理
                    display_cols = ["氏名", v_col, c_col, "備考"]
                    st.table(match_df[display_cols])
                else:
                    st.error("条件に完全に一致する運転手が見つかりませんでした。")
            else:
                st.warning(f"リスト内に『{res['vehicle']}』や『{res['client']}』の項目が見つかりません。手動で確認してください。")

        except Exception as e:
            st.error(f"解析エラーが発生しました。LINE文の形式やAPIキーを確認してください。: {e}")
            st.write(response.text if 'response' in locals() else "")
