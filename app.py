import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

# --- 設定頁面寬度與標題 ---
st.set_page_config(page_title="每日施工人數統計系統", layout="wide")

# --- 初始化 Session State ---
# 1. 初始化專案資料 (預設 3 個專案卡槽，可視需求增減)
if 'projects_data' not in st.session_state:
    st.session_state.projects_data = {}
    # 預先建立三個空白專案容器
    for i in range(1, 4):
        st.session_state.projects_data[f"proj_{i}"] = {
            "name": "",  # 預設空白
            "host": "",  # 預設空白
            "data": pd.DataFrame(columns=["日期", "廠商名稱", "施工工種", "班別", "施工人數", "備註"])
        }

# 2. 初始化工種選單 (預設一些常見的，可讓使用者自行新增)
if 'work_types' not in st.session_state:
    st.session_state.work_types = ["鋼筋", "模板", "混凝土", "水電", "泥作", "裝修"]

# --- 輔助函式：判斷是否為假日 ---
def get_holiday_ranges(start_date, end_date):
    """
    回傳一段時間內的假日清單 (包含週末與自定義國定假日)。
    """
    # 範例國定假日 (可自行擴充)
    public_holidays = [
        "2024-01-01", "2024-02-08", "2024-02-09", "2024-02-12", "2024-02-13", "2024-02-14", 
        "2024-02-28", "2024-04-04", "2024-04-05", "2024-05-01", "2024-06-10", "2024-09-17", "2024-10-10",
        "2025-01-01", "2025-01-25", "2025-01-26", "2025-01-27", "2025-01-28", "2025-01-29",
    ]
    
    holidays = []
    current = start_date
    while current <= end_date:
        if current.weekday() >= 5 or current.strftime("%Y-%m-%d") in public_holidays:
            holidays.append(current)
        current += timedelta(days=1)
    return holidays

# --- 側邊欄：管理工種 ---
with st.sidebar:
    st.header("⚙️ 設定")
    st.write("目前可選工種：")
    st.code(", ".join(st.session_state.work_types))
    
    # 新增工種功能
    new_type = st.text_input("➕ 新增工種 (輸入後按 Enter)", placeholder="例如：油漆")
    if new_type:
        if new_type not in st.session_state.work_types:
            st.session_state.work_types.append(new_type)
            st.success(f"已新增：{new_type}")
            st.rerun() # 重新整理以更新選單
        else:
            st.warning("該工種已存在")

# --- 主程式 ---
st.title("🏗️ 每日施工人數紀錄與統計 APP")

# 動態產生分頁標題
# 如果使用者還沒輸入專案名稱，就顯示 "專案 1", "專案 2"...
tab_labels = []
project_ids = list(st.session_state.projects_data.keys())

for pid in project_ids:
    p_name = st.session_state.projects_data[pid]["name"]
    p_host = st.session_state.projects_data[pid]["host"]
    # 標題顯示邏輯：如果有輸入名稱就顯示名稱，否則顯示預設 ID
    label = p_name if p_name else f"新專案 ({pid})"
    tab_labels.append(label)

tabs = st.tabs(tab_labels)

for i, pid in enumerate(project_ids):
    with tabs[i]:
        # 取得該專案目前的資料
        current_proj = st.session_state.projects_data[pid]

        # 1. 專案基本資料輸入區 (標題與主辦單位)
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            # 使用 on_change 或直接讀取值來更新
            new_name = st.text_input(f"工程名稱", value=current_proj["name"], key=f"name_{pid}", placeholder="請輸入工程名稱")
            # 更新 Session State 中的名稱
            if new_name != current_proj["name"]:
                st.session_state.projects_data[pid]["name"] = new_name
                st.rerun() # 名稱變更