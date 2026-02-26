import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# ==========================================
# 1. Googleスプレッドシートの連携設定
# ==========================================
try:
    # StreamlitのSecretsから認証情報を読み込む
    credentials_dict = json.loads(st.secrets["gcp_credentials"])
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く（※ファイル名が違う場合はここを変更してください）
    SPREADSHEET_NAME = "バレーボール分析データ" 
    sh = client.open(SPREADSHEET_NAME)
    
    # シートの取得
    ws_players = sh.worksheet("選手データ")
    ws_records = sh.worksheet("試合記録")
    
    # シートが完全に空の場合、1行目に自動でヘッダー（見出し）を追加する
    if not ws_players.get_all_values():
        ws_players.append_row(["チーム", "背番号", "ポジション"])
    if not ws_records.get_all_values():
        ws_records.append_row(["試合名", "チーム", "背番号", "スキル", "評価"])
        
except Exception as e:
    st.error(f"スプレッドシートの連携に失敗しました。Secretsの設定や共有設定を確認してください。エラー詳細: {e}")
    st.stop()

# ==========================================
# 2. 選手データの読み込み関数
# ==========================================
def get_player_data():
    records = ws_players.get_all_records()
    return pd.DataFrame(records)

# ==========================================
# 3. 画面レイアウトとメニュー
# ==========================================
st.sidebar.title("メニュー")
menu = st.sidebar.radio(
    "画面を選択してください",
    ["チーム・選手登録", "サーブ・レセプション・ディグ", "スパイク・ブロック", "セット"]
)

# 常に最新の選手データをスプレッドシートから取得
player_df = get_player_data()

# --- 【画面A】チーム・選手登録 ---
if menu == "チーム・選手登録":
    st.title("チーム・選手登録")
    
    with st.form(key='player_registration_form', clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            team_name = st.text_input("チーム名", placeholder="例: 広島大学")
        with col2:
            player_number = st.number_input("背番号", min_value=1, max_value=99, step=1)
        with col3:
            position = st.selectbox("ポジション", ["OH", "MB", "S", "OP", "L"])
            
        submit_button = st.form_submit_button(label='スプレッドシートに登録')
        
        if submit_button:
            if team_name:
                # スプレッドシートに1行追加
                ws_players.append_row([team_name, player_number, position])
                st.success(f"{team_name}の{player_number}番 ({position}) を登録しました！")
                st.rerun() # 画面を更新して最新のリストを表示
            else:
                st.error("チーム名を入力してください。")

    # 登録済みの選手一覧を表示
    if not player_df.empty:
        st.write("【現在の登録済み選手一覧】")
        st.dataframe(player_df)

# ==========================================
# 4. 共通の記録フォーム作成関数
# ==========================================
def create_record_form(skill_type, skills_list, eval_table_md, default_match=""):
    st.title(f"{skill_type}の記録")
    
    with st.expander("評価基準表を表示", expanded=True):
        st.markdown(eval_table_md)

    if player_df.empty:
        st.warning("先に「チーム・選手登録」から選手を登録してください。")
        return

    # 登録されているチームのリストを作成
    registered_teams = player_df["チーム"].unique().tolist()

    with st.form(key=f'record_form_{skill_type}', clear_on_submit=True):
        match_name = st.text_input("試合名", value=default_match, placeholder="例: 春季リーグ vs.　第１セット")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_team = st.selectbox("チームを選択", registered_teams)
        with col2:
            # 選択したチームに所属する選手だけを抽出して選択肢にする
            team_players = player_df[player_df["チーム"] == selected_team]["背番号"].astype(str).tolist()
            selected_number = st.selectbox("背番号を選択", team_players if team_players else ["登録なし"])

        col3, col4 = st.columns(2)
        with col3:
            if len(skills_list) == 1:
                selected_skill = st.selectbox("スキル", skills_list, disabled=True)
            else:
                selected_skill = st.radio("スキルを選択", skills_list, horizontal=True)
        with col4:
            selected_eval = st.radio("評価を選択", ["#", "+", "-", "="], horizontal=True)

        submit_record = st.form_submit_button(label='記録を保存する')

        if submit_record:
            if selected_number == "登録なし":
                st.error("選手を選択してください。")
            elif not match_name:
                st.error("試合名を入力してください。")
            else:
                # スプレッドシートの「試合記録」シートに書き込み
                ws_records.append_row([match_name, selected_team, selected_number, selected_skill, selected_eval])
                st.success(f"保存完了: {selected_team} #{selected_number} | {selected_skill} {selected_eval}")

# --- 【画面B】サーブ・レセプション・ディグ ---
if menu == "サーブ・レセプション・ディグ":
    eval_table = """
    | 記号 | 評価意味 | 内容 |
    | :--- | :--- | :--- |
    | **#** | パーフェクト | サービスエース（得点、返球なし）、完璧なレシーブ（Aパス） |
    | **+** | ポジティブ | 相手がAパスではなかった、良いディグ（Bパス） |
    | **-** | ネガティブ | レシーブが乱れて攻撃が限られる、Cパス以下 |
    | **=** | エラー | サーブミス、レセプション・ディグ失点 |
    """
    create_record_form("サーブ・レセプション・ディグ", ["S", "R", "D"], eval_table)

# --- 【画面C】スパイク・ブロック ---
if menu == "スパイク・ブロック":
    eval_table = """
    | 記号 | 評価意味 | 内容 |
    | :--- | :--- | :--- |
    | **#** | パーフェクト | 攻撃ポイント、ブロックポイント |
    | **+** | ポジティブ | 相手を崩す攻撃、スパイクでブロックアウトする、ブロックでワンタッチを取る |
    | **-** | ネガティブ | 相手レシーブがセッターに返る、ブロックアウトされる |
    | **=** | エラー | 攻撃ミス（アウト・ネット）、被ブロック、反則、失点 |
    """
    create_record_form("スパイク・ブロック", ["A", "B"], eval_table)

# --- 【画面D】セット ---
if menu == "セット":
    eval_table = """
    | 記号 | 評価意味 | 内容 |
    | :--- | :--- | :--- |
    | **#** | パーフェクト | 完璧なセット、ブロックを振る |
    | **+** | ポジティブ | スパイカーが打ちやすいセット、相手ブロックはついている |
    | **-** | ネガティブ | セットが乱れて攻撃が限られる、速攻と合わない |
    | **=** | エラー | ドリブルなどの反則、失点 |
    """
    create_record_form("セット", ["E"], eval_table)
