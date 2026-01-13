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
                st.rerun() # 名稱變更時重新整理，以更新上方分頁標籤

        with col_input2:
            new_host = st.text_input(f"主辦單位", value=current_proj["host"], key=f"host_{pid}", placeholder="請輸入主辦單位")
            if new_host != current_proj["host"]:
                st.session_state.projects_data[pid]["host"] = new_host

        st.markdown("---")

        # 2. 施工紀錄輸入
        st.subheader("📝 新增施工紀錄")
        
        # 輸入介面
        c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.5, 1.2, 1, 1, 1.5])
        with c1:
            input_date = st.date_input("日期", key=f"d_{pid}", value=date.today())
        with c2:
            input_vendor = st.text_input("廠商名稱", key=f"v_{pid}")
        with c3:
            # 這裡的選單會讀取 st.session_state.work_types (包含側邊欄新增的)
            input_type = st.selectbox("施工工種", st.session_state.work_types, key=f"t_{pid}")
        with c4:
            input_shift = st.selectbox("班別", ["早班", "中班", "晚班"], key=f"s_{pid}")
        with c5:
            input_count = st.number_input("人數", min_value=1, value=5, step=1, key=f"c_{pid}")
        with c6:
            input_remark = st.text_input("備註", key=f"r_{pid}")
        
        if st.button("寫入紀錄", key=f"btn_{pid}"):
            if not input_vendor:
                st.error("請輸入廠商名稱")
            else:
                new_record = pd.DataFrame({
                    "日期": [pd.to_datetime(input_date)],
                    "廠商名稱": [input_vendor],
                    "施工工種": [input_type],
                    "班別": [input_shift],
                    "施工人數": [input_count],
                    "備註": [input_remark]
                })
                # 更新資料
                st.session_state.projects_data[pid]["data"] = pd.concat(
                    [st.session_state.projects_data[pid]["data"], new_record], ignore_index=True
                )
                st.success("已寫入！")
                st.rerun()

        # 3. 資料展示與圖表
        df = st.session_state.projects_data[pid]["data"]
        
        if not df.empty:
            st.markdown("---")
            
            # 顯示表格 (依照日期排序)
            df = df.sort_values(by="日期")
            df_display = df.copy()
            df_display['日期'] = df_display['日期'].dt.strftime('%Y-%m-%d') # 格式化日期顯示
            
            st.subheader(f"📋 {new_name if new_name else '此專案'} - 施工明細")
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )

            # 4. 統計折線圖
            st.subheader("📈 每日人力統計圖")
            
            # 依據「日期」加總人數 (不分廠商、工種)
            daily_stats = df.groupby("日期")["施工人數"].sum().reset_index()

            if not daily_stats.empty:
                min_date = daily_stats['日期'].min()
                max_date = daily_stats['日期'].max()
                
                fig = go.Figure()

                # 加入折線
                fig.add_trace(go.Scatter(
                    x=daily_stats['日期'], 
                    y=daily_stats['施工人數'],
                    mode='lines+markers+text',
                    text=daily_stats['施工人數'], # 在點上顯示數字
                    textposition="top center",
                    name='總人數',
                    line=dict(color='#D62728', width=3), # 紅色線條較顯眼
                    marker=dict(size=8)
                ))

                # 假日背景處理
                holidays_list = get_holiday_ranges(min_date, max_date)
                for h_date in holidays_list:
                    x0 = h_date - timedelta(hours=12)
                    x1 = h_date + timedelta(hours=12)
                    fig.add_vrect(
                        x0=x0, x1=x1,
                        fillcolor="LightSkyBlue", 
                        opacity=0.5, 
                        layer="below", 
                        line_width=0,
                    )

                fig.update_layout(
                    title=f"{new_name} - 每日出工人數趨勢",
                    xaxis_title="日期",
                    yaxis_title="人數",
                    plot_bgcolor='white',
                    xaxis=dict(showgrid=True, gridcolor='#eee', tickformat='%Y-%m-%d'),
                    yaxis=dict(showgrid=True, gridcolor='#eee'),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("目前尚無資料，請填寫上方表格以開始紀錄。")