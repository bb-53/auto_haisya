import streamlit as st
import pandas as pd
import google.generativeai as genai

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

# 頑丈な読み込み関数
def smart_read(file):
    if file is None: return None
    for enc in ['utf-8-sig', 'utf-8', 'cp932']:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=enc)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except:
            continue
    return None

# --- データ処理 ---
df_drivers, df_vehicles, df_clients = None, None, None

if f_d and f_s and f_v and f_c:
    d = smart_read(f_d)
    s = smart_read(f_s)
    v = smart_read(f_v)
    c = smart_read(f_c)

    try:
        # 1. 担当データの1列目（担当名/名前/所属など）を「名前」に統一
        if c is not None:
            c = c.rename(columns={c.columns[0]: "名前"})
        
        # 2. 運転手データの合体 (dとsを「氏名」で結合)
        if d is not None and s is not None:
            if "氏名" in d.columns and "氏名" in s.columns:
                df_drivers = pd.merge(d, s, on="氏名", how="inner")
                df_vehicles = v
                df_clients = c
            else:
                st.sidebar.error("運転手リストに『氏名』列が必要です")
    except Exception as e:
        st.error(f"データ加工エラー: {e}")

# --- 表示制御 ---
if not api_key:
    st.warning("サイドバーにAPI Keyを入力してください")
    st.stop()

if df_drivers is None:
    st.info("4つのファイルをアップロードしてください。")
    # 診断表示
    status = {"1.車種": f_d, "2.担当スキル": f_s, "3.車両": f_v, "4.住所": f_c}
    cols = st.columns(4)
    for i, (name, f) in enumerate(status.items()):
        cols[i].write(f"{name}: {'✅' if f else '❌'}")
    st.stop()

st.success("✅ 全データ連携成功！")

# --- 解析実行セクション ---
line_text = st.text_area("LINEの依頼文を貼り付けてください（例：1980で石井杏奈さん迎え...）", height=200)

if st.button("AI配車シミュレーション実行") and line_text:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # データをテキスト化してAIに渡す
    v_info = df_vehicles.to_string(index=False)
    c_info = df_clients.to_string(index=False)
    
    prompt = f"""
    あなたは送迎業界のベテラン配車マンです。
    以下の【車両リスト】と【担当住所リスト】をマスターデータとして使い、
    入力された【LINE文】から配車計画を作成してください。
    
    【ルール】
    - 車番から車種を特定してください。
    - 名前から、送るべき「住所」を特定してください。
    - 拠点は「中目黒」として、移動時間を含めた拘束時間を予測してください。
    
    【車両リスト】
    {v_info}
    
    【担当住所リスト】
    {c_info}
    
    【LINE文】
    {line_text}
    """
    
    with st.spinner('ベテラン配車マンが計算中...'):
        response = model.generate_content(prompt)
        st.markdown(response.text)
