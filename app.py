import streamlit as st
import pandas as pd

# --- データの一時保存用（セッションステートの初期化） ---
if 'players' not in st.session_state:
    st.session_state['players'] = []
if 'records' not in st.session_state:
    st.session_state['records'] = []

# --- サイドバーのメニュー ---
st.sidebar.title("メニュー")
menu = st.sidebar.radio(
    "画面を選択してください",
    ["チーム・選手登録", "サーブ・レセプション・ディグ", "スパイク・ブロック", "セット"]
)

# --- 1. チーム・選手登録画面 ---
if menu == "チーム・選手登録":
    st.title("チーム・選手登録")
    
    with st.form(key='player_registration_form', clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            # 頻繁に入力しそうなチーム名を初期値として設定
            team_name = st.text_input("チーム名", placeholder="例: 広島サンダーズ")
        with col2:
            player_number = st.number_input("背番号", min_value=1, max_value=99, step=1)
        with col3:
            position = st.selectbox("ポジション", ["OH", "MB", "S", "OP", "L"])
            
        submit_button = st.form_submit_button(label='登録する')
        
        if submit_button and team_name:
            st.session_state['players'].append({
                "チーム": team_name,
                "背番号": player_number,
                "ポジション": position
            })
            st.success(f"{team_name}の{player_number}番 ({position}) を登録しました！")

    # 登録済みの選手一覧を表示
    if st.session_state['players']:
        st.write("【登録済み選手一覧】")
        st.dataframe(pd.DataFrame(st.session_state['players']))

# --- 共通の記録フォーム作成関数 ---
def create_record_form(skill_type, skills_list, eval_table_md, default_match="広島サンダーズ vs サントリーサンバーズ"):
    st.title(f"{skill_type}の記録")
    
    # 評価基準表の表示（折りたたみ式にすると画面がすっきりします）
    with st.expander("評価基準表を表示", expanded=True):
        st.markdown(eval_table_md)

    # 登録されているチームのリストを取得
    registered_teams = list(set([p["チーム"] for p in st.session_state['players']]))
    
    if not registered_teams:
        st.warning("先に「チーム・選手登録」から選手を登録してください。")
        return

    with st.form(key=f'record_form_{skill_type}', clear_on_submit=True):
        match_name = st.text_input("試合名", value=default_match)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_team = st.selectbox("チームを選択", registered_teams)
        with col2:
            # 選択したチームに所属する選手だけを抽出して選択肢にする
            team_players = [str(p["背番号"]) for p in st.session_state['players'] if p["チーム"] == selected_team]
            selected_number = st.selectbox("背番号を選択", team_players if team_players else ["登録なし"])

        col3, col4 = st.columns(2)
        with col3:
            if len(skills_list) == 1:
                selected_skill = st.selectbox("スキル", skills_list, disabled=True)
            else:
                selected_skill = st.radio("スキルを選択", skills_list, horizontal=True)
        with col4:
            selected_eval = st.radio("評価を選択", ["#", "+", "-", "="], horizontal=True)

        submit_record = st.form_submit_button(label='記録を保存')

        if submit_record:
            if selected_number == "登録なし":
                st.error("選手を選択してください。")
            else:
                record = {
                    "試合名": match_name,
                    "チーム": selected_team,
                    "背番号": selected_number,
                    "スキル": selected_skill,
                    "評価": selected_eval
                }
                st.session_state['records'].append(record)
                st.success(f"記録しました: {selected_team} #{selected_number} | {selected_skill} {selected_eval}")

    # 記録履歴の表示
    if st.session_state['records']:
        st.write("【現在の入力履歴】")
        st.dataframe(pd.DataFrame(st.session_state['records']).tail(5)) # 最新の5件を表示

# --- 2. サーブ・レセプション・ディグ画面 ---
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

# --- 3. スパイク・ブロック画面 ---
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

# --- 4. セット画面 ---
if menu == "セット":
    eval_table = """
    | 記号 | 評価意味 | 内容 |
    | :--- | :--- | :--- |
    | **#** | パーフェクト | 完璧なセット、ブロックを振る |
    | **+** | ポジティブ | スパイカーが打ちやすいセット、相手ブロックはついている |
    | **-** | ネガティブ | セットが乱れて攻撃が限られる、速攻と合わない |
    | **=** | エラー | ドリブルなどの反則、失点 |
    """
    # スキルは "E" のみ（固定）にするためリストの要素を1つにする
    create_record_form("セット", ["E"], eval_table)